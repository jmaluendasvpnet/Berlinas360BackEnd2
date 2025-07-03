# myapp/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from .models import Login, Permisos, Notification
from django.contrib.auth import authenticate
from .serializers import ColaboradoresSlr
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.conf import settings
import urllib.parse
import logging
import json
import jwt

logger = logging.getLogger('myapp.consumers')

active_users = {}

class SessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        user = self.scope.get('user')
        if user and user.is_authenticated and user.username in active_users:
            del active_users[user.username]
            await self.broadcast_users_list()

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action', '')

        if action == 'login':
            await self.handle_login(text_data_json)
        elif action == 'login_with_token':
            await self.handle_login_with_token(text_data_json)

    async def handle_login(self, data):
        username = data.get('username')
        password = data.get('password')

        user = await sync_to_async(authenticate)(username=username, password=password)
        if user is not None:
            await self.login_user(user)
        else:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'Credenciales inválidas'
            }))

    async def handle_login_with_token(self, data):
        token = data.get('token')
        if not token:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'Token no proporcionado'
            }))
            return

        user = await sync_to_async(self.authenticate_with_token)(token)
        if user is not None:
            await self.login_user(user)
        else:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': 'Token inválido o expirado'
            }))

    def authenticate_with_token(self, token):
        try:
            user = Login.objects.get(single_use_token=token, is_active=True)
            if user.expiration_time and user.expiration_time < timezone.now():
                return None
            if user.has_logged_in:
                return None
            user.has_logged_in = True
            user.save()
            return user
        except Login.DoesNotExist:
            return None

    async def login_user(self, user):
        rol_id = await sync_to_async(self.get_rol_id)(user)
        payload = {
            "username": user.username,
            "nombre": user.first_name,
            "apellido": user.last_name,
            "rol_id": rol_id
        }
        token_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        colaborador = await sync_to_async(lambda: user.documento_num)()
        colaborador_serializer = ColaboradoresSlr(colaborador)
        colaborador_data = await sync_to_async(lambda: colaborador_serializer.data)()
        modules = await sync_to_async(self.get_user_modules)(user)

        active_users[user.username] = self
        logger.info({
            'status': 'ok',
            'token': token_jwt,
            'username': user.username,
            'nombre': user.first_name,
            'apellido': user.last_name,
            'rol_id': rol_id,
            'modulos': modules,
            'colaborador': colaborador_data,
            'message': f'{user.first_name} ha iniciado sesión'
        })
        await self.send(text_data=json.dumps({
            'status': 'ok',
            'token': token_jwt,
            'username': user.username,
            'nombre': user.first_name,
            'apellido': user.last_name,
            'rol_id': rol_id,
            'modulos': modules,
            'colaborador': colaborador_data,
            'message': f'{user.first_name} ha iniciado sesión'
        }))

        await self.broadcast_users_list()

    def get_rol_id(self, user):
        try:
            return user.documento_num.rol_id.id_rol
        except AttributeError:
            return None

    async def send_users_list(self):
        users_list = list(active_users.keys())
        await self.send(text_data=json.dumps({
            'action': 'update_users_list',
            'users': users_list
        }))

    def get_user_modules(self, user):
        role = user.documento_num.rol_id
        permisos = Permisos.objects.filter(rol=role, estado_permiso=True)
        modules = permisos.values_list('modulo__link', flat=True)
        return list(modules)

    async def broadcast_users_list(self):
        users_list = list(active_users.keys())
        message = json.dumps({
            'action': 'update_users_list',
            'users': users_list
        })
        for connection in active_users.values():
            await connection.send(text_data=message)

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        token = self.get_token_from_query_string(query_string)

        user = await sync_to_async(self.authenticate_with_token)(token)
        
        if not user or isinstance(user, AnonymousUser):
            await self.close()
        else:
            self.scope['user'] = user
            self.group_name = f"user_{user.documento_num_id}"
            logger.info(f"Group name in consumer: {self.group_name}")

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

            notifications = await self.get_pending_notifications()

            for notification in notifications:
                await self.send_notification({
                    "type": "send_notification",
                    "content": {
                        'id': notification.id,
                        'type': notification.type,
                        'content': notification.content,
                        'time': notification.time.isoformat(),
                        'status': notification.status,
                    }
                })
                await self.mark_notification_as_read(notification)

    def get_token_from_query_string(self, query_string):
        parsed_qs = urllib.parse.parse_qs(query_string)
        return parsed_qs.get('token', [None])[0]

    def authenticate_with_token(self, token):
        if not token:
            return None
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            username = payload.get('username')
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(username=username)
            return user
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return None

    async def disconnect(self, close_code):
        if not self.scope["user"].is_anonymous:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        logger.info('Enviando notificación')
        await self.send_json(event)

    @sync_to_async
    def get_pending_notifications(self):
        return list(
            Notification.objects.filter(
                user__num_documento=self.scope['user'].documento_num_id,
                is_read=False
            )
        )

    @sync_to_async
    def mark_notification_as_read(self, notification):
        notification.is_read = True
        notification.save()

