# # myapp/view_rf_for.py
# from .models import Colaboradores, RegistroAsistencia, Agenda
# from .serializers import ColaboradoresSlr
# from datetime import datetime, timedelta
# from django.http import JsonResponse
# from django.utils import timezone
# import face_recognition
# import tempfile
# import json
# import cv2
# import os

# def is_image_valid(image_path):
#     image = cv2.imread(image_path)
#     if image is None or image.size < 1000:
#         return False
#     return True

# def detect_face_features(image_path):
#     image = face_recognition.load_image_file(image_path)
#     face_locations = face_recognition.face_locations(image)
#     return len(face_locations) > 0

# def reconocimiento_facial(request):
#     from deepface import DeepFace
#     if request.method == 'POST':
#         image_data = request.FILES.get('imageData')
#         document_number = request.POST.get('documentNumber')

#         if not image_data:
#             return JsonResponse({'message': 'No se recibió ninguna imagen'}, status=400)

#         with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
#             for chunk in image_data.chunks():
#                 temp_file.write(chunk)
#             temp_file_path = temp_file.name

#         try:
#             if not is_image_valid(temp_file_path):
#                 return JsonResponse({'message': 'La imagen no es válida'}, status=400)

#             if not detect_face_features(temp_file_path):
#                 return JsonResponse({'message': 'No se detectaron características faciales suficientes'}, status=400)

#             recognized_user = None
#             face_ids = request.POST.get('faceIds')
#             reference_images_list = json.loads(face_ids) if face_ids else []

#             if document_number:
#                 try:
#                     colaborador = Colaboradores.objects.get(num_documento=document_number)
#                     if colaborador.face_ids:
#                         if isinstance(colaborador.face_ids, str):
#                             reference_images_list = json.loads(colaborador.face_ids)
#                         else:
#                             reference_images_list = colaborador.face_ids
#                     else:
#                         reference_images_list = []
#                 except Colaboradores.DoesNotExist:
#                     return JsonResponse({'message': 'Colaborador no encontrado'}, status=404)

#             current_folder = os.path.dirname(os.path.realpath(__file__))
#             parent_folder = os.path.abspath(os.path.join(current_folder, '..', 'media'))

#             for image_name in reference_images_list:
#                 reference_image_path = os.path.join(parent_folder, image_name)
#                 if not os.path.isfile(reference_image_path):
#                     continue
#                 if recognized_user:
#                     break
#                 try:
#                     result = DeepFace.verify(temp_file_path, reference_image_path, model_name='VGG-Face')
#                     print('Reconocido? ', result['verified'])
#                     if result['verified']:
#                         recognized_user = colaborador.num_documento if document_number else "Desconocido"
#                         break
#                 except Exception as e:
#                     print(f"Error comparando imágenes: {e}")

#             if recognized_user:
#                 if os.path.exists(temp_file_path):
#                     os.remove(temp_file_path)
#                 return JsonResponse({
#                     'user_id': recognized_user,
#                     'colaborador': ColaboradoresSlr(colaborador).data if document_number else {},
#                     'message': f'Usuario reconocido: {recognized_user}'
#                 }, status=200)
#             else:
#                 return JsonResponse({'message': 'No se encontró ningún usuario reconocido'}, status=400)

#         finally:
#             if os.path.exists(temp_file_path):
#                 os.remove(temp_file_path)

#     return JsonResponse({'message': 'Método no permitido'}, status=405)


# def time_record(request):
#     if request.method == 'POST':
#         image_data = request.FILES.get('imageData')
#         document_number = request.POST.get('documentNumber', '')
#         face_ids_json = request.POST.get('faceIds', '[]')

#         if not image_data and not document_number:
#             return JsonResponse({'message': 'No se recibió ningún dato de registro'}, status=400)

#         with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
#             if image_data:
#                 for chunk in image_data.chunks():
#                     temp_file.write(chunk)
#                 temp_file_path = temp_file.name
#             else:
#                 temp_file_path = None

#         try:
#             recognized_user = None
#             colaborador = None

