# views_whatsapp.py
TWILIO_ACCOUNT_SID = "key"
TWILIO_AUTH_TOKEN = "key"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_VOICE_FROM = "+1234567890"


from .models import (
    ConversationSession, ConversationMessage, Colaboradores, Siniestro,
    Vehiculos, VehiculoPropietario, Propietario, Tercero, ActaConciliacion,
    Soat, RevisionTecnomecanica, SiniestroMedia, Empresas, SiniestroLog
)
from django.views.decorators.http import require_http_methods
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from transformers import BertTokenizer, BertModel
from .consumers import broadcast_siniestro_update
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from twilio.rest import Client
from gtts import gTTS
import requests
import tempfile
import whisper
import torch
import uuid
import re
import os

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

LABELS = {
    0: "registrar_siniestro",
    3: "consultar_poliza",
    5: "otro"
}

MODEL_NAME = "dccuchile/bert-base-spanish-wwm-cased"
MODEL_PATH = "C:/Users/jemal/OneDrive/Desktop/Berlinas/BerliDATA/Berlinas360BackEnd/trainings/intencion/best_model_intenciones_bert.pth"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

WHISPER_MODEL = whisper.load_model("medium")

def check_ffmpeg_installed():
    return True

def process_audio_file_sync(audio_data, file_extension):
    try:
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        temp_path = os.path.join(tempfile.gettempdir(), unique_filename)
        with open(temp_path, 'wb') as f:
            f.write(audio_data)

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            return None
        if not check_ffmpeg_installed():
            return None

        result = WHISPER_MODEL.transcribe(temp_path, language='es')
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return result["text"]
    except Exception:
        return None

class BERTIntentClassifier(torch.nn.Module):
    def __init__(self, bert_model, num_labels, freeze_bert=True):
        super().__init__()
        self.bert = BertModel.from_pretrained(bert_model)
        if freeze_bert:
            for param in self.bert.parameters():
                param.requires_grad = False
        self.dropout = torch.nn.Dropout(0.3)
        self.fc = torch.nn.Linear(768, num_labels)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        pooled_output = self.dropout(pooled_output)
        logits = self.fc(pooled_output)
        return logits

model = BERTIntentClassifier(bert_model=MODEL_NAME, num_labels=len(LABELS), freeze_bert=True).to(device)
state_dict = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(state_dict)
model.eval()

tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)

def infer_intent(text: str) -> str:
    encoded = tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=64,
        return_tensors="pt"
    ).to(device)
    with torch.no_grad():
        logits = model(encoded["input_ids"], encoded["attention_mask"])
        predicted_id = torch.argmax(logits, dim=1).item()
    return LABELS[predicted_id]

def store_message(session: ConversationSession, text: str, is_user: bool, intent: str = None):
    ConversationMessage.objects.create(
        session=session,
        text=text,
        is_user=is_user,
        intent=intent if intent else ""
    )

def get_driver_by_phone(user_phone: str):
    try:
        return Colaboradores.objects.get(telefono=user_phone)
    except Colaboradores.DoesNotExist:
        return None

def get_or_create_session(user_phone: str) -> ConversationSession:
    one_hour_ago = timezone.now() - timedelta(hours=1)
    sessions = ConversationSession.objects.filter(user_phone=user_phone).order_by("-id")

    active_session = sessions.exclude(current_step="DONE").first()
    print(active_session)
    if active_session:
        return active_session

    recent_done_session = sessions.filter(current_step="DONE", closed_at__gte=one_hour_ago).first()
    if recent_done_session:
        return recent_done_session

    session = ConversationSession.objects.create(
        user_phone=user_phone,
        current_flow="",
        current_step="START",
        metadata={}
    )

    driver = get_driver_by_phone(user_phone)
    if driver and driver.vehiculo and not session.metadata.get("placa"):
        session.metadata["placa"] = driver.vehiculo.placa
        session.metadata["documento"] = str(driver.num_documento)
        session.metadata["conductor_nombre"] = f"{driver.nombres} {driver.apellidos}"
        session.save()

    return session

