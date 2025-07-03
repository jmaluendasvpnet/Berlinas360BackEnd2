# views_whatsapp.py

from .flows import RegistrarSiniestroFlowComponent, ConsultarPolizaFlowComponent
from .models import Siniestro, SiniestroMedia, SiniestroLog, ConversationSession
from django.views.decorators.http import require_http_methods
from twilio.twiml.messaging_response import MessagingResponse
from django.core.files.storage import default_storage
from twilio.twiml.voice_response import VoiceResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta

from .utils import (
    store_message,
    get_or_create_session,
    attach_incoming_media_and_maybe_transcribe,
    create_tts_audio
)

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        data = request.POST.dict()
        print(data)
        from_number = data.get("From", "").replace("whatsapp:", "")
        latitude = data.get("Latitude")
        longitude = data.get("Longitude")
        if from_number == '+14155238886':
            return

    session = get_or_create_session(from_number)

    if latitude and longitude:
        session.metadata["Latitude"] = latitude
        session.metadata["Longitude"] = longitude

    body = data.get("Body", "").strip()
    transcribed_audio_text = attach_incoming_media_and_maybe_transcribe(session, data)

    if int(data.get("NumMedia", "0")) > 0 and not body.strip() and not transcribed_audio_text:
        if session.current_flow == "registrar_siniestro" and session.current_step != "DONE":
            msg = RegistrarSiniestroFlowComponent(session).handle("")
        else:
            msg = "Media recibida y registrada."
        resp = MessagingResponse()
        reply = resp.message()
        reply.body(msg)
        store_message(session, text=msg, is_user=False)
        return HttpResponse(str(resp), content_type="text/xml")

    if not body and "Latitude" in session.metadata and "Longitude" in session.metadata:
        body = f"{session.metadata['Latitude']},{session.metadata['Longitude']}"

    if transcribed_audio_text:
        body = f"{body} {transcribed_audio_text}".strip()

    if session.current_step == "START":
        intent = "registrar_siniestro"
    else:
        intent = "registrar_siniestro"

    store_message(session, text=body, is_user=True, intent=intent)

    resp = MessagingResponse()
    reply = resp.message()

    user_sent_audio = any(
        "audio" in data.get(f"MediaContentType{i}", "")
        for i in range(int(data.get("NumMedia", "0")))
    )

    if session.current_flow == "" and session.current_step == "START":
        if intent == "registrar_siniestro":
            session.current_flow = "registrar_siniestro"
            session.save()
            msg = RegistrarSiniestroFlowComponent(session).handle(body)
        elif intent == "consultar_poliza":
            session.current_flow = "consultar_poliza"
            session.current_step = "DONE"
            if session.closed_at is None:
                session.closed_at = timezone.now()
            session.save()
            msg = ConsultarPolizaFlowComponent(session).handle(body)
        else:
            session.current_flow = "general"
            session.current_step = "DONE"
            if session.closed_at is None:
                session.closed_at = timezone.now()
            session.save()
            msg = "Hola, soy tu asistente. Manejo registro de siniestros y consulta de pólizas."
    elif session.current_flow == "registrar_siniestro":
        msg = RegistrarSiniestroFlowComponent(session).handle(body)
    elif session.current_flow == "consultar_poliza":
        msg = ConsultarPolizaFlowComponent(session).handle(body)
    else:
        msg = "¿En qué más puedo ayudarte? (Manejo siniestros y consulta de pólizas)."

    if user_sent_audio:
        audio_url = create_tts_audio(msg, request)
        reply.media(audio_url)
    else:
        reply.body(msg)

    store_message(session, text=msg, is_user=False)
    return HttpResponse(str(resp), content_type="text/xml")