#             current_folder = os.path.dirname(os.path.realpath(__file__))
#             parent_folder = os.path.abspath(os.path.join(current_folder, '..', 'media'))

#             if image_data:
#                 if not is_image_valid(temp_file_path):
#                     return JsonResponse({'message': 'La imagen no es válida'}, status=400)

#                 if not detect_face_features(temp_file_path):
#                     return JsonResponse({'message': 'No se detectaron características faciales suficientes'}, status=400)

#                 try:
#                     if document_number:
#                         colaborador = Colaboradores.objects.get(num_documento=document_number)
#                         reference_images_list = json.loads(face_ids_json) if face_ids_json else colaborador.face_ids[:2]
#                     else:
#                         colaboradores = Colaboradores.objects.exclude(face_ids__isnull=True).exclude(face_ids=[])
#                         for colab in colaboradores:
#                             reference_images_list = colab.face_ids[:2]
#                             for image_name in reference_images_list:
#                                 reference_image_path = os.path.join(parent_folder, image_name)
#                                 if not os.path.isfile(reference_image_path):
#                                     continue
#                                 try:
#                                     result = DeepFace.verify(temp_file_path, reference_image_path, model_name='VGG-Face')
#                                     if result['verified']:
#                                         recognized_user = colab.num_documento
#                                         colaborador = colab
#                                         break
#                                 except Exception as e:
#                                     print(f"Error comparando imágenes: {e}")
#                             if recognized_user:
#                                 break
#                 except Colaboradores.DoesNotExist:
#                     return JsonResponse({'message': 'Colaborador no encontrado'}, status=404)

#                 if not recognized_user and document_number:
#                     try:
#                         colaborador = Colaboradores.objects.get(num_documento=document_number)
#                         reference_images_list = colaborador.face_ids[:2]
#                         for image_name in reference_images_list:
#                             reference_image_path = os.path.join(parent_folder, image_name)
#                             if not os.path.isfile(reference_image_path):
#                                 continue
#                             try:
#                                 result = DeepFace.verify(temp_file_path, reference_image_path, model_name='VGG-Face')
#                                 if result['verified']:
#                                     recognized_user = colaborador.num_documento
#                                     break
#                             except Exception as e:
#                                 print(f"Error comparando imágenes: {e}")
#                     except Colaboradores.DoesNotExist:
#                         return JsonResponse({'message': 'Colaborador no encontrado'}, status=404)

#             elif document_number:
#                 try:
#                     colaborador = Colaboradores.objects.get(num_documento=document_number)
#                     recognized_user = colaborador.num_documento
#                 except Colaboradores.DoesNotExist:
#                     return JsonResponse({'message': 'Colaborador no encontrado'}, status=404)

#             if recognized_user and colaborador:
#                 tipo_registro, is_late, left_early = determine_tipo_registro(colaborador)
#                 print('Tipo registro: ', tipo_registro, ' - is late: ', is_late, ' - left early: ', left_early)
#                 # Crear el registro de asistencia con los nuevos campos
#                 RegistroAsistencia.objects.create(
#                     colaborador=colaborador,
#                     tipo=tipo_registro,
#                     is_late=is_late,
#                     left_early=left_early
#                 )

#                 # Obtener los últimos 5 días de registros
#                 five_days_ago = timezone.now() - timedelta(days=5)
#                 registros = RegistroAsistencia.objects.filter(
#                     colaborador=colaborador,
#                     timestamp__gte=five_days_ago
#                 ).order_by('-timestamp')

#                 # Agrupar registros por día
#                 registros_por_dia = {}
#                 for registro in registros:
#                     fecha = registro.timestamp.date()
#                     if fecha not in registros_por_dia:
#                         registros_por_dia[fecha] = {'entrada': None, 'salida': None}
#                     registros_por_dia[fecha][registro.tipo] = registro.timestamp.time()

#                 # Formatear los datos para los últimos 5 días
#                 last_five_days_records = []
#                 for fecha in sorted(registros_por_dia.keys(), reverse=True)[:5]:
#                     last_five_days_records.append({
#                         'date': fecha.strftime('%Y-%m-%d'),
#                         'entrada_time': registros_por_dia[fecha]['entrada'],
#                         'salida_time': registros_por_dia[fecha]['salida'],
#                     })