def parse_user_data(text: str) -> dict:
    data = {"placa": None, "documento": None}
    text_upper = text.upper()

    placa_label_pattern = re.compile(r'(?i)\bPLAC[A-Z]*[:\s]*([\w\s-]+)')
    placa_match = placa_label_pattern.search(text)
    if placa_match:
        candidate = placa_match.group(1)
        candidate_clean = re.sub(r'[^A-Z0-9]', '', candidate.upper())
        if re.fullmatch(r'[A-Z]{3}\d{3,4}', candidate_clean):
            data["placa"] = candidate_clean

    if not data["placa"]:
        placa_generic_pattern = re.compile(r'((?:[A-Z][\s-]*){3}(?:\d[\s-]*){3,4})')
        for candidate in placa_generic_pattern.findall(text_upper):
            candidate_clean = re.sub(r'[^A-Z0-9]', '', candidate)
            if re.fullmatch(r'[A-Z]{3}\d{3,4}', candidate_clean):
                data["placa"] = candidate_clean
                break

    doc_label_pattern = re.compile(r'(?i)\b(?:C[EÉ]DULA|DOCUMENTO)[:\s]*([\d\s.-]+)')
    doc_match = doc_label_pattern.search(text)
    if doc_match:
        candidate = doc_match.group(1)
        candidate_clean = re.sub(r'[^0-9]', '', candidate)
        if 6 <= len(candidate_clean) <= 10:
            data["documento"] = candidate_clean

    if not data["documento"]:
        doc_generic_pattern = re.compile(r'((?:\d[\s-]*){6,10})')
        for candidate in doc_generic_pattern.findall(text):
            candidate_clean = re.sub(r'[^0-9]', '', candidate)
            if 6 <= len(candidate_clean) <= 10:
                data["documento"] = candidate_clean
                break

    return data

def send_whatsapp_notification(to_phone: str, message: str):
    client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_FROM,
        # to=f"whatsapp:+15005550006"
        to=f"whatsapp:{to_phone}"
    )

def register_siniestro(session: ConversationSession) -> Siniestro:
    placa = session.metadata.get("placa")
    documento = session.metadata.get("documento")
    driver = Colaboradores.objects.get(num_documento=documento)
    vehiculo = Vehiculos.objects.get(placa=placa)

    siniestro = Siniestro.objects.create(
        vehiculo=vehiculo,
        colaborador=driver,
        empresa=driver.empresa,
        descripcion=session.metadata.get("descripcion")
    )

    pending_media = session.metadata.get("pending_media", [])
    for item in pending_media:
        SiniestroMedia.objects.create(
            siniestro=siniestro,
            file_url=item["url"],
            tipo=item["tipo"]
        )
    session.metadata["pending_media"] = []
    session.save()

    broadcast_siniestro_update(siniestro.id)
    return siniestro

def notify_propietario(vehiculo: Vehiculos, siniestro_id: int):
    vp_relation = getattr(vehiculo, 'propietarios_relations', None)
    if vp_relation and callable(vp_relation.first):
        relation = vp_relation.first()
        if relation:
            propietario = relation.propietario
            whatsapp_msg = f"Se ha registrado un siniestro (ID: {siniestro_id}) para el vehículo {vehiculo.placa}."
            send_whatsapp_notification(propietario.telefono, whatsapp_msg)

