# views_whatsapp.py

from .models import Siniestro, SiniestroMedia, SiniestroLog, ConversationSession, ConversationMessage
from .utils import store_message, get_or_create_session, attach_incoming_media_and_maybe_transcribe
from .flows import RegistrarSiniestroFlowComponent, ConsultarPolizaFlowComponent
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.conf import settings
from twilio.rest import Client
from datetime import timedelta
import mimetypes
import requests
import json
import re

TWILIO_ACCOUNT_SID = settings.TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_manychat_message(subscriber_id, message_data, channel="whatsapp"):
    send_url = f"https://api.manychat.com/fb/sending/sendContent"

    token = settings.MANYCHAT_API_TOKEN_FB if channel == "facebook" else settings.MANYCHAT_API_TOKEN_WT
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    if channel == "whatsapp":
        buttons = []
        if "buttons" in message_data:
            for btn_caption in message_data["buttons"][:1]:
                buttons.append({
                    "type": "flow",
                    "caption": btn_caption,
                    "target": "wa_default"
                })
        payload = {
            "subscriber_id": subscriber_id,
            "data": {
                "version": "v2",
                "channel": "whatsapp",
                "content": {
                    "type": "whatsapp",
                    "messages": [{
                        "type": "text",
                        "text": message_data["text"],
                        "buttons": buttons
                    }],
                    "actions": [],
                    "quick_replies": []
                }
            },
            "message_tag": "ACCOUNT_UPDATE"
        }
    else:
        quick_replies = []
        if "buttons" in message_data:
            for btn_caption in message_data["buttons"][:10]:
                quick_replies.append({
                    "type": "flow",
                    "caption": btn_caption,
                    "target": "content20250708231332_237555"
                })
        payload = {
            "subscriber_id": subscriber_id,
            "data": {
                "version": "v2",
                "content": {
                    "messages": [
                        {
                            "type": "text",
                            "text": message_data["text"]
                        }
                    ],
                    "actions": [],
                    "quick_replies": quick_replies
                }
            },
            "message_tag": "ACCOUNT_UPDATE"
        }

    response = requests.post(
        send_url,
        headers=headers,
        json=payload,
        timeout=10
    )
    return response.status_code, response.json()

def send_twilio_message(to_phone, message_data):
    try:
        message_body = message_data["text"]
        if "buttons" in message_data:
            button_texts = [f"- {btn}" for btn in message_data["buttons"]]
            message_body += "\n\n" + "\n".join(button_texts)

        twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_phone}"
        )
        return 200, {"status": "ok"}
    except Exception as e:
        return 500, {"error": str(e)}

def send_unified_message(session, message_data):
    source = session.metadata.get("source", "twilio")
    if source.startswith("manychat"):
        subscriber_id = session.metadata.get("subscriber_id")
        channel = "whatsapp" if source == "manychat_whatsapp" else "facebook"
        return send_manychat_message(subscriber_id, message_data, channel)
    else:
        return send_twilio_message(session.user_phone, message_data)