#                 # Contar las veces que llegó tarde en el último mes
#                 one_month_ago = timezone.now() - timedelta(days=30)
#                 late_count = RegistroAsistencia.objects.filter(
#                     colaborador=colaborador,
#                     tipo='entrada',
#                     is_late=True,
#                     timestamp__gte=one_month_ago
#                 ).count()

#                 response_data = {
#                     'user_id': recognized_user,
#                     'colaborador': ColaboradoresSlr(colaborador).data,
#                     'tipoRegistro': tipo_registro,
#                     'isLate': is_late,
#                     'leftEarly': left_early,
#                     'message': f'Usuario reconocido: {recognized_user}',
#                     'lastFiveDaysRecords': last_five_days_records,
#                     'lateCountLastMonth': late_count
#                 }

#                 return JsonResponse(response_data, status=200)
#             else:
#                 return JsonResponse({'message': 'No se encontró ningún usuario reconocido'}, status=400)

#         finally:
#             if temp_file_path and os.path.exists(temp_file_path):
#                 os.remove(temp_file_path)

#     return JsonResponse({'message': 'Método no permitido'}, status=405)


# def determine_tipo_registro(colaborador):
#     now = datetime.now()
#     today = now.date()
#     current_time = now.time()

#     try:
#         agenda = Agenda.objects.get(
#             agenda_colaborador_id=colaborador,
#             agenda_start_date=today,
#             agenda_end_date=today,
#             agenda_type='work'
#         )
#     except Agenda.DoesNotExist:
#         return 'entrada', False, False

#     last_registro = RegistroAsistencia.objects.filter(colaborador=colaborador).order_by('-timestamp').first()

#     if last_registro:
#         if last_registro.tipo == 'entrada':
#             tipo_registro = 'salida'
#         else:
#             tipo_registro = 'entrada'
#     else:
#         tipo_registro = 'entrada'

#     is_late = False
#     left_early = False

#     if tipo_registro == 'entrada':
#         if current_time > datetime.combine(today, agenda.agenda_start_time):
#             is_late = True
#     else:
#         if current_time < datetime.combine(today, agenda.agenda_end_time):
#             left_early = True

#     return tipo_registro, is_late, left_early



import os
import re
import cv2
import threading
import matplotlib
import numpy as np
matplotlib.use('Agg')
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from paddleocr import PaddleOCR
import matplotlib.pyplot as plt
from django.conf import settings
from rest_framework import status
import matplotlib.patches as patches
from pdf2image import convert_from_path
from tempfile import TemporaryDirectory
from rest_framework.views import APIView
from django.http import HttpResponseRedirect
from rest_framework.response import Response
from django.core.files.base import ContentFile
from rest_framework.permissions import AllowAny
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser, FormParser

TARGET_WIDTH_LICENSE = 5100
TARGET_HEIGHT_LICENSE = 6600
TARGET_WIDTH_POLICY = 2480
TARGET_HEIGHT_POLICY = 3508