def normalize_plate(plate_input: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', plate_input.upper())

def user_response_says_yes(text: str) -> bool:
    text_lower = text.lower().replace("sí", "si")
    words = re.findall(r'\w+', text_lower)
    return "si" in words

def user_response_says_no(text: str) -> bool:
    text_lower = text.lower()
    words = re.findall(r'\w+', text_lower)
    return "no" in words

def truncate_if_needed(value: str, max_length: int) -> str:
    if len(value) > max_length:
        return value[:max_length]
    return value

def flow_registrar_siniestro(session: ConversationSession, user_text: str) -> str:
    step = session.current_step
    print(step)
    response = ""
    parsed = parse_user_data(user_text)

    def check_documento_valid(doc: str) -> bool:
        return Colaboradores.objects.filter(num_documento=doc).exists()

    def check_placa_valid(placa: str) -> bool:
        return Vehiculos.objects.filter(placa=placa).exists()

    if step == "START":
        placa = parsed.get("placa") or session.metadata.get("placa")
        documento = parsed.get("documento") or session.metadata.get("documento")
        if placa and documento:
            session.metadata["placa"] = placa
            session.metadata["documento"] = documento
            session.current_step = "CONFIRMAR_DATOS"
            response = f"Detecté que tu placa es {placa} y tu documento es {documento}. ¿Son correctos estos datos? (Responde 'Sí' o 'No')"
        else:
            session.current_step = "ASK_PLACA"
            response = "Por favor ingresa la placa del vehículo."
        session.save()

    elif step == "ASK_PLACA":
        if not user_text.strip():
            response = "No pude leer la placa. Ingresa la placa del vehículo."
        else:
            maybe_placa = normalize_plate(user_text)
            if 6 <= len(maybe_placa) <= 7:
                session.metadata["placa"] = maybe_placa
                session.current_step = "ASK_DOCUMENTO"
                response = f"Placa {maybe_placa} recibida. Ahora ingresa tu número de documento."
            else:
                response = "No pude leer la placa. Ingresa la placa del vehículo (Ej: ABC123)."
        session.save()

    elif step == "ASK_DOCUMENTO":
        if not user_text.strip():
            response = "No pude leer el documento. Indica solo números."
        else:
            maybe_doc = re.sub(r'[^0-9]', '', user_text.strip())
            if maybe_doc and 6 <= len(maybe_doc) <= 10:
                session.metadata["documento"] = maybe_doc
                session.current_step = "CONFIRMAR_DATOS"
                response = f"Detecté placa {session.metadata.get('placa')} y doc {maybe_doc}. ¿Son correctos? (Sí/No)"
            else:
                response = "No pude leer el documento. Indica solo números, ej: 12345678."
        session.save()

    elif step == "CONFIRMAR_DATOS":
        if user_response_says_yes(user_text):
            siniestro = register_siniestro(session)
            session.metadata["siniestro_id"] = siniestro.id
            vehiculo = Vehiculos.objects.get(placa=session.metadata.get("placa"))
            notify_propietario(vehiculo, siniestro.id)
            session.current_step = "ASK_DESCRIPCION"
            response = "Por favor, proporciona la descripción del siniestro."
        elif user_response_says_no(user_text):
            session.current_step = "FIX_DOCUMENTO"
            response = "Ok, ingresa tu número de documento correcto."
        else:
            response = "No comprendí tu respuesta. ¿Son correctos estos datos? Responde 'Sí' o 'No'."
        session.save()

    elif step == "FIX_DOCUMENTO":
        doc_input = re.sub(r'[^0-9]', '', user_text.strip())
        if not doc_input.isdigit() or len(doc_input) == 0:
            response = "Documento inválido. Indica solo números."
        else:
            if check_documento_valid(doc_input):
                session.metadata["documento"] = doc_input
                session.current_step = "FIX_PLACA"
                response = f"Documento {doc_input} válido. Ahora ingresa la placa del vehículo."
            else:
                response = "Ese documento no existe en colaboradores. Intenta con otro."
        session.save()

    elif step == "FIX_PLACA":
        placa_input = normalize_plate(user_text)
        if len(placa_input) < 6 or len(placa_input) > 7:
            response = "Formato de placa inválido. Ej: ABC123 o ABC1234. Intenta de nuevo."
        else:
            if check_placa_valid(placa_input):
                session.metadata["placa"] = placa_input
                session.current_step = "CONFIRMAR_DATOS"
                response = (
                    f"Perfecto. Ahora detecté que tu placa es {placa_input} y tu documento es {session.metadata.get('documento')}. "
                    "¿Son correctos estos datos? (Responde 'Sí' o 'No')"
                )
            else:
                response = "No encontré esa placa en la base de datos. Intenta otra."
        session.save()

    elif step == "ASK_DESCRIPCION":
        descripcion = user_text.strip()
        if descripcion:
            session.metadata["descripcion"] = descripcion
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                Siniestro.objects.filter(id=siniestro_id).update(descripcion=descripcion)
                broadcast_siniestro_update(siniestro_id)
            session.current_step = "ASK_UBICACION"
            response = "Siniestro registrado. Por favor, comparte la ubicación."
        else:
            response = "No se pudo leer la descripción. Por favor, proporciona una descripción del siniestro."
        session.save()

    elif step == "ASK_UBICACION":
        latlong_text = user_text.strip()
        if latlong_text:
            parts = latlong_text.split(",")
            if len(parts) == 2:
                lat_str, lon_str = parts[0].strip(), parts[1].strip()
                siniestro_id = session.metadata.get("siniestro_id")
                if siniestro_id:
                    Siniestro.objects.filter(id=siniestro_id).update(
                        latitud=truncate_if_needed(lat_str, 15),
                        longitud=truncate_if_needed(lon_str, 15)
                    )
                    broadcast_siniestro_update(siniestro_id)
                session.metadata["ubicacion"] = f"{lat_str},{lon_str}"
                session.current_step = "ASK_CONCILIACION"
                response = "Ubicación recibida. ¿Está de acuerdo el tercero en la conciliación? (Responde 'Sí' o 'No')"
            else:
                response = "Formato de ubicación inválido. Envía algo como: 4.12345, -72.12345"
        else:
            response = "No se recibió ubicación. Envía lat, long."
        session.save()

    elif step == "ASK_CONCILIACION":
        if user_response_says_yes(user_text):
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=siniestro_id,
                    defaults={"conciliacion_lograda": True}
                )
                broadcast_siniestro_update(siniestro_id)
            session.current_step = "ASK_TERCERO_NOMBRE"
            response = "Por favor, ingresa el nombre completo del tercero (Conductor 2)."
        elif user_response_says_no(user_text):
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=siniestro_id,
                    defaults={"conciliacion_lograda": False}
                )
                broadcast_siniestro_update(siniestro_id)
            session.current_step = "DONE"
            if session.closed_at is None:
                session.closed_at = timezone.now()
            session.save()
            response = "No se llegó a conciliación. Proceso finalizado."
        else:
            response = "No comprendí tu respuesta. ¿Está de acuerdo el tercero en la conciliación? (Responde 'Sí' o 'No')"
        session.save()

    elif step == "ASK_TERCERO_NOMBRE":
        nom = user_text.strip()
        if nom:
            nom_limpio = truncate_if_needed(nom, 250)
            session.metadata["tercero_nombre"] = nom_limpio
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=siniestro_id,
                    defaults={"nombre_completo_conductor2": nom_limpio}
                )
                broadcast_siniestro_update(siniestro_id)
            session.current_step = "ASK_TERCERO_CEDULA"
            response = "Por favor, ingresa la cédula del tercero."
        else:
            response = "No leí el nombre. Inténtalo nuevamente."
        session.save()

    elif step == "ASK_TERCERO_CEDULA":
        ced = user_text.strip()
        if ced:
            ced_limpio = truncate_if_needed(ced, 15)
            session.metadata["tercero_cedula"] = ced_limpio
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=siniestro_id,
                    defaults={"cedula_conductor2": ced_limpio}
                )
                broadcast_siniestro_update(siniestro_id)
            session.current_step = "ASK_TERCERO_PLACA"
            response = "Por favor, ingresa la placa del vehículo del tercero."
        else:
            response = "No leí la cédula. Inténtalo nuevamente."
        session.save()

    elif step == "ASK_TERCERO_PLACA":
        pl = normalize_plate(user_text)
        if pl:
            pl_limpio = truncate_if_needed(pl, 7)
            session.metadata["tercero_placa"] = pl_limpio
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=siniestro_id,
                    defaults={"placa_conductor2": pl_limpio}
                )
                broadcast_siniestro_update(siniestro_id)
            session.current_step = "ASK_TERCERO_TELEFONO"
            response = "Ingresa el número de teléfono del tercero."
        else:
            response = "No pude leer la placa. Inténtalo nuevamente."
        session.save()

    elif step == "ASK_TERCERO_TELEFONO":
        tel = user_text.strip()
        if tel:
            tel_limpio = truncate_if_needed(tel, 15)
            session.metadata["tercero_telefono"] = tel_limpio
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=siniestro_id,
                    defaults={"telefono_conductor2": tel_limpio}
                )
                broadcast_siniestro_update(siniestro_id)
            session.current_step = "ASK_TERCERO_EMAIL"
            response = "Ingresa el email del tercero."
        else:
            response = "No leí el teléfono. Inténtalo nuevamente."
        session.save()

    elif step == "ASK_TERCERO_EMAIL":
        correo = user_text.strip()
        if correo:
            correo_limpio = truncate_if_needed(correo, 50)
            session.metadata["tercero_email"] = correo_limpio
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=siniestro_id,
                    defaults={"email_conductor2": correo_limpio}
                )
                broadcast_siniestro_update(siniestro_id)
            session.current_step = "ASK_CONDUCTOR2_SUMAPAGAR"
            response = "Ingresa la suma a pagar acordada."
        else:
            response = "No leí el email. Inténtalo nuevamente."
        session.save()

    elif step == "ASK_CONDUCTOR2_SUMAPAGAR":
        val = user_text.strip()
        if val:
            val_limpio = truncate_if_needed(val, 15)
            siniestro_id = session.metadata.get("siniestro_id")
            if siniestro_id:
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=siniestro_id,
                    defaults={"suma_a_pagar": val_limpio}
                )
                broadcast_siniestro_update(siniestro_id)

            placa_actual = session.metadata.get("placa", "")
            url_firma = f"http://localhost:8000/sinister/conciliacion?placa={placa_actual}&siniestroId={siniestro_id}"
            response = (
                "Datos de conciliación guardados.\n"
                f"Ingresa al siguiente enlace para firmar la conciliación: {url_firma}\n"
                "Después de esto tienes una hora para subir fotos, videos y audios que formen parte de la evidencia del siniestro."
            )

            session.current_step = "DONE"
            if session.closed_at is None:
                session.closed_at = timezone.now()
            session.save()
        else:
            response = "No leí la suma a pagar. Inténtalo nuevamente."
        session.save()

    else:
        response = "Hemos finalizado el proceso. ¡Gracias!."
        session.current_step = "DONE"
        if session.closed_at is None:
            session.closed_at = timezone.now()
        session.save()

    return response

