
from django.core.files.storage import default_storage
from transformers import BertTokenizer, BertModel
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from twilio.rest import Client
from gtts import gTTS
import tempfile
import requests
import whisper
import torch
import uuid
import os
import re

from .models import (
    ConversationSession, ConversationMessage, Colaboradores, Siniestro,
    Vehiculos, SiniestroMedia
)

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_CONTENT_SID = os.getenv('TWILIO_CONTENT_SID')
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

LABELS = {
    0: "registrar_siniestro",
    1: "consultar_estado",
    2: "pedir_asistencia",
    3: "consultar_poliza",
    4: "solicitar_reparacion",
    5: "otro"
}

MODEL_NAME = "dccuchile/bert-base-spanish-wwm-cased"
MODEL_PATH = os.path.join(settings.BASE_DIR, 'trainings', 'intencion', 'best_model_intenciones_bert.pth')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

WHISPER_MODEL = None
bert_classifier_model = None
bert_tokenizer = None

try:
    print("Cargando modelo Whisper (medium)...")
    WHISPER_MODEL = whisper.load_model("medium")
    print("Modelo Whisper cargado.")
except Exception as e:
    print(f"ERROR CRÍTICO: No se pudo cargar el modelo Whisper: {e}")

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

try:
    print(f"Cargando modelo BERT desde: {MODEL_PATH}")
    bert_classifier_model = BERTIntentClassifier(bert_model=MODEL_NAME, num_labels=len(LABELS), freeze_bert=True).to(device)
    state_dict = torch.load(MODEL_PATH, map_location=device, weights_only=True)
    bert_classifier_model.load_state_dict(state_dict)
    bert_classifier_model.eval()
    print("Modelo BERT cargado.")
    print("Cargando tokenizer BERT...")
    bert_tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
    print("Tokenizer BERT cargado.")
except FileNotFoundError:
    print(f"ERROR CRÍTICO: Archivo de modelo BERT no encontrado en {MODEL_PATH}")
except Exception as e:
    print(f"ERROR CRÍTICO: No se pudo cargar el modelo BERT o el tokenizer: {e}")


def check_ffmpeg_installed():
    return True

def process_audio_file_sync(audio_data, file_extension):
    if not WHISPER_MODEL:
        print("Error en process_audio_file_sync: Modelo Whisper no cargado.")
        return None
    try:
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        temp_path = os.path.join(tempfile.gettempdir(), unique_filename)
        with open(temp_path, 'wb') as f:
            f.write(audio_data)

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            print(f"Error en process_audio_file_sync: Archivo temporal no válido o vacío en {temp_path}")
            return None
        if not check_ffmpeg_installed():
            print("Error en process_audio_file_sync: ffmpeg no instalado.")
            return None

        result = WHISPER_MODEL.transcribe(temp_path, language='es')
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return result["text"]
    except Exception as e:
        print(f"Excepción en process_audio_file_sync: {e}")
        return None

def infer_intent(text: str) -> str:
    if not bert_classifier_model or not bert_tokenizer:
        print("Error en infer_intent: Modelo BERT o tokenizer no están cargados.")
        return LABELS[5]

    try:
        encoded = bert_tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=64,
            return_tensors="pt"
        ).to(device)
        with torch.no_grad():
            logits = bert_classifier_model(encoded["input_ids"], encoded["attention_mask"])
            predicted_id = torch.argmax(logits, dim=1).item()
        return LABELS[predicted_id]
    except Exception as e:
        print(f"Excepción en infer_intent: {e}")
        return LABELS[5]


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

def get_or_create_session(user_phone: str, has_media: bool = False) -> ConversationSession:
    one_hour_ago = timezone.now() - timedelta(hours=1)
    sessions = ConversationSession.objects.filter(user_phone=user_phone).order_by("-id")
    active_session = sessions.exclude(current_step="DONE").first()

    if active_session:
        return active_session

    if has_media:
        recent_done_session = sessions.filter(current_step="DONE", current_flow='registrar_siniestro', closed_at__gte=one_hour_ago).first()
    else:
        recent_done_session = None

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
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_phone}"
        )
    except Exception as e:
        print(f"Error enviando mensaje de WhatsApp: {e}")


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

    from .consumers import broadcast_siniestro_update
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

def _download_and_store_media_file(media_url: str, content_type: str) -> str:
    try:
        response = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        response.raise_for_status()
        content = response.content

        extension = "bin"
        if "image" in content_type:
            extension = content_type.split("/")[-1]
            if extension == "jpeg": extension = "jpg"
        elif "video" in content_type:
            extension = content_type.split("/")[-1]
        elif "audio" in content_type:
            extension = content_type.split("/")[-1]

        unique_filename = f"siniestros_media/{uuid.uuid4()}.{extension}"
        file_url = default_storage.save(unique_filename, ContentFile(content))
        return file_url
    except Exception as e:
        print(f"Error en _download_and_store_media_file: {e}")
        return None

def transcribe_audio_from_twilio_media_url(media_url: str, content_type: str) -> str:
    if not WHISPER_MODEL:
        print("Error en transcribe_audio_from_twilio_media_url: Modelo Whisper no cargado.")
        return ""
    try:
        response = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        response.raise_for_status()
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
    except Exception as e:
        print(f"Excepción en transcribe_audio_from_twilio_media_url: {e}")
        return ""

# utils.py

# utils.py

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
        # Nuevo manejo: guardamos siempre el archivo, incluso si es audio
        stored_url = _download_and_store_media_file(media_url, media_type) or media_url
        session.metadata["pending_media"].append({"url": stored_url, "tipo": media_type})
        # Solo transcribimos si es audio
        if "audio" in media_type:
            result_text = transcribe_audio_from_twilio_media_url(media_url, media_type)
            if result_text:
                transcribed_text = f"{transcribed_text} {result_text}".strip()
    session.save(update_fields=["metadata"])
    return transcribed_text



def create_tts_audio(text: str, request) -> str:
    try:
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(settings.MEDIA_ROOT, filename)
        tts = gTTS(text=text, lang='es')
        tts.save(filepath)
        full_url = request.build_absolute_uri(settings.MEDIA_URL + filename)
        return full_url
    except Exception as e:
        print(f"Error creando TTS audio: {e}")
        return ""

def check_whisper_model_availability():
    if not WHISPER_MODEL:
        print("Error: Modelo Whisper (WHISPER_MODEL) no está cargado globalmente.")
        return False
    return True