ROIS = {
    'soat': {
        'bolivar': { "fecha_expedicion": (610, 1150, 1060, 1250), "vigencia_desde": (1280, 1150, 1690, 1250), "vigencia_hasta": (1950, 1150, 2360, 1250), "numero_poliza": (450, 1740, 1020, 1862), "placa": (1090, 1740, 1458, 1862) },
        'aseguradora': { "fecha_expedicion": (410, 1010, 950, 1130), "vigencia_desde": (1110, 1010, 1620, 1130), "vigencia_hasta": (1850, 1010, 2370, 1130), "numero_poliza": (300, 1630, 910, 1810), "placa": (980, 1640, 1480, 1800) },
        'mundial': { "fecha_expedicion": (410, 1010, 950, 1130), "vigencia_desde": (1110, 1010, 1620, 1130), "vigencia_hasta": (1850, 1010, 2370, 1130), "numero_poliza": (300, 1630, 910, 1810), "placa": (980, 1640, 1480, 1800) },
        'estado': { "fecha_expedicion": (410, 1050, 950, 1180), "vigencia_desde": (1150, 1050, 1620, 1180), "vigencia_hasta": (1890, 1050, 2370, 1180), "numero_poliza": (280, 1630, 910, 1810), "placa": (1160, 1640, 1530, 1800) },
        'unknown': { "fecha_expedicion": (610, 1150, 1060, 1250), "vigencia_desde": (1280, 1150, 1690, 1250), "vigencia_hasta": (1950, 1150, 2360, 1250), "numero_poliza": (450, 1740, 1020, 1862), "placa": (1090, 1740, 1458, 1862) }
    },
    'tecno': {
        'unknown': { "entidad_expide_certificado": (1920, 2600, 4490, 2750), "nit": (1300, 2870, 2200, 2999), "fecha_expedicion": (1360, 3080, 2250, 3270), "no_certificado": (2100, 2000, 3000, 2150), "fecha_vencimiento": (3350, 3100, 4400, 3250), "placa": (1100, 3730, 2300, 3870) }
    },
    'operacion': {
        'unknown': { "no_certificado": (2200, 1570, 3000, 1750), "placa": (1530, 2100, 2300, 2250), "nit": (1530, 4270, 2300, 4430), "fecha_expedicion": (1530, 4800, 2300, 4950), "vigencia_desde": (2000, 5000, 2600, 5150), "fecha_vencimiento": (3100, 5000, 3650, 5150) }
    }
}

INSURER_KEYWORDS = {
    'bolivar': ['BOLIVAR'],
    'estado': ['ESTADO S.A.'],
    'mundial': ['MUNDIAL', 'ASEGURADORA'],
}

POLICY_TYPE_KEYWORDS = {
    'contractual': ['RESPONSABILIDAD CIVIL CONTRACTUAL'],
    'extracontractual': ['RESPONSABILIDAD CIVIL EXTRACONTRACTUAL'],
}

LICENSE_TECNO_KEYWORDS = ['CERTIFICADO DE REVISION TÉCNICO MECANICA', 'TECNO MECANICA', 'TÉCNICO MECANICA', 'DATOS CENTRO DIAGNOSTICO', 'CERTIFICADO DE REVISION TECNICO MECANICA Y DE EMISIONES CONTAMINANTES', 'TECNICO MECANICA']
LICENSE_SOAT_KEYWORDS = ['SOAT', 'PRIMA SOAT', 'ASEGuRADORY']
LICENSE_OPERACION_KEYWORDS = ['TARJETA DE OPERACIóN', 'TARJETA DE']

try:
    ocr_instance = PaddleOCR(
        use_angle_cls=True,
        lang='es',
        det_db_box_thresh=0.5,
        use_gpu=True,
        det_model_dir='./paddleocr_models/det_lite',
        rec_model_dir='./paddleocr_models/rec_lite',
        show_log=False
    )
except Exception:
    ocr_instance = PaddleOCR(
        use_angle_cls=True,
        lang='es',
        det_db_box_thresh=0.5,
        use_gpu=False,
        det_model_dir='./paddleocr_models/det_lite',
        rec_model_dir='./paddleocr_models/rec_lite',
        show_log=False
    )

ocr_lock = threading.Lock()

def resize_image(image, width, height):
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

def preprocess_license_image(image):
    if image is None:
        raise ValueError("La imagen de entrada es None.")
    resized = resize_image(image, TARGET_WIDTH_LICENSE, TARGET_HEIGHT_LICENSE)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

def preprocess_policy_image(image):
    if image is None:
        raise ValueError("La imagen de entrada es None.")
    resized = resize_image(image, TARGET_WIDTH_POLICY, TARGET_HEIGHT_POLICY)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

def preprocess_tecno_image(image):
    resized = resize_image(image, TARGET_WIDTH_LICENSE, TARGET_HEIGHT_LICENSE)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 140, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