def flow_consultar_poliza(session: ConversationSession, user_text: str) -> str:
    driver = get_driver_by_phone(session.user_phone)
    if not driver or not driver.vehiculo:
        session.current_step = "DONE"
        if session.closed_at is None:
            session.closed_at = timezone.now()
        session.save()
        return "No se encontró vehículo asociado a tu número de teléfono."

    vehiculo = driver.vehiculo
    soats = Soat.objects.filter(vehiculo=vehiculo, estado=True).order_by('-id')
    revs = RevisionTecnomecanica.objects.filter(vehiculo=vehiculo, estado=True).order_by('-id')
    if not soats and not revs:
        session.current_step = "DONE"
        if session.closed_at is None:
            session.closed_at = timezone.now()
        session.save()
        return "No se encontró SOAT ni Revisión Tecnomecánica para tu vehículo."

    response = ""
    if soats:
        soat = soats.first()
        response += (
            f"SOAT: {soat.numero_poliza} - Expedición: {soat.fecha_expedicion} - "
            f"Vence: {soat.vigencia_hasta}\nDescarga PDF: {soat.soporte}\n\n"
        )
    if revs:
        rev = revs.first()
        response += (
            f"Tecnomecánica Cert: {rev.no_certificado} - Vence: {rev.fecha_vencimiento}\n"
            f"Descarga PDF: {rev.soporte}\n"
        )

    session.current_step = "DONE"
    if session.closed_at is None:
        session.closed_at = timezone.now()
    session.save()
    return response