# myapp/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import SiniestrosSlr
from django.conf import settings
from .models import Siniestro
import subprocess
import tempfile
import logging
import whisper
import base64
import math
import json
import uuid
import os

logger = logging.getLogger(__name__)

WHISPER_MODEL = whisper.load_model("medium")

ROUTE = [
    {"name": "Bogotá", "lat": 4.711, "lng": -74.0721},
    {"name": "Tunja", "lat": 4.1339, "lng": -73.6340},
    {"name": "Barbosa", "lat": 7.1122, "lng": -73.1035},
    {"name": "Socorro", "lat": 7.0000, "lng": -73.0170},
    {"name": "San Gil", "lat": 6.7333, "lng": -73.1167},
    {"name": "Bucaramanga", "lat": 7.1254, "lng": -73.1198},
    {"name": "Barranquilla", "lat": 10.9685, "lng": -74.7813},
    {"name": "Santa Marta", "lat": 11.2408, "lng": -74.1990},
    {"name": "Cúcuta", "lat": 7.8939, "lng": -72.5079},
    {"name": "Pamplona", "lat": 7.3841, "lng": -72.1393},
    {"name": "Cartagena", "lat": 10.3910, "lng": -75.4794},
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def compute_enhanced_address(lat, lng):
    logger.debug(f"compute_enhanced_address called with lat={lat}, lng={lng}")
    min_diff = float('inf')
    best_info = None

    for i in range(len(ROUTE) - 1):
        cityA = ROUTE[i]
        cityB = ROUTE[i + 1]
        distAB = haversine(cityA["lat"], cityA["lng"], cityB["lat"], cityB["lng"])
        distA_loc = haversine(cityA["lat"], cityA["lng"], lat, lng)
        distLoc_B = haversine(lat, lng, cityB["lat"], cityB["lng"])
        sum_dist = distA_loc + distLoc_B
        diff = abs(distAB - sum_dist)

        logger.debug(
            f"Segment {cityA['name']} -> {cityB['name']} | "
            f"distAB={distAB}, distA_loc={distA_loc}, distLoc_B={distLoc_B}, "
            f"sum_dist={sum_dist}, diff={diff}, min_diff={min_diff}"
        )

        if diff < min_diff:
            min_diff = diff
            best_info = (cityA, cityB, distAB, distA_loc, distLoc_B)

    logger.debug(f"Best info after loop: {best_info}")

    if best_info is not None:
        cityA, cityB, distAB, distA_loc, distLoc_B = best_info
        if distAB * 0.95 <= (distA_loc + distLoc_B) <= distAB * 1.05:
            distA_locKM = round(distA_loc / 1000, 1)
            result = f"Se encuentra en {cityA['name']} en el kilómetro {distA_locKM} vía {cityB['name']}"
            logger.debug(f"Match found, returning: {result}")
            return result

    closest_city = None
    min_city_dist = float('inf')
    for city in ROUTE:
        d = haversine(city["lat"], city["lng"], lat, lng)
        if d < min_city_dist:
            min_city_dist = d
            closest_city = city

    logger.debug(f"Closest city: {closest_city}, distance: {min_city_dist}")

    if closest_city:
        dist_km = round(min_city_dist / 1000, 1)
        result = (
            f"Se encuentra a {dist_km} km de la ciudad de {closest_city['name']}. "
            "La ubicación actual no coincide con ninguna ruta conocida."
        )
        logger.debug(f"No segment match, returning closest city result: {result}")
        return result

    logger.debug("No route match and no closest city found, returning default message.")
    return "La ubicación actual no coincide con ninguna ruta conocida."

def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except:
        return False

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

        result = WHISPER_MODEL.transcribe(temp_path)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return result["text"]
    except Exception:
        return None

def broadcast_siniestro_update(siniestro_id: int):
    from .models import Siniestro
    from .serializers import SiniestrosSlr

    channel_layer = get_channel_layer()
    
    siniestro = Siniestro.objects.select_related(
        "colaborador", "vehiculo", "empresa", "acta_conciliacion"
    ).prefetch_related(
        "media", "entes_atendieron", "logs__user", "terceros"
    ).get(id=siniestro_id)

    data = SiniestrosSlr(siniestro).data

    if data.get("latitud") and data.get("longitud"):
        data["enhanced_address"] = compute_enhanced_address(
            float(data["latitud"]),
            float(data["longitud"])
        )
    else:
        data["enhanced_address"] = ""

    async_to_sync(channel_layer.group_send)(
        f"siniestro_{siniestro_id}",
        {
            "type": "siniestro_update",
            "content": data,
        }
    )

class SiniestroConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.siniestro_id = self.scope['url_route']['kwargs']['siniestro_id']
        self.group_name = f"siniestro_{self.siniestro_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command')
        if command == 'fetch_siniestro':
            await self.fetch_siniestro(data)
        elif command == 'update_siniestro':
            await self.update_siniestro(data)
        elif command == 'update_conciliacion':
            await self.update_conciliacion(data)
        elif command == 'update_terceros':
            await self.update_terceros(data)
        else:
            await self.send(json.dumps({"command": "error", "content": "Comando no reconocido."}))

    async def fetch_siniestro(self, data):
        siniestro_id = data.get('siniestroId')
        try:
            siniestro = await database_sync_to_async(
                Siniestro.objects.select_related(
                    "colaborador",
                    "vehiculo",
                    "empresa",
                    "acta_conciliacion"
                ).prefetch_related(
                    "media",
                    "entes_atendieron",
                    "logs__user",
                    "terceros"
                ).get
            )(id=siniestro_id)

            serializer_data = await database_sync_to_async(lambda: SiniestrosSlr(siniestro).data)()

            if serializer_data.get("latitud") and serializer_data.get("longitud"):
                serializer_data["enhanced_address"] = compute_enhanced_address(
                    float(serializer_data["latitud"]),
                    float(serializer_data["longitud"])
                )
            else:
                serializer_data["enhanced_address"] = ""

            await self.send(json.dumps({
                "command": "siniestro_update",
                "content": serializer_data,
            }))
        except Siniestro.DoesNotExist:
            await self.send(json.dumps({
                "command": "error",
                "content": "No se encontró el siniestro."
            }))

    async def update_siniestro(self, data):
        siniestro_id = data.get('siniestroId')
        update_data = data.get('data', {})
        try:
            siniestro = await database_sync_to_async(Siniestro.objects.get)(id=siniestro_id)
        except Siniestro.DoesNotExist:
            await self.send(json.dumps({"command": "error", "content": "No se encontró el siniestro."}))
            return

        if update_data.get('audio_descripcion'):
            try:
                audio_data_base64 = update_data.pop('audio_descripcion')
                audio_data = base64.b64decode(audio_data_base64)
                transcription = await database_sync_to_async(process_audio_file_sync)(audio_data, 'wav')
                if siniestro.descripcion:
                    siniestro.descripcion += "\n" + (transcription or "")
                else:
                    siniestro.descripcion = transcription or ""
            except:
                await self.send(json.dumps({
                    "command": "error",
                    "content": "Error al procesar audio."
                }))
                return

        for key, value in update_data.items():
            if key == "entes_atendieron":
                if not value:
                    await database_sync_to_async(siniestro.entes_atendieron.clear)()
                else:
                    if isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            value = []
                    value = [item for item in value if item is not None]
                    await database_sync_to_async(siniestro.entes_atendieron.set)(value)
            else:
                setattr(siniestro, key, value)

        if 'latitud' in update_data and 'longitud' in update_data:
            try:
                lat = float(update_data['latitud'])
                lng = float(update_data['longitud'])
                siniestro.direccion_text = compute_enhanced_address(lat, lng)
            except:
                siniestro.direccion_text = ""

        await database_sync_to_async(siniestro.save)()

        updated_siniestro = await database_sync_to_async(
            Siniestro.objects.select_related(
                "colaborador",
                "vehiculo",
                "empresa",
                "acta_conciliacion"
            ).prefetch_related(
                "media",
                "entes_atendieron",
                "logs__user",
                "terceros"
            ).get
        )(id=siniestro_id)

        serializer_data = await database_sync_to_async(lambda: SiniestrosSlr(updated_siniestro).data)()

        if serializer_data.get("latitud") and serializer_data.get("longitud"):
            serializer_data["enhanced_address"] = compute_enhanced_address(
                float(serializer_data["latitud"]),
                float(serializer_data["longitud"])
            )
        else:
            serializer_data["enhanced_address"] = ""

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "siniestro_update",
                "content": serializer_data,
            }
        )

    async def update_conciliacion(self, data):
        siniestro_id = data.get('siniestroId')
        payload = data.get('data', {})
        try:
            siniestro = await database_sync_to_async(Siniestro.objects.get)(id=siniestro_id)
            acta = await database_sync_to_async(lambda: getattr(siniestro, 'acta_conciliacion', None))()
            if acta:
                for key, value in payload.items():
                    setattr(acta, key, value)
                await database_sync_to_async(acta.save)()
            else:
                from .models import ActaConciliacion
                acta = ActaConciliacion(siniestro=siniestro, **payload)
                await database_sync_to_async(acta.save)()

            updated_siniestro = await database_sync_to_async(
                Siniestro.objects.select_related(
                    "colaborador",
                    "vehiculo",
                    "empresa",
                    "acta_conciliacion"
                ).prefetch_related(
                    "media",
                    "entes_atendieron",
                    "logs__user",
                    "terceros"
                ).get
            )(id=siniestro_id)

            serializer_data = await database_sync_to_async(lambda: SiniestrosSlr(updated_siniestro).data)()

            if serializer_data.get("latitud") and serializer_data.get("longitud"):
                serializer_data["enhanced_address"] = compute_enhanced_address(
                    float(serializer_data["latitud"]),
                    float(serializer_data["longitud"])
                )
            else:
                serializer_data["enhanced_address"] = ""

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "siniestro_update",
                    "content": serializer_data,
                }
            )
        except Siniestro.DoesNotExist:
            await self.send(json.dumps({
                "command": "error",
                "content": "No se encontró el siniestro."
            }))

    async def update_terceros(self, data):
        siniestro_id = data.get('siniestroId')
        terceros_data = data.get('data', [])
        try:
            siniestro = await database_sync_to_async(Siniestro.objects.get)(id=siniestro_id)

            updated_siniestro = await database_sync_to_async(
                Siniestro.objects.select_related(
                    "colaborador",
                    "vehiculo",
                    "empresa",
                    "acta_conciliacion"
                ).prefetch_related(
                    "media",
                    "entes_atendieron",
                    "logs__user",
                    "terceros"
                ).get
            )(id=siniestro_id)

            serializer_data = await database_sync_to_async(lambda: SiniestrosSlr(updated_siniestro).data)()

            if serializer_data.get("latitud") and serializer_data.get("longitud"):
                serializer_data["enhanced_address"] = compute_enhanced_address(
                    float(serializer_data["latitud"]),
                    float(serializer_data["longitud"])
                )
            else:
                serializer_data["enhanced_address"] = ""

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "siniestro_update",
                    "content": serializer_data,
                }
            )
        except Siniestro.DoesNotExist:
            await self.send(json.dumps({
                "command": "error",
                "content": "No se encontró el siniestro."
            }))

    async def siniestro_update(self, event):
        await self.send(json.dumps({
            "command": "siniestro_update",
            "content": event["content"],
        }))