def detect_insurer(extracted_text):
    print(extracted_text)
    text_upper = extracted_text.upper()
    for insurer, keywords in INSURER_KEYWORDS.items():
        for keyword in keywords:
            if keyword.upper() in text_upper:
                return insurer
    return 'unknown'

def detect_policy_type_from_text_internal(extracted_text):
    text_upper = extracted_text.upper()
    for policy_type, keywords_list in POLICY_TYPE_KEYWORDS.items():
        for keyword in keywords_list:
            if keyword.upper() in text_upper:
                if "SERVICIO PUBLICO PASAJEROS" in text_upper:
                    return policy_type
                else:
                    return policy_type
    return 'desconocido'

def combined_detect_document_type(extracted_text):
    text_upper = extracted_text.upper()
    policy_specific = detect_policy_type_from_text_internal(extracted_text)
    if policy_specific != 'desconocido':
        return policy_specific, 'unknown'
    if any(k.upper() in text_upper for k in LICENSE_TECNO_KEYWORDS):
        return 'tecno', 'unknown'
    if any(k.upper() in text_upper for k in LICENSE_SOAT_KEYWORDS) or ('SOAT' in text_upper and any(ins_kw.upper() in text_upper for ins_kw_list in INSURER_KEYWORDS.values() for ins_kw in ins_kw_list)):
        return 'soat', detect_insurer(extracted_text)
    if any(k.upper() in text_upper for k in LICENSE_OPERACION_KEYWORDS):
        return 'operacion', 'unknown'
    return 'desconocido', 'unknown'

def is_box_center_in_roi(box_coords, roi_coords):
    x0, y0, x1, y1 = roi_coords
    cx = sum(p[0] for p in box_coords) / 4
    cy = sum(p[1] for p in box_coords) / 4
    return x0 <= cx <= x1 and y0 <= cy <= y1

def collect_raw_ocr_lines_by_roi(full_ocr_result, rois_map):
    raw_map = {field: [] for field in rois_map}
    if full_ocr_result and full_ocr_result[0]:
        for line_info in full_ocr_result[0]:
            box_coords, txt = line_info[0], line_info[1][0]
            for field, roi in rois_map.items():
                if is_box_center_in_roi(box_coords, roi):
                    raw_map[field].append(txt)
    return raw_map

def visualize_rois_on_image(image_array, rois_map, output_path):
    rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    fig, ax = plt.subplots(figsize=(12, 16))
    ax.imshow(rgb)
    for field, (x0, y0, x1, y1) in rois_map.items():
        rect = patches.Rectangle((x0, y0), x1 - x0, y1 - y0, linewidth=3, edgecolor='red', facecolor='none')
        ax.add_patch(rect)
        ax.text(x0, y0 - 15, field, color='red', fontsize=14, weight='bold')
    plt.axis('off')
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