def _download_and_store_media_file(media_url: str, content_type: str) -> str:
    try:
        response = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        content = response.content

        if "/" in content_type:
            main, sub = content_type.split("/", 1)
        else:
            main, sub = "", ""

        if main in ("image", "video", "audio"):
            extension = sub
        else:
            extension = os.path.splitext(media_url.split("?")[0])[1].lstrip(".") or "bin"

        unique_filename = f"siniestros_media/{uuid.uuid4()}.{extension}"
        file_path = default_storage.save(unique_filename, ContentFile(content))
        return file_path
    except Exception:
        return None


def transcribe_audio_from_twilio_media_url(media_url: str, content_type: str) -> str:
    try:
        response = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        audio_data = response.content
        extension = "ogg"
        if "mpeg" in content_type:
            extension = "mp3"
        elif "amr" in content_type:
            extension = "amr"

        text_transcribed = process_audio_file_sync(audio_data, extension)
        if not text_transcribed:
            return ""
        return text_transcribed.strip()
    except Exception:
        return ""

def attach_incoming_media_and_maybe_transcribe(session: ConversationSession, request_data: dict) -> str:
    num_media = int(request_data.get("NumMedia", "0"))
    transcribed_text = ""
    if num_media == 0:
        return transcribed_text
    if session.closed_at and (timezone.now() - session.closed_at) > timedelta(hours=1):
        return transcribed_text
    if "pending_media" not in session.metadata:
        session.metadata["pending_media"] = []
    for i in range(num_media):
        media_url = request_data.get(f"MediaUrl{i}")
        media_type = request_data.get(f"MediaContentType{i}", "application/octet-stream")
        if not media_url:
            continue
        if "audio" in media_type:
            result_text = transcribe_audio_from_twilio_media_url(media_url, media_type)
            if result_text:
                transcribed_text += f" {result_text}"
        else:
            final_url = _download_and_store_media_file(media_url, media_type)
            if not final_url:
                continue
            if session.current_step == "DONE" and session.metadata.get("siniestro_id"):
                SiniestroMedia.objects.create(
                    siniestro_id=session.metadata["siniestro_id"],
                    file_url=final_url,
                    tipo=media_type
                )
            else:
                session.metadata["pending_media"].append({"url": final_url, "tipo": media_type})
    session.save()
    return transcribed_text.strip()



def create_tts_audio(text: str, request) -> str:
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    tts = gTTS(text=text, lang='es')
    tts.save(filepath)
    full_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
    return full_url

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "POST":
        data = request.POST.dict()
        from_number = data.get("From", "").replace("whatsapp:", "")
        latitude = data.get("Latitude")
        longitude = data.get("Longitude")

        session = get_or_create_session(from_number)

        if latitude and longitude:
            session.metadata["Latitude"] = latitude
            session.metadata["Longitude"] = longitude

        body = data.get("Body", "").strip()
        transcribed_audio_text = attach_incoming_media_and_maybe_transcribe(session, data)

        if not body and not transcribed_audio_text and int(data.get("NumMedia", "0")) > 0:
            reprompt_msg = ""
            if session.current_flow == "registrar_siniestro" and session.current_step != "DONE":
                reprompt_msg = flow_registrar_siniestro(session, "")
            resp = MessagingResponse()
            msg = "Media recibida y registrada. " + reprompt_msg
            resp.message(msg)
            store_message(session, text=msg, is_user=False)
            return HttpResponse(str(resp), content_type="text/xml")

        if not body and "Latitude" in session.metadata and "Longitude" in session.metadata:
            body = f"{session.metadata['Latitude']},{session.metadata['Longitude']}"

        if transcribed_audio_text:
            if body:
                body = f"{body} {transcribed_audio_text}"
            else:
                body = transcribed_audio_text

        if session.current_step == "START":
            intent = 'registrar_siniestro'
        else:
            intent = 'registrar_siniestro'

        store_message(session, text=body, is_user=True, intent=intent if intent else "")

        resp = MessagingResponse()
        reply = resp.message()

        user_sent_audio = False
        num_media = int(data.get("NumMedia", "0"))
        for i in range(num_media):
            media_type = data.get(f"MediaContentType{i}", "")
            if "audio" in media_type:
                user_sent_audio = True
                break
        
        print(body)
        if session.current_flow == "" and session.current_step == "START":
            if intent == "registrar_siniestro":
                session.current_flow = "registrar_siniestro"
                session.save()
                msg = flow_registrar_siniestro(session, body)
            elif intent == "consultar_poliza":
                session.current_flow = "consultar_poliza"
                session.current_step = "DONE"
                if session.closed_at is None:
                    session.closed_at = timezone.now()
                session.save()
                msg = flow_consultar_poliza(session, body)
            else:
                session.current_flow = "general"
                session.current_step = "DONE"
                if session.closed_at is None:
                    session.closed_at = timezone.now()
                session.save()
                msg = "Hola, soy tu asistente. Manejo registro de siniestros y consulta de pólizas."
        elif session.current_flow == "registrar_siniestro":
            msg = flow_registrar_siniestro(session, body)
        elif session.current_flow == "consultar_poliza":
            msg = flow_consultar_poliza(session, body)
        else:
            msg = "¿En qué más puedo ayudarte? (Manejo siniestros y consulta de pólizas)."

        if user_sent_audio:
            audio_url = create_tts_audio(msg, request)
            reply.media(audio_url)
        else:
            reply.body(msg)

        store_message(session, text=msg, is_user=False)
        return HttpResponse(str(resp), content_type="text/xml")

    return HttpResponse("Only POST allowed", status=405)

@csrf_exempt
def voice_webhook(request):
    if request.method == "POST":
        from_number = request.POST.get("From", "")
        user_speech = "Necesito registrar un siniestro ABC123 documento 1234234"

        intent = infer_intent(user_speech)
        session = get_or_create_session(from_number)
        store_message(session, text=user_speech, is_user=True, intent=intent)

        resp = VoiceResponse()
        if intent == "registrar_siniestro":
            parsed = parse_user_data(user_speech)
            if parsed["placa"] and parsed["documento"]:
                session.current_flow = "registrar_siniestro"
                session.current_step = "CONFIRMAR_DATOS"
                session.metadata["placa"] = parsed["placa"]
                session.metadata["documento"] = parsed["documento"]
                session.save()
                msg = (
                    f"Detectamos que tu placa es {parsed['placa']} y tu documento {parsed['documento']}. "
                    "Recibirás un mensaje de WhatsApp para finalizar el registro. Gracias."
                )
            else:
                session.current_flow = "registrar_siniestro"
                session.current_step = "ASK_PLACA"
                session.save()
                msg = (
                    "Iniciaremos el registro de siniestro. "
                    "Te enviaremos un mensaje de WhatsApp para continuar con los datos. Gracias."
                )
            resp.say(msg, voice="alice", language="es-ES")
            store_message(session, text=msg, is_user=False)

        elif intent == "consultar_poliza":
            msg = flow_consultar_poliza(session, user_speech)
            resp.say(msg, voice="alice", language="es-ES")
            store_message(session, text=msg, is_user=False)
            session.current_flow = "consultar_poliza"
            session.current_step = "DONE"
            if session.closed_at is None:
                session.closed_at = timezone.now()
            session.save()
        else:
            msg = (
                "Hola, soy tu asistente. Manejo registro de siniestros y consulta de pólizas. "
                "Envía un mensaje de WhatsApp si necesitas más información."
            )
            resp.say(msg, voice="alice", language="es-ES")
            store_message(session, text=msg, is_user=False)
            session.current_flow = "general"
            session.current_step = "DONE"
            if session.closed_at is None:
                session.closed_at = timezone.now()
            session.save()

        return HttpResponse(str(resp), content_type="text/xml")

    return HttpResponse("Only POST allowed", status=405)

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