def get_request_data_and_source(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        if data.get("whatsapp_phone"):
            return data, "manychat_whatsapp"
        if "id" in data and "last_input_text" in data:
            return data, "manychat_messenger"
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    data = request.POST.dict()
    if "From" in data:
        return data, "twilio"

    return {}, None

def upload_media_to_last_siniestro(session):
    from .models import ConversationMessage
    one_hour_ago = timezone.now() - timedelta(hours=1)
    last_user_msg = ConversationMessage.objects.filter(session__user_phone=session.user_phone, is_user=True).order_by('-created_at').first()
    if not last_user_msg or last_user_msg.created_at < one_hour_ago:
        return
    target_session = ConversationSession.objects.filter(user_phone=session.user_phone, metadata__siniestro_id__isnull=False).order_by('-id').first()
    if not target_session:
        return
    siniestro_id = target_session.metadata.get("siniestro_id")
    if not siniestro_id:
        return
    try:
        siniestro = Siniestro.objects.get(id=siniestro_id)
    except Siniestro.DoesNotExist:
        return
    pending = session.metadata.get("pending_media", [])
    if not pending:
        return
    for item in pending:
        SiniestroMedia.objects.create(
            siniestro=siniestro,
            file_url=item["url"],
            tipo=item["tipo"]
        )
    session.metadata["pending_media"] = []
    session.save(update_fields=["metadata"])

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    data, source = get_request_data_and_source(request)
    print(data)
    print(source)
    if not source:
        return HttpResponse(status=400)
    if source == "manychat_whatsapp":
        from_number = data.get("whatsapp_phone", "").replace("whatsapp:", "")
        subscriber_id = data.get("id")
        last_text = data.get("last_input_text", "").strip()
        num_media = int(data.get("NumMedia", 0))
    elif source == "manychat_messenger":
        subscriber_id = data.get("id")
        from_number = f"messenger:{subscriber_id}"
        last_text = data.get("last_input_text", "").strip()
        num_media = int(data.get("NumMedia", 0)) if "NumMedia" in data else 0
    else:
        from_number = data.get("From", "").replace("whatsapp:", "")
        subscriber_id = None
        last_text = data.get("Body", "").strip()
        num_media = int(data.get("NumMedia", 0))
    if source.startswith("manychat") and num_media == 0 and last_text:
        pattern = re.compile(r'^https?://.+\.(?:jpg|jpeg|png|gif|mp4|mov|ogg|mp3)(?:\?.*)?$', re.IGNORECASE)
        if pattern.match(last_text):
            media_url = last_text
            content_type = mimetypes.guess_type(media_url)[0] or "application/octet-stream"
            data["NumMedia"] = "1"
            data["MediaUrl0"] = media_url
            data["MediaContentType0"] = content_type
            last_text = ""
            num_media = 1
    session = get_or_create_session(from_number)
    if source.startswith("manychat"):
        session.metadata["subscriber_id"] = subscriber_id
        session.metadata["source"] = source
        session.save()
    else:
        session.metadata["source"] = "twilio"
        session.save()
    transcribed_audio_text = attach_incoming_media_and_maybe_transcribe(session, data, source)
    if num_media > 0 and not last_text and not transcribed_audio_text:
        if session.current_flow == "registrar_siniestro" and session.current_step != "DONE":
            msg_data = RegistrarSiniestroFlowComponent(session).handle("")
        else:
            upload_media_to_last_siniestro(session)
            msg_data = {"text": "Media recibida y registrada."}
        store_message(session, text=msg_data["text"], is_user=False)
        send_unified_message(session, msg_data)
        return HttpResponse(status=200)
    body = (last_text + " " + transcribed_audio_text).strip()
    intent = "registrar_siniestro" if session.current_step == "START" else session.current_flow or "registrar_siniestro"
    store_message(session, text=body, is_user=True, intent=intent)
    if session.current_flow == "" and session.current_step == "START":
        session.current_flow = intent
        if intent == "consultar_poliza":
            session.current_step = "DONE"
            session.closed_at = session.closed_at or timezone.now()
            msg_data = ConsultarPolizaFlowComponent(session).handle(body)
        else:
            msg_data = RegistrarSiniestroFlowComponent(session).handle(body)
        session.save()
    elif session.current_flow == "registrar_siniestro":
        msg_data = RegistrarSiniestroFlowComponent(session).handle(body)
    elif session.current_flow == "consultar_poliza":
        msg_data = ConsultarPolizaFlowComponent(session).handle(body)
    else:
        msg_data = {"text": "¿En qué más puedo ayudarte? (Manejo siniestros y consulta de pólizas)."}
    store_message(session, text=msg_data["text"], is_user=False)
    send_unified_message(session, msg_data)
    return HttpResponse(status=200)

@csrf_exempt
@require_http_methods(["POST"])
def upload_media(request):
    siniestro_id = request.POST.get("siniestro_id")
    files = request.FILES.getlist("file")
    if not siniestro_id or not files:
        return JsonResponse({"error": "Siniestro ID y archivos son requeridos"}, status=400)

    try:
        siniestro = Siniestro.objects.get(id=siniestro_id)
    except Siniestro.DoesNotExist:
        return JsonResponse({"error": "Siniestro no encontrado"}, status=404)

    session = ConversationSession.objects.filter(
        metadata__siniestro_id=siniestro_id
    ).order_by("-id").first()

    if not session:
        return JsonResponse({"error": "No existe una sesión asociada a este siniestro."}, status=400)

    if session.closed_at and (timezone.now() - session.closed_at) > timedelta(hours=1):
        return JsonResponse({"error": "Ha excedido la 1 hora para subir evidencia después de finalizar el registro."}, status=400)

    file_urls = []
    for file in files:
        filename = default_storage.save(f"siniestros_media/{file.name}", file)
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
            action=f"Medio subido: {file.name}",
            media=media
        )

        file_urls.append(file_url)

    return JsonResponse({"urls": file_urls})