class UploadLicenseView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        if 'files' not in request.FILES:
            return Response({"error": "No se encontraron archivos en la solicitud."}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist('files')
        password = request.data.get('password', None)

        file_obj = files[0]
        original_name = file_obj.name
        try:
            base = "".join(c if c.isalnum() else '_' for c in os.path.splitext(original_name)[0])
            ext = os.path.splitext(original_name)[1].lower()
            unique_name = f"{base}_0{ext}"
            saved_path = default_storage.save(os.path.join('licenses', unique_name), file_obj)
            full_path = default_storage.path(saved_path)

            if ext == '.pdf':
                kwargs = {'dpi': 600, 'fmt': 'png', 'thread_count': 4}
                if password:
                    kwargs['userpw'] = password
                pages = convert_from_path(full_path, first_page=1, last_page=1, **kwargs)
                if not pages:
                    raise ValueError("El PDF no contiene páginas o la conversión falló.")
                pil_img = pages[0]
                img_src = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            elif ext in ['.jpg', '.jpeg', '.png']:
                img_src = cv2.imread(full_path)
                if img_src is None:
                    raise ValueError(f"No se pudo leer la imagen: {full_path}")
            else:
                return Response({"error": "Formato no soportado."}, status=status.HTTP_400_BAD_REQUEST)

            img_tmp_for_ocr = preprocess_license_image(img_src.copy())
            with ocr_lock:
                ocr_results_tmp = ocr_instance.ocr(np.ascontiguousarray(img_tmp_for_ocr), cls=True)
            lines_tmp = []
            if ocr_results_tmp and ocr_results_tmp[0]:
                for ln in ocr_results_tmp[0]:
                    if len(ln) >= 2 and isinstance(ln[1], (tuple, list)):
                        lines_tmp.append(ln[1][0])
            full_text_tmp = "\n".join(lines_tmp)
            doc_type, insurer = combined_detect_document_type(full_text_tmp)

            if doc_type not in ['soat', 'tecno', 'operacion', 'contractual', 'extracontractual']:
                return Response({"error": "Tipo de documento no reconocido."}, status=status.HTTP_400_BAD_REQUEST)

            if doc_type == 'soat':
                rois_map = ROIS['soat'].get(insurer, ROIS['soat']['unknown'])
                to_visualize = preprocess_license_image(img_src.copy())
                with ocr_lock:
                    ocr_results = ocr_instance.ocr(np.ascontiguousarray(to_visualize), cls=True)
                raw_ocr_map = collect_raw_ocr_lines_by_roi(ocr_results, rois_map)
                print(f"Texto OCR bruto por ROI (soat, {insurer}): {raw_ocr_map}")
            elif doc_type == 'operacion':
                rois_map = ROIS['operacion']['unknown']
                to_visualize = preprocess_license_image(img_src.copy())
                with ocr_lock:
                    ocr_results = ocr_instance.ocr(np.ascontiguousarray(to_visualize), cls=True)
                raw_ocr_map = collect_raw_ocr_lines_by_roi(ocr_results, rois_map)
                print(f"Texto OCR bruto por ROI (operacion): {raw_ocr_map}")
            elif doc_type == 'tecno':
                rois_map = ROIS['tecno']['unknown']
                to_visualize = preprocess_tecno_image(img_src.copy())
                with ocr_lock:
                    ocr_results = ocr_instance.ocr(np.ascontiguousarray(to_visualize), cls=True)
                raw_ocr_map = collect_raw_ocr_lines_by_roi(ocr_results, rois_map)
                print(f"Texto OCR bruto por ROI (tecno): {raw_ocr_map}")
            else:
                # contractual / extracontractual
                img_for_policy = preprocess_policy_image(img_src.copy())
                with ocr_lock:
                    policy_results = ocr_instance.ocr(np.ascontiguousarray(img_for_policy), cls=True)
                policy_lines = []
                if policy_results and policy_results[0]:
                    for ln in policy_results[0]:
                        print(ln)
                        if len(ln) >= 2 and isinstance(ln[1], (tuple, list)):
                            policy_lines.append(ln[1][0])
                # extraer número de póliza
                policy_number = None
                for line in policy_lines:
                    m = re.search(r'\b[A-Z]{2}\d{6}\b', line)
                    if m:
                        policy_number = m.group()
                        break
                raw_ocr_map = {"numero_poliza": [policy_number] if policy_number else []}
                print(f"Texto OCR bruto completo póliza: {policy_lines}")
                print(f"Número de póliza extraído: {policy_number}")
                rois_map = {}
                to_visualize = img_for_policy.copy()

            with TemporaryDirectory() as tmpdir:
                vis_name = f"{base}_rois.png"
                vis_tmp = os.path.join(tmpdir, vis_name)
                visualize_rois_on_image(to_visualize, rois_map, vis_tmp)
                with open(vis_tmp, 'rb') as fvis:
                    vis_bytes = fvis.read()
                content = ContentFile(vis_bytes)
                storage_path = default_storage.save(os.path.join('licenses', 'visualizations', vis_name), content)

            rel = storage_path
            if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT and settings.MEDIA_ROOT in storage_path:
                rel = os.path.relpath(storage_path, settings.MEDIA_ROOT)
            vis_url = request.build_absolute_uri(settings.MEDIA_URL + rel.replace("\\", "/"))
            return HttpResponseRedirect(vis_url)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
