import re
from django.utils import timezone
from .models import Siniestro, ActaConciliacion, Tercero, Colaboradores, Vehiculos, Soat, RevisionTecnomecanica, SiniestroMedia
from .utils import (
    parse_user_data,
    normalize_plate,
    user_response_says_yes,
    user_response_says_no,
    truncate_if_needed,
    register_siniestro,
    notify_propietario,
    get_driver_by_phone
)
from .consumers import broadcast_siniestro_update
from django.conf import settings

class RegistrarSiniestroFlowComponent:
    def __init__(self, session):
        self.session = session

    def check_documento_valid(self, doc):
        return Colaboradores.objects.filter(num_documento=doc).exists()

    def check_placa_valid(self, placa):
        return Vehiculos.objects.filter(placa=placa).exists()

    def get_no_conciliacion_tercero(self):
        siniestro_id = self.session.metadata.get("siniestro_id")
        if not siniestro_id:
            return None
        tercero_id = self.session.metadata.get("current_tercero_id")
        if tercero_id:
            return Tercero.objects.get(id=tercero_id)
        tercero = Tercero.objects.create(siniestro_id=siniestro_id)
        self.session.metadata["current_tercero_id"] = tercero.id
        self.session.save(update_fields=["metadata"])
        return tercero

    def handle(self, user_text):
        step = self.session.current_step
        parsed = parse_user_data(user_text)
        response = {}
        user_text_lower = user_text.lower().strip()

        if step == "START":
            placa = parsed.get("placa") or self.session.metadata.get("placa")
            documento = parsed.get("documento") or self.session.metadata.get("documento")
            if placa and documento:
                self.session.metadata["placa"] = placa
                self.session.metadata["documento"] = documento
                self.session.current_step = "CONFIRMAR_DATOS"
                response["text"] = f"Detecté que tu placa es {placa} y tu documento es {documento}. ¿Son correctos estos datos?"
                response["buttons"] = ["Sí", "No"]
            else:
                self.session.current_step = "ASK_PLACA"
                response["text"] = "Por favor ingresa la placa del vehículo."
            self.session.save()
        elif step == "ASK_PLACA":
            placa_in = normalize_plate(user_text)
            if 6 <= len(placa_in) <= 7:
                self.session.metadata["placa"] = placa_in
                self.session.current_step = "ASK_DOCUMENTO"
                response["text"] = f"Placa {placa_in} recibida. Ahora ingresa tu número de documento."
            else:
                response["text"] = "No pude leer la placa. Ingresa la placa del vehículo (Ej: ABC123)."
            self.session.save()
        elif step == "ASK_DOCUMENTO":
            doc_in = re.sub(r'[^0-9]', '', user_text)
            if 6 <= len(doc_in) <= 10:
                self.session.metadata["documento"] = doc_in
                self.session.current_step = "CONFIRMAR_DATOS"
                response["text"] = f"Detecté placa {self.session.metadata['placa']} y doc {doc_in}. ¿Son correctos?"
                response["buttons"] = ["Sí", "No"]
            else:
                response["text"] = "No pude leer el documento. Indica solo números, ej: 12345678."
            self.session.save()
        elif step == "CONFIRMAR_DATOS":
            if user_response_says_yes(user_text):
                placa_valid = self.check_placa_valid(self.session.metadata["placa"])
                doc_valid = self.check_documento_valid(self.session.metadata["documento"])
                if placa_valid and doc_valid:
                    siniestro = register_siniestro(self.session)
                    self.session.metadata["siniestro_id"] = siniestro.id
                    vehiculo = Vehiculos.objects.get(placa=self.session.metadata["placa"])
                    notify_propietario(vehiculo, siniestro.id)
                    self.session.current_step = "ASK_DESCRIPCION"
                    response["text"] = "Por favor, proporciona la descripción del siniestro."
                    response["buttons"] = ["Omitir"]
                else:
                    if not placa_valid:
                        self.session.current_step = "FIX_PLACA"
                        response["text"] = "La placa no es válida. Ingresa la placa del vehículo."
                    elif not doc_valid:
                        self.session.current_step = "FIX_DOCUMENTO"
                        response["text"] = "El documento no es válido. Ingresa tu número de documento correcto."
            elif user_response_says_no(user_text):
                self.session.current_step = "FIX_DOCUMENTO"
                response["text"] = "Ok, ingresa tu número de documento correcto."
            else:
                response["text"] = "No comprendí tu respuesta. ¿Son correctos estos datos?"
                response["buttons"] = ["Sí", "No"]
            self.session.save()
        elif step == "FIX_DOCUMENTO":
            doc_fix = re.sub(r'[^0-9]', '', user_text)
            if self.check_documento_valid(doc_fix):
                self.session.metadata["documento"] = doc_fix
                self.session.current_step = "FIX_PLACA"
                response["text"] = f"Documento {doc_fix} válido. Ahora ingresa la placa del vehículo."
            else:
                response["text"] = "Ese documento no existe en nuestros registros. Intenta con otro."
            self.session.save()
        elif step == "FIX_PLACA":
            placa_fix = normalize_plate(user_text)
            if self.check_placa_valid(placa_fix):
                self.session.metadata["placa"] = placa_fix
                self.session.current_step = "CONFIRMAR_DATOS"
                response["text"] = f"Ahora detecté placa {placa_fix} y documento {self.session.metadata['documento']}. ¿Son correctos?"
                response["buttons"] = ["Sí", "No"]
            else:
                response["text"] = "No encontré esa placa en la base de datos. Intenta otra."
            self.session.save()
        elif step == "ASK_DESCRIPCION":
            if user_text_lower != "omitir":
                self.session.metadata["descripcion"] = user_text.strip()
                Siniestro.objects.filter(id=self.session.metadata["siniestro_id"]).update(descripcion=user_text.strip())
            else:
                self.session.metadata["descripcion"] = ""
                Siniestro.objects.filter(id=self.session.metadata["siniestro_id"]).update(descripcion="")
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.current_step = "ASK_UBICACION"
            response["text"] = "Descripción recibida. Por favor, comparte la ubicación del siniestro (ej: 4.12345,-72.12345)."
            response["buttons"] = ["Omitir"]
            self.session.save()
        elif step == "ASK_UBICACION":
            if user_text_lower != "omitir" and "," in user_text:
                lat, lon = map(str.strip, user_text.split(",", 1))
                Siniestro.objects.filter(id=self.session.metadata["siniestro_id"]).update(
                    latitud=truncate_if_needed(lat, 15),
                    longitud=truncate_if_needed(lon, 15)
                )
                self.session.metadata["ubicacion"] = f"{lat},{lon}"
            else:
                Siniestro.objects.filter(id=self.session.metadata["siniestro_id"]).update(
                    latitud="",
                    longitud=""
                )
                self.session.metadata["ubicacion"] = ""
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.current_step = "ASK_CONCILIACION"
            response["text"] = "Ubicación recibida. ¿Hay acuerdo con el tercero para conciliación?"
            response["buttons"] = ["Sí", "No", "Conciliador"]
            self.session.save()
        elif step == "ASK_CONCILIACION":
            if user_response_says_yes(user_text_lower):
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=self.session.metadata["siniestro_id"], defaults={"conciliacion_lograda": True}
                )
                broadcast_siniestro_update(self.session.metadata["siniestro_id"])
                self.session.current_step = "ASK_TERCERO_NOMBRE"
                response["text"] = "Por favor, ingresa el nombre completo del tercero (Conductor 2)."
                response["buttons"] = ["Omitir"]
            elif user_response_says_no(user_text_lower):
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=self.session.metadata["siniestro_id"], defaults={"conciliacion_lograda": False}
                )
                broadcast_siniestro_update(self.session.metadata["siniestro_id"])
                self.session.metadata["current_tercero_id"] = None
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_NOMBRE"
                response["text"] = "Entendido. No hay conciliación. Ingresa el nombre completo del conductor del otro vehículo."
                response["buttons"] = ["Omitir"]
            elif "conciliador" in user_text_lower:
                self.session.current_step = "ASK_CONCILIADOR_FOTO"
                response["text"] = "Por favor, sube el archivo o imagen del acuerdo realizado por el conciliador."
            else:
                response["text"] = "No comprendí tu respuesta."
                response["buttons"] = ["Sí", "No", "Conciliador"]
            self.session.save()
        elif step == "ASK_CONCILIADOR_FOTO":
            pending = self.session.metadata.get("pending_media", [])
            if pending:
                path = pending.pop(0)["url"]
                ActaConciliacion.objects.update_or_create(
                    siniestro_id=self.session.metadata["siniestro_id"],
                    defaults={"conciliacion_por_conciliador": path, "conciliacion_lograda": True}
                )
                broadcast_siniestro_update(self.session.metadata["siniestro_id"])
                self.session.metadata["pending_media"] = pending
                self.session.current_step = "DONE"
                if self.session.closed_at is None:
                    self.session.closed_at = timezone.now()
                response["text"] = "La conciliación por conciliador se ha registrado exitosamente. Proceso finalizado.\nTienes una hora para subir evidencias."
            else:
                response["text"] = "No se recibió el archivo. Sube la imagen o archivo del acuerdo."
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_NOMBRE":
            tercero = self.get_no_conciliacion_tercero()
            if user_text_lower != "omitir":
                tercero.nombre_completo = user_text.strip()
            else:
                tercero.nombre_completo = ""
            tercero.save(update_fields=["nombre_completo"])
            self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_CEDULA"
            response["text"] = "Ingresa el número de cédula del conductor."
            response["buttons"] = ["Omitir"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_CEDULA":
            tercero = self.get_no_conciliacion_tercero()
            ced = re.sub(r'[^0-9]', '', user_text)
            if user_text_lower != "omitir" and 6 <= len(ced) <= 10:
                tercero.cedula = ced
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_TELEFONO"
                response["text"] = "Ingresa el teléfono del conductor."
                response["buttons"] = ["Omitir"]
            elif user_text_lower == "omitir":
                tercero.cedula = ""
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_TELEFONO"
                response["text"] = "Ingresa el teléfono del conductor."
                response["buttons"] = ["Omitir"]
            else:
                response["text"] = "Cédula inválida. Ingresa una cédula correcta o 'omitir'."
            tercero.save(update_fields=["cedula"])
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_TELEFONO":
            tercero = self.get_no_conciliacion_tercero()
            if user_text_lower != "omitir":
                tercero.telefono = user_text.strip()
            else:
                tercero.telefono = ""
            tercero.save(update_fields=["telefono"])
            self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_DIRECCION"
            response["text"] = "Ingresa la dirección del conductor."
            response["buttons"] = ["Omitir"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_DIRECCION":
            tercero = self.get_no_conciliacion_tercero()
            if user_text_lower != "omitir":
                tercero.direccion = user_text.strip()
            else:
                tercero.direccion = ""
            tercero.save(update_fields=["direccion"])
            self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_EMAIL"
            response["text"] = "Ingresa el email del conductor."
            response["buttons"] = ["Omitir"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_EMAIL":
            tercero = self.get_no_conciliacion_tercero()
            if user_text_lower != "omitir":
                tercero.email = user_text.strip()
            else:
                tercero.email = ""
            tercero.save(update_fields=["email"])
            self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_LICENCIA"
            response["text"] = "Envía una foto de la licencia de conducción del conductor."
            response["buttons"] = ["Omitir"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_LICENCIA":
            tercero = self.get_no_conciliacion_tercero()
            pending = self.session.metadata.get("pending_media", [])
            if pending:
                media = pending.pop(0)
                path = media["url"]
                tercero.licencia_conduccion = path
                SiniestroMedia.objects.create(
                    siniestro_id=self.session.metadata["siniestro_id"],
                    file_url=path,
                    tipo=media["tipo"],
                    descripcion="Licencia de Conducción Tercero"
                )
                self.session.metadata["pending_media"] = pending
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_LICENCIA_TRANSITO"
                response["text"] = "Licencia de conducción recibida. Envía ahora una foto de la licencia de tránsito."
                response["buttons"] = ["Omitir"]
            elif user_text_lower == "omitir":
                tercero.licencia_conduccion = ""
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_LICENCIA_TRANSITO"
                response["text"] = "Licencia de conducción omitida. Envía ahora una foto de la licencia de tránsito."
                response["buttons"] = ["Omitir"]
            else:
                response["text"] = "No se recibió la imagen. Envía una foto de la licencia de conducción."
                response["buttons"] = ["Omitir"]
            tercero.save(update_fields=["licencia_conduccion"])
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_LICENCIA_TRANSITO":
            tercero = self.get_no_conciliacion_tercero()
            pending = self.session.metadata.get("pending_media", [])
            if pending:
                media = pending.pop(0)
                path = media["url"]
                tercero.licencia_transito = path
                SiniestroMedia.objects.create(
                    siniestro_id=self.session.metadata["siniestro_id"],
                    file_url=path,
                    tipo=media["tipo"],
                    descripcion="Licencia de Tránsito Tercero"
                )
                self.session.metadata["pending_media"] = pending
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_AUDIO"
                response["text"] = "Licencia de tránsito recibida. Envía ahora un audio con la versión del conductor."
                response["buttons"] = ["Omitir"]
            elif user_text_lower == "omitir":
                tercero.licencia_transito = ""
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_AUDIO"
                response["text"] = "Licencia de tránsito omitida. Envía ahora un audio con la versión del conductor."
                response["buttons"] = ["Omitir"]
            else:
                response["text"] = "No se recibió la imagen. Envía una foto de la licencia de tránsito."
                response["buttons"] = ["Omitir"]
            tercero.save(update_fields=["licencia_transito"])
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_AUDIO":
            tercero = self.get_no_conciliacion_tercero()
            pending = self.session.metadata.get("pending_media", [])
            if pending:
                media = pending.pop(0)
                path = media["url"]
                tercero.audio_version = path
                SiniestroMedia.objects.create(
                    siniestro_id=self.session.metadata["siniestro_id"],
                    file_url=path,
                    tipo=media["tipo"],
                    descripcion="Audio Versión Conductor Tercero"
                )
                self.session.metadata["pending_media"] = pending
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_FOTO_SEGURO"
                response["text"] = "Audio recibido. Envía ahora una foto del seguro del vehículo."
                response["buttons"] = ["Omitir"]
            elif user_text_lower == "omitir":
                tercero.audio_version = ""
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_FOTO_SEGURO"
                response["text"] = "Audio omitido. Envía ahora una foto del seguro del vehículo."
                response["buttons"] = ["Omitir"]
            else:
                response["text"] = "No se recibió el audio. Envía el audio con la versión del conductor."
                response["buttons"] = ["Omitir"]
            tercero.save(update_fields=["audio_version"])
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_CONDUCTOR_FOTO_SEGURO":
            tercero = self.get_no_conciliacion_tercero()
            pending = self.session.metadata.get("pending_media", [])
            if pending:
                media = pending.pop(0)
                path = media["url"]
                tercero.fotos_seguro = path
                SiniestroMedia.objects.create(
                    siniestro_id=self.session.metadata["siniestro_id"],
                    file_url=path,
                    tipo=media["tipo"],
                    descripcion="Foto Seguro Tercero"
                )
                self.session.metadata["pending_media"] = pending
                self.session.current_step = "NO_CONCILIACION_IS_CONDUCTOR_SAME_AS_PROPIETARIO"
                response["text"] = "Foto del seguro recibida. ¿El conductor es el mismo propietario del vehículo?"
                response["buttons"] = ["Sí", "No", "Omitir"]
            elif user_text_lower == "omitir":
                tercero.fotos_seguro = ""
                self.session.current_step = "NO_CONCILIACION_IS_CONDUCTOR_SAME_AS_PROPIETARIO"
                response["text"] = "Foto del seguro omitida. ¿El conductor es el mismo propietario del vehículo?"
                response["buttons"] = ["Sí", "No", "Omitir"]
            else:
                response["text"] = "No se recibió la imagen. Envía una foto del seguro."
                response["buttons"] = ["Omitir"]
            tercero.save(update_fields=["fotos_seguro"])
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_IS_CONDUCTOR_SAME_AS_PROPIETARIO":
            tercero = self.get_no_conciliacion_tercero()
            if user_response_says_yes(user_text):
                tercero.propietario = tercero.nombre_completo
                tercero.direccion_propietario = tercero.direccion
                tercero.correo_propietario = tercero.email
                tercero.save()
                self.session.current_step = "ASK_ANOTHER_TERCERO"
                response["text"] = "¿Hay otro tercero involucrado en el siniestro?"
                response["buttons"] = ["Sí", "No"]
            elif user_response_says_no(user_text):
                self.session.current_step = "NO_CONCILIACION_ASK_PROPIETARIO_NOMBRE"
                response["text"] = "Ingresa el nombre completo del propietario."
                response["buttons"] = ["Omitir"]
            elif user_text_lower == "omitir":
                self.session.current_step = "ASK_ANOTHER_TERCERO"
                response["text"] = "¿Hay otro tercero involucrado en el siniestro?"
                response["buttons"] = ["Sí", "No"]
            else:
                response["text"] = "No comprendí tu respuesta. ¿El conductor es el propietario?"
                response["buttons"] = ["Sí", "No", "Omitir"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_PROPIETARIO_NOMBRE":
            tercero = self.get_no_conciliacion_tercero()
            if user_text_lower != "omitir":
                tercero.propietario = user_text.strip()
            else:
                tercero.propietario = ""
            tercero.save(update_fields=["propietario"])
            self.session.current_step = "NO_CONCILIACION_ASK_PROPIETARIO_CEDULA"
            response["text"] = "Ingresa el número de cédula del propietario."
            response["buttons"] = ["Omitir"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIacion_ASK_PROPIETARIO_CEDULA":
            tercero = self.get_no_conciliacion_tercero()
            ced = re.sub(r'[^0-9]', '', user_text)
            if user_text_lower != "omitir" and 6 <= len(ced) <= 10:
                tercero.cedula_propietario = ced
                self.session.current_step = "NO_CONCILIACION_ASK_PROPIETARIO_DIRECCION"
                response["text"] = "Cédula del propietario recibida. Ingresa la dirección del propietario."
                response["buttons"] = ["Omitir"]
            elif user_text_lower == "omitir":
                tercero.cedula_propietario = ""
                self.session.current_step = "NO_CONCILIACION_ASK_PROPIETARIO_DIRECCION"
                response["text"] = "Cédula del propietario omitida. Ingresa la dirección del propietario."
                response["buttons"] = ["Omitir"]
            else:
                response["text"] = "Cédula inválida. Ingresa una cédula correcta para el propietario o 'omitir'."
            tercero.save(update_fields=["cedula_propietario"])
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_PROPIETARIO_DIRECCION":
            tercero = self.get_no_conciliacion_tercero()
            if user_text_lower != "omitir":
                tercero.direccion_propietario = user_text.strip()
            else:
                tercero.direccion_propietario = ""
            tercero.save(update_fields=["direccion_propietario"])
            self.session.current_step = "NO_CONCILIACION_ASK_PROPIETARIO_EMAIL"
            response["text"] = "Ingresa el correo electrónico del propietario."
            response["buttons"] = ["Omitir"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "NO_CONCILIACION_ASK_PROPIETARIO_EMAIL":
            tercero = self.get_no_conciliacion_tercero()
            if user_text_lower != "omitir":
                tercero.correo_propietario = user_text.strip()
            else:
                tercero.correo_propietario = ""
            tercero.save(update_fields=["correo_propietario"])
            self.session.current_step = "ASK_ANOTHER_TERCERO"
            response["text"] = "¿Hay otro tercero involucrado en el siniestro?"
            response["buttons"] = ["Sí", "No"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "ASK_ANOTHER_TERCERO":
            if user_response_says_yes(user_text):
                self.session.metadata["current_tercero_id"] = None
                self.session.current_step = "NO_CONCILIACION_ASK_CONDUCTOR_NOMBRE"
                response["text"] = "Ingresa el nombre completo del siguiente conductor del otro vehículo."
                response["buttons"] = ["Omitir"]
            elif user_response_says_no(user_text):
                self.session.current_step = "DONE"
                if self.session.closed_at is None:
                    self.session.closed_at = timezone.now()
                response["text"] = "Hemos finalizado el proceso de registro de terceros. ¡Gracias!.\nTienes una hora para subir evidencias."
            else:
                response["text"] = "No comprendí tu respuesta. ¿Hay otro tercero?"
                response["buttons"] = ["Sí", "No"]
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.save()
        elif step == "ASK_TERCERO_NOMBRE":
            defaults = {}
            if user_text_lower != "omitir":
                defaults["nombre_completo_conductor2"] = truncate_if_needed(user_text.strip(), 250)
            else:
                defaults["nombre_completo_conductor2"] = ""
            ActaConciliacion.objects.update_or_create(siniestro_id=self.session.metadata["siniestro_id"], defaults=defaults)
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.current_step = "ASK_TERCERO_CEDULA"
            response["text"] = "Por favor, ingresa la cédula del tercero."
            response["buttons"] = ["Omitir"]
            self.session.save()
        elif step == "ASK_TERCERO_CEDULA":
            ced = re.sub(r'[^0-9]', '', user_text)
            defaults = {}
            if user_text_lower != "omitir" and ced:
                defaults["cedula_conductor2"] = truncate_if_needed(ced, 15)
            else:
                defaults["cedula_conductor2"] = ""
            ActaConciliacion.objects.update_or_create(siniestro_id=self.session.metadata["siniestro_id"], defaults=defaults)
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.current_step = "ASK_TERCERO_PLACA"
            response["text"] = "Por favor, ingresa la placa del vehículo del tercero."
            response["buttons"] = ["Omitir"]
            self.session.save()
        elif step == "ASK_TERCERO_PLACA":
            placa_t = normalize_plate(user_text)
            defaults = {}
            if user_text_lower != "omitir" and placa_t:
                defaults["placa_conductor2"] = truncate_if_needed(placa_t, 7)
            else:
                defaults["placa_conductor2"] = ""
            ActaConciliacion.objects.update_or_create(siniestro_id=self.session.metadata["siniestro_id"], defaults=defaults)
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.current_step = "ASK_TERCERO_TELEFONO"
            response["text"] = "Ingresa el número de teléfono del tercero."
            response["buttons"] = ["Omitir"]
            self.session.save()
        elif step == "ASK_TERCERO_TELEFONO":
            defaults = {}
            if user_text_lower != "omitir":
                defaults["telefono_conductor2"] = truncate_if_needed(user_text.strip(), 15)
            else:
                defaults["telefono_conductor2"] = ""
            ActaConciliacion.objects.update_or_create(siniestro_id=self.session.metadata["siniestro_id"], defaults=defaults)
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.current_step = "ASK_TERCERO_EMAIL"
            response["text"] = "Ingresa el email del tercero."
            response["buttons"] = ["Omitir"]
            self.session.save()
        elif step == "ASK_TERCERO_EMAIL":
            defaults = {}
            if user_text_lower != "omitir":
                defaults["email_conductor2"] = truncate_if_needed(user_text.strip(), 50)
            else:
                defaults["email_conductor2"] = ""
            ActaConciliacion.objects.update_or_create(siniestro_id=self.session.metadata["siniestro_id"], defaults=defaults)
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            self.session.current_step = "ASK_CONDUCTOR2_SUMAPAGAR"
            response["text"] = "Ingresa la suma a pagar acordada."
            response["buttons"] = ["Omitir"]
            self.session.save()
        elif step == "ASK_CONDUCTOR2_SUMAPAGAR":
            defaults = {}
            if user_text_lower != "omitir":
                defaults["suma_a_pagar"] = truncate_if_needed(user_text.strip(), 15)
            else:
                defaults["suma_a_pagar"] = ""
            ActaConciliacion.objects.update_or_create(siniestro_id=self.session.metadata["siniestro_id"], defaults=defaults)
            broadcast_siniestro_update(self.session.metadata["siniestro_id"])
            url_firma = f"{settings.FRONTEND_URL}/sinister/conciliacion?placa={self.session.metadata['placa']}&siniestroId={self.session.metadata['siniestro_id']}"
            response["text"] = f"Datos guardados.\nIngresa al siguiente enlace para firmar la conciliación: {url_firma}\nTienes una hora para subir evidencias."
            self.session.current_step = "DONE"
            if self.session.closed_at is None:
                self.session.closed_at = timezone.now()
            self.session.save()
        else:
            response["text"] = "Hemos finalizado el proceso. ¡Gracias!"
            self.session.current_step = "DONE"
            if self.session.closed_at is None:
                self.session.closed_at = timezone.now()
            self.session.save()

        return response

class ConsultarPolizaFlowComponent:
    def __init__(self, session):
        self.session = session

    def handle(self, user_text: str):
        driver = get_driver_by_phone(self.session.user_phone)
        if not driver or not driver.vehiculo:
            self.session.current_step = "DONE"
            if self.session.closed_at is None:
                self.session.closed_at = timezone.now()
            self.session.save()
            return {"text": "No se encontró vehículo asociado a tu número de teléfono."}

        vehiculo = driver.vehiculo
        soats = Soat.objects.filter(vehiculo=vehiculo, estado=True).order_by('-id')
        revs = RevisionTecnomecanica.objects.filter(vehiculo=vehiculo, estado=True).order_by('-id')
        if not soats and not revs:
            self.session.current_step = "DONE"
            if self.session.closed_at is None:
                self.session.closed_at = timezone.now()
            self.session.save()
            return {"text": "No se encontró SOAT ni Revisión Tecnomecánica para tu vehículo."}

        response_text = ""
        if soats:
            soat = soats.first()
            response_text += (
                f"SOAT: {soat.numero_poliza} - Expedición: {soat.fecha_expedicion.strftime('%Y-%m-%d')} - "
                f"Vence: {soat.vigencia_hasta.strftime('%Y-%m-%d')}\nDescarga PDF: {soat.soporte}\n\n"
            )
        if revs:
            rev = revs.first()
            response_text += (
                f"Tecnomecánica Cert: {rev.no_certificado} - Vence: {rev.fecha_vencimiento.strftime('%Y-%m-%d')}\n"
                f"Descarga PDF: {rev.soporte}\n"
            )

        self.session.current_step = "DONE"
        if self.session.closed_at is None:
            self.session.closed_at = timezone.now()
        self.session.save()
        return {"text": response_text.strip()}