@csrf_exempt
@require_http_methods(["POST"])
def upload_media(request):
    siniestro_id = request.POST.get('siniestro_id')
    files = request.FILES.getlist('file')
    if not siniestro_id or not files:
        return JsonResponse({'error': 'Siniestro ID y archivos son requeridos'}, status=400)

    try:
        siniestro = Siniestro.objects.get(id=siniestro_id)
    except Siniestro.DoesNotExist:
        return JsonResponse({'error': 'Siniestro no encontrado'}, status=404)

    session = ConversationSession.objects.filter(
        metadata__siniestro_id=siniestro_id
    ).order_by('-id').first()

    if not session:
        return JsonResponse({'error': 'No existe una sesión asociada a este siniestro.'}, status=400)

    if session.closed_at:
        if (timezone.now() - session.closed_at) > timedelta(hours=1):
            return JsonResponse({'error': 'Ha excedido la 1 hora para subir evidencia después de finalizar el registro.'}, status=400)

    file_urls = []
    for file in files:
        filename = default_storage.save(f'siniestros_media/{file.name}', file)
        file_url = default_storage.url(filename)
        file_type = file.content_type

        media = SiniestroMedia.objects.create(
            siniestro=siniestro,
            file_url=file_url,
            tipo=file_type
        )

        SiniestroLog.objects.create(
            siniestro=siniestro,
            user=siniestro.colaborador,
            action=f'Medio subido: {file.name}',
            media=media
        )

        file_urls.append(file_url)
    return JsonResponse({'urls': file_urls})

# @csrf_exempt
# def voice_webhook(request):
#     if request.method == "POST":
#         from_number = request.POST.get("From", "")
#         user_speech = "Necesito registrar un siniestro ABC123 documento 1234234"

#         intent = infer_intent(user_speech)
#         session = get_or_create_session(from_number, has_media=False )
#         store_message(session, text=user_speech, is_user=True, intent=intent)

#         resp = VoiceResponse()
#         if intent == "registrar_siniestro":
#             from .utils import parse_user_data
#             parsed = parse_user_data(user_speech)
#             if parsed["placa"] and parsed["documento"]:
#                 session.current_flow = "registrar_siniestro"
#                 session.current_step = "CONFIRMAR_DATOS"
#                 session.metadata["placa"] = parsed["placa"]
#                 session.metadata["documento"] = parsed["documento"]
#                 session.save()
#                 msg = (
#                     f"Detectamos que tu placa es {parsed['placa']} y tu documento {parsed['documento']}. "
#                     "Recibirás un mensaje de WhatsApp para finalizar el registro. Gracias."
#                 )
#             else:
#                 session.current_flow = "registrar_siniestro"
#                 session.current_step = "ASK_PLACA"
#                 session.save()
#                 msg = (
#                     "Iniciaremos el registro de siniestro. "
#                     "Te enviaremos un mensaje de WhatsApp para continuar con los datos. Gracias."
#                 )
#             resp.say(msg, voice="alice", language="es-ES")
#             store_message(session, text=msg, is_user=False)

#         elif intent == "consultar_poliza":
#             component = ConsultarPolizaFlowComponent(session)
#             msg = component.handle(user_speech)
#             resp.say(msg, voice="alice", language="es-ES")
#             store_message(session, text=msg, is_user=False)
#             session.current_flow = "consultar_poliza"
#             session.current_step = "DONE"
#             if session.closed_at is None:
#                 session.closed_at = timezone.now()
#             session.save()
#         else:
#             msg = (
#                 "Hola, soy tu asistente. Manejo registro de siniestros y consulta de pólizas. "
#                 "Envía un mensaje de WhatsApp si necesitas más información."
#             )
#             resp.say(msg, voice="alice", language="es-ES")
#             store_message(session, text=msg, is_user=False)
#             session.current_flow = "general"
#             session.current_step = "DONE"
#             if session.closed_at is None:
#                 session.closed_at = timezone.now()
#             session.save()

#         return HttpResponse(str(resp), content_type="text/xml")

#     return HttpResponse("Only POST allowed", status=405)