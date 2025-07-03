import re
import os
import cv2
import matplotlib
matplotlib.use('Agg')
from paddleocr import PaddleOCR
import matplotlib.pyplot as plt
from rest_framework import status
import matplotlib.patches as patches
from tempfile import TemporaryDirectory
from pdf2image import convert_from_path
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.conf import settings

POPPLER_PATH = r"C:\poppler\bin"

ocr = PaddleOCR(
    use_angle_cls=True, 
    lang='es',
    det_db_box_thresh=0.5,
)

ROIS = {
    'soat': {
        'bolivar': {
            "fecha_expedicion": (610, 1150, 1060, 1250),
            "vigencia_desde": (1280, 1150, 1690, 1250),
            "vigencia_hasta": (1950, 1150, 2360, 1250),
            "numero_poliza": (450, 1740, 1020, 1862),
            "placa": (1090, 1740, 1458, 1862),
            "clase": (1585, 1740, 2400, 1862),
            "tipo_servicio": (2490, 1740, 3350, 1862),
            "cilindraje": (3500, 1737, 3911, 1859),
            "modelo": (4080, 1737, 4482, 1859),
            "pasajeros": (450, 2020, 650, 2150),
            "marca": (980, 1960, 2400, 2080),
            "linea": (973, 2096, 2400, 2208),
            "carroceria": (3285, 2020, 4300, 2150),
            "numero_motor": (450, 2320, 1400, 2460),
            "chasis": (1685, 2330, 2800, 2450),
            "vin": (2980, 2330, 4000, 2450),
            "nombres_apellidos_tomador": (450, 2620, 2090, 2760),
            "telefono_tomador": (2200, 2640, 2760, 2760),
            "tipo_documento_tomador": (2830, 2640, 3200, 2760),
            "numero_documento_tomador": (3430, 2640, 4000, 2760),
            "ciudad_residencia_tomador": (4060, 2640, 4600, 2760),
            "total_a_pagar": (500, 3530, 1200, 3650),
        },
        'aseguradora': {
            "fecha_expedicion": (410, 1010, 950, 1130),
            "vigencia_desde": (1110, 1010, 1620, 1130),
            "vigencia_hasta": (1850, 1010, 2370, 1130),

            "numero_poliza": (300, 1630, 910, 1810),
            "placa": (980, 1640, 1480, 1800),
            "clase": (1510, 1640, 2410, 1800),
            "tipo_servicio": (2480, 1640, 3360, 1800),
            "cilindraje": (3560, 1640, 3920, 1800),
            "modelo": (4180, 1640, 4490, 1800),

            "pasajeros": (300, 1950, 530, 2090),
            "marca": (850, 1850, 2310, 2000),
            "linea": (850, 2010, 2360, 2140),
            "carroceria": (3310, 1960, 4310, 2100),

            "numero_motor": (300, 2270, 1380, 2440),
            "chasis": (1610, 2270, 2810, 2440),
            "vin": (2990, 2270, 4010, 2440),

            "nombres_apellidos_tomador": (300, 2610, 2100, 2770),
            "telefono_tomador": (2150, 2610, 2770, 2770),
            "tipo_documento_tomador": (2820, 2610, 3210, 2750),
            "numero_documento_tomador": (3470, 2610, 4010, 2750),
            "ciudad_residencia_tomador": (4150, 2610, 4610, 2770),

            "total_a_pagar": (310, 3590, 1170, 3800),
        },
        'mundial': {
            "fecha_expedicion": (410, 1010, 950, 1130),
            "vigencia_desde": (1110, 1010, 1620, 1130),
            "vigencia_hasta": (1850, 1010, 2370, 1130),

            "numero_poliza": (300, 1630, 910, 1810),
            "placa": (980, 1640, 1480, 1800),
            "clase": (1510, 1640, 2410, 1800),
            "tipo_servicio": (2480, 1640, 3360, 1800),
            "cilindraje": (3560, 1640, 3920, 1800),
            "modelo": (4180, 1640, 4490, 1800),

            "pasajeros": (300, 1950, 530, 2090),
            "marca": (850, 1850, 2310, 2000),
            "linea": (850, 2010, 2360, 2140),
            "carroceria": (3310, 1960, 4310, 2100),

            "numero_motor": (300, 2270, 1380, 2440),
            "chasis": (1610, 2270, 2810, 2440),
            "vin": (2990, 2270, 4010, 2440),

            "nombres_apellidos_tomador": (300, 2610, 2100, 2770),
            "telefono_tomador": (2150, 2610, 2770, 2770),
            "tipo_documento_tomador": (2820, 2610, 3210, 2750),
            "numero_documento_tomador": (3470, 2610, 4010, 2750),
            "ciudad_residencia_tomador": (4150, 2610, 4610, 2770),

            "total_a_pagar": (310, 3590, 1170, 3800),
        },
        'estado': {
            "fecha_expedicion": (410, 1050, 950, 1180),
            "vigencia_desde": (1150, 1050, 1620, 1180),
            "vigencia_hasta": (1890, 1050, 2370, 1180),

            "numero_poliza": (280, 1630, 910, 1810),
            "placa": (1160, 1640, 1530, 1800),
            "clase": (1730, 1640, 2500, 1800),
            "tipo_servicio": (2730, 1640, 3360, 1800),
            "cilindraje": (3950, 1640, 4300, 1800),
            "modelo": (4450, 1640, 4700, 1800),

            "pasajeros": (280, 1950, 530, 2090),
            "marca": (830, 1850, 2310, 1980),
            "linea": (830, 1990, 2360, 2110),
            "carroceria": (3360, 1960, 4310, 2100),

            "numero_motor": (280, 2240, 1380, 2400),
            "chasis": (1600, 2240, 2810, 2400),
            "vin": (3050, 2240, 4010, 2400),

            "nombres_apellidos_tomador": (270, 2540, 2100, 2700),
            "telefono_tomador": (2130, 2540, 2770, 2700),
            "tipo_documento_tomador": (2840, 2540, 3210, 2700),
            "numero_documento_tomador": (3500, 2540, 4010, 2700),
            "ciudad_residencia_tomador": (4190, 2540, 4870, 2700),

            "total_a_pagar": (240, 3470, 1100, 3590),
        },
        'unknown': {
            "fecha_expedicion": (610, 1150, 1060, 1250),
            "vigencia_desde": (1280, 1150, 1690, 1250),
            "vigencia_hasta": (1950, 1150, 2360, 1250),
            "numero_poliza": (450, 1740, 1020, 1862),
            "placa": (1090, 1740, 1458, 1862),
            "clase": (1585, 1740, 2400, 1862),
            "tipo_servicio": (2490, 1740, 3350, 1862),
            "cilindraje": (3500, 1737, 3911, 1859),
            "modelo": (4080, 1737, 4482, 1859),
            "pasajeros": (450, 2020, 650, 2150),
            "marca": (980, 1960, 2400, 2080),
            "linea": (973, 2096, 2400, 2208),
            "carroceria": (3285, 2020, 4300, 2150),
            "numero_motor": (450, 2320, 1400, 2460),
            "chasis": (1685, 2330, 2800, 2450),
            "vin": (2980, 2330, 4000, 2450),
            "nombres_apellidos_tomador": (450, 2620, 2090, 2760),
            "telefono_tomador": (2200, 2640, 2760, 2760),
            "tipo_documento_tomador": (2830, 2640, 3200, 2760),
            "numero_documento_tomador": (3430, 2640, 4000, 2760),
            "ciudad_residencia_tomador": (4060, 2640, 4600, 2760),
            "total_a_pagar": (500, 3530, 1200, 3650),
        }
    },
    'tecno': {
        'unknown': {
            "entidad_expide_certificado": (1920, 2600, 4490, 2750),

            "nit": (1300, 2870, 2200, 2999),
            "fecha_expedicion": (1390, 3120, 2200, 3250),

            "no_certificado": (3350, 2870, 4300, 2999),
            "fecha_vencimiento": (3350, 3120, 4300, 3250),

            "placa": (1100, 3730, 2300, 3870),
            "marca": (1100, 3980, 2300, 4120),
            "servicio": (1100, 4220, 2300, 4350),
            "cilindraje": (1100, 4450, 2300, 4570),
            "chasis": (1100, 4670, 2300, 4820),
            "linea": (1100, 4900, 2300, 5041),
            "color": (1100, 5134, 2300, 5254),

            "clase": (3180, 3730, 4200, 3870),
            "modelo": (3180, 3980, 4200, 4120),
            "combustible": (3180, 4220, 4200, 4350),
            "numero_motor": (3180, 4450, 4200, 4570),
            "vin": (3180, 4670, 4200, 4820),

            "nombre_propietario": (1600, 5400, 4200, 5540),
        },
    },
    'operacion': {
        'unknown': {
            "no_certificado": (2200, 1570, 3000, 1750),

            "placa": (1530, 2100, 2300, 2250),
            "clase": (1530, 2270, 2300, 2430),
            "carroceria": (1530, 2450, 2300, 2600),
            "linea": (1530, 3020, 2300, 3170),
            "servicio": (1530, 3200, 2300, 3350),
            "radio_accion": (1530, 3370, 2300, 3520),

            "modelo": (3300, 2100, 4200, 2250),
            "marca": (3300, 2280, 4200, 2430),
            "combustible": (3300, 2450, 4200, 2600),
            "modalidad": (3500, 2850, 4500, 3000),

            "razon_social": (1530, 4100, 2400, 4250),
            "nit": (1530, 4270, 2300, 4430),
            "direccion": (1530, 4450, 2700, 4600),
            "ciudad": (1530, 4620, 2500, 4770),

            "fecha_expedicion": (1530, 4800, 2300, 4950),
            "vigencia_desde": (2000, 5000, 2600, 5150),
            "fecha_vencimiento": (3100, 5000, 3650, 5150),

            "entidad_expide_certificado": (1530, 5160, 4490, 5310),
        }
    }
}

INSURER_KEYWORDS = {
    'bolivar': ['BOLIVAR'],
    'estado': ['ESTADO S.A.'],
    'mundial': ['MUNDIAL', 'ASEGURADORA'],
}

TARGET_WIDTH = 5100
TARGET_HEIGHT = 6600

def resize_image(image, width, height):
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("No se pudo leer la imagen en la ruta proporcionada.")
    image = resize_image(image, TARGET_WIDTH, TARGET_HEIGHT)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    preprocessed_path = image_path.replace('.jpg', '_pre.jpg').replace('.png', '_pre.png')
    cv2.imwrite(preprocessed_path, thresh)
    return preprocessed_path

def detect_insurer(extracted_text):
    for insurer, keywords in INSURER_KEYWORDS.items():
        for keyword in keywords:
            if keyword.upper() in extracted_text.upper():
                return insurer
    return 'unknown'

def detect_document_type_and_insurer(extracted_text):
    soat_keywords = ['SOAT', 'ASEGURADORA', 'MUNDIAL', 'PRIMA SOAT', 'ASEGuRADORY']
    tecno_keywords = ['CERTIFICADO DE REVISION TÉCNICO MECANICA', 'TECNO MECANICA', 'TÉCNICO MECANICA', 'DATOS CENTRO DIAGNOSTICO', 'CERTIFICADO DE REVISION TECNICO MECANICA Y DE EMISIONES CONTAMINANTES', 'TECNICO MECANICA']
    operacion_keywords = ['TARJETA DE OPERACIóN', 'TARJETA DE']
    text_upper = extracted_text.upper()
    doc_type = 'desconocido'
    for keyword in soat_keywords:
        if keyword.upper() in text_upper:
            doc_type = 'soat'
            break
    if doc_type == 'desconocido':
        for keyword in tecno_keywords:
            if keyword.upper() in text_upper:
                doc_type = 'tecno'
                break
    if doc_type == 'desconocido':
        for keyword in operacion_keywords:
            if keyword.upper() in text_upper:
                doc_type = 'operacion'
                break
    insurer = detect_insurer(extracted_text)
    return doc_type, insurer

def extract_text_from_roi(image, roi):
    x_start, y_start, x_end, y_end = roi
    cropped_image = image[y_start:y_end, x_start:x_end]
    cropped_gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(cropped_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ocr_result = ocr.ocr(thresh, cls=True)
    text = ""
    for res in ocr_result:
        for line in res:
            if len(line) >= 2 and isinstance(line[1], (tuple, list)):
                text += str(line[1][0]) + " "
    return text.strip()

def extract_data_with_rois(image_path, rois):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("No se pudo leer la imagen preprocesada.")
    data = {}
    for field, roi in rois.items():
        try:
            extracted_text = extract_text_from_roi(image, roi)
            data[field] = extracted_text if extracted_text else None
        except Exception:
            data[field] = None
    return data

def visualize_rois(image_path, rois, doc_type):
    image = cv2.imread(image_path)
    if image is None:
        return
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    fig, ax = plt.subplots(figsize=(20, 20))
    ax.imshow(image_rgb)
    for field, roi in rois.items():
        x_start, y_start, x_end, y_end = roi
        rect = patches.Rectangle((x_start, y_start), x_end - x_start, y_end - y_start, linewidth=2, edgecolor='r', facecolor='none')
        ax.add_patch(rect)
        plt.text(x_start, y_start - 10, field, color='red', fontsize=12, weight='bold')
    plt.axis('off')
    visualization_path = image_path.replace('.jpg', f'_{doc_type}_rois.jpg').replace('.png', f'_{doc_type}_rois.png')
    plt.savefig(visualization_path, bbox_inches='tight')
    plt.close(fig)

class UploadLicenseView(APIView):
    def post(self, request, format=None):
        if 'files' not in request.FILES:
            return Response({"error": "No se encontraron archivos en la solicitud."}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist('files')
        password = request.data.get('password', None)

        try:
            with TemporaryDirectory() as temp_dir:
                saved_file_paths = []
                for file in files:
                    saved_file_path = default_storage.save(os.path.join('licenses', file.name), file)
                    full_file_path = default_storage.path(saved_file_path)
                    saved_file_paths.append(full_file_path)

                extracted_data = {
                    "soat": None,
                    "tecno": None,
                    "operacion": None
                }

                for file_path in saved_file_paths:
                    try:
                        file_extension = os.path.splitext(file_path)[1].lower()
                        image_paths = []

                        if file_extension == '.pdf':
                            fmt = 'png'
                            convert_kwargs = {
                                'dpi': 600,
                                'fmt': fmt,
                                'output_folder': temp_dir,
                                'thread_count': 4,
                                'poppler_path': POPPLER_PATH
                            }
                            if password:
                                convert_kwargs['userpw'] = password
                            pages = convert_from_path(file_path, first_page=1, last_page=1, **convert_kwargs)
                            if not pages:
                                raise ValueError("El PDF no contiene páginas o la conversión falló.")
                            image_path = os.path.join(temp_dir, f'page_1.{fmt}')
                            pages[0].save(image_path, fmt.upper())
                            image_paths.append(image_path)
                        elif file_extension in ['.jpg', '.jpeg', '.png']:
                            image_paths.append(file_path)
                        else:
                            extracted_data[file.name] = {"error": "Formato de archivo no soportado. Solo se permiten imágenes y PDFs."}
                            continue

                        for image_path in image_paths:
                            preprocessed_image_path = preprocess_image(image_path)
                            preprocessed_image = cv2.imread(preprocessed_image_path)
                            if preprocessed_image is None:
                                raise ValueError("No se pudo leer la imagen preprocesada.")
                            raw_result = ocr.ocr(preprocessed_image, cls=True)
                            lines = []
                            for res in raw_result:
                                for line in res:
                                    if len(line) >= 2 and isinstance(line[1], (tuple, list)) and len(line[1]) >= 1:
                                        lines.append(str(line[1][0]))
                            extracted_text = "\n".join(lines)
                            doc_type, insurer = detect_document_type_and_insurer(extracted_text)
                            if doc_type in ['tecno', 'soat', 'operacion']:
                                rois = ROIS.get(doc_type, {}).get(insurer, ROIS.get(doc_type, {}).get('unknown', {}))
                                if rois:
                                    data = extract_data_with_rois(preprocessed_image_path, rois)
                                    visualize_rois(preprocessed_image_path, rois, doc_type)

                                    relative_path = saved_file_path.split(settings.MEDIA_ROOT)[-1]
                                    # soporte_url = request.build_absolute_uri(default_storage.url(relative_path))
                                    
                                    data['soporte'] = relative_path

                                    if extracted_data.get(doc_type) is None:
                                        extracted_data[doc_type] = data
                                    else:
                                        extracted_data[doc_type].update(data)
                                else:
                                    data = {"error": "No se encontraron ROIs definidos para el tipo de documento y aseguradora detectados."}
                                    if extracted_data.get(doc_type) is None:
                                        extracted_data[doc_type] = data
                                    else:
                                        extracted_data[doc_type].update(data)
                            else:
                                data = {"document_type": "desconocido"}
                                extracted_data[file.name] = data
                    except Exception as e:
                        extracted_data[file.name] = {"error": f"Error al procesar el archivo: {str(e)}"}

                return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error al procesar los archivos: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

ROIS_SIMPLE = {
    'soat': {
        'bolivar': {
            "fecha_expedicion": (610, 1150, 1060, 1250),
            "vigencia_desde": (1280, 1150, 1690, 1250),
            "vigencia_hasta": (1950, 1150, 2360, 1250),
            "numero_poliza": (450, 1740, 1020, 1862),
            "placa": (1090, 1740, 1458, 1862),
        },
        'aseguradora': {
            "fecha_expedicion": (410, 1010, 950, 1130),
            "vigencia_desde": (1110, 1010, 1620, 1130),
            "vigencia_hasta": (1850, 1010, 2370, 1130),

            "numero_poliza": (300, 1630, 910, 1810),
            "placa": (980, 1640, 1480, 1800),
        },
        'mundial': {
            "fecha_expedicion": (410, 1010, 950, 1130),
            "vigencia_desde": (1110, 1010, 1620, 1130),
            "vigencia_hasta": (1850, 1010, 2370, 1130),

            "numero_poliza": (300, 1630, 910, 1810),
            "placa": (980, 1640, 1480, 1800),
        },
        'estado': {
            "fecha_expedicion": (410, 1050, 950, 1180),
            "vigencia_desde": (1150, 1050, 1620, 1180),
            "vigencia_hasta": (1890, 1050, 2370, 1180),

            "numero_poliza": (280, 1630, 910, 1810),
            "placa": (1160, 1640, 1530, 1800),
        },
        'unknown': {
            "fecha_expedicion": (610, 1150, 1060, 1250),
            "vigencia_desde": (1280, 1150, 1690, 1250),
            "vigencia_hasta": (1950, 1150, 2360, 1250),
            "numero_poliza": (450, 1740, 1020, 1862),
            "placa": (1090, 1740, 1458, 1862),
        }
    },
    'tecno': {
        'unknown': {
            "fecha_expedicion": (1390, 3120, 2200, 3250),

            "no_certificado": (3350, 2870, 4300, 2999),
            "fecha_vencimiento": (3350, 3120, 4300, 3250),

            "placa": (1100, 3730, 2300, 3870),
            "marca": (1100, 3980, 2300, 4120),
        },
    },
    'operacion': {
        'unknown': {
            "no_certificado": (2200, 1570, 3000, 1750),

            "placa": (1530, 2100, 2300, 2250),
            "clase": (1530, 2270, 2300, 2430),
            "carroceria": (1530, 2450, 2300, 2600),
            "linea": (1530, 3020, 2300, 3170),
            "servicio": (1530, 3200, 2300, 3350),
            "radio_accion": (1530, 3370, 2300, 3520),

            "modelo": (3300, 2100, 4200, 2250),
            "marca": (3300, 2280, 4200, 2430),
            "combustible": (3300, 2450, 4200, 2600),
            "modalidad": (3500, 2850, 4500, 3000),

            "razon_social": (1530, 4100, 2400, 4250),
            "nit": (1530, 4270, 2300, 4430),
            "direccion": (1530, 4450, 2700, 4600),
            "ciudad": (1530, 4620, 2500, 4770),

            "fecha_expedicion": (1530, 4800, 2300, 4950),
            "vigencia_desde": (2000, 5000, 2600, 5150),
            "fecha_vencimiento": (3100, 5000, 3650, 5150),

            "entidad_expide_certificado": (1530, 5160, 4490, 5310),
        }
    }
}

class UploadLicenseSimplifiedView(APIView):
    def post(self, request, format=None):
        if 'files' not in request.FILES:
            return Response({"error": "No se encontraron archivos en la solicitud."}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES.getlist('files')
        password = request.data.get('password', None)

        try:
            with TemporaryDirectory() as temp_dir:
                saved_file_paths = []
                for file in files:
                    saved_file_path = default_storage.save(os.path.join('licenses', file.name), file)
                    full_file_path = default_storage.path(saved_file_path)
                    saved_file_paths.append(full_file_path)

                extracted_data = {
                    "soat": None,
                    "tecno": None
                }

                for file_path in saved_file_paths:
                    try:
                        file_extension = os.path.splitext(file_path)[1].lower()
                        image_paths = []

                        if file_extension == '.pdf':
                            fmt = 'png'
                            convert_kwargs = {
                                'dpi': 600,
                                'fmt': fmt,
                                'output_folder': temp_dir,
                                'thread_count': 4,
                                'poppler_path': POPPLER_PATH
                            }
                            if password:
                                convert_kwargs['userpw'] = password
                            pages = convert_from_path(file_path, first_page=1, last_page=1, **convert_kwargs)
                            if not pages:
                                raise ValueError("El PDF no contiene páginas o la conversión falló.")
                            image_path = os.path.join(temp_dir, f'page_1.{fmt}')
                            pages[0].save(image_path, fmt.upper())
                            image_paths.append(image_path)
                        elif file_extension in ['.jpg', '.jpeg', '.png']:
                            image_paths.append(file_path)
                        else:
                            extracted_data[file.name] = {"error": "Formato de archivo no soportado. Solo se permiten imágenes y PDFs."}
                            continue

                        for image_path in image_paths:
                            preprocessed_image_path = preprocess_image(image_path)
                            preprocessed_image = cv2.imread(preprocessed_image_path)
                            if preprocessed_image is None:
                                raise ValueError("No se pudo leer la imagen preprocesada.")
                            raw_result = ocr.ocr(preprocessed_image, cls=True)
                            lines = []
                            for res in raw_result:
                                for line in res:
                                    if len(line) >= 2 and isinstance(line[1], (tuple, list)) and len(line[1]) >= 1:
                                        lines.append(str(line[1][0]))
                            extracted_text = "\n".join(lines)
                            doc_type, insurer = detect_document_type_and_insurer(extracted_text)
                            if doc_type in ['tecno', 'soat']:
                                rois = ROIS_SIMPLE.get(doc_type, {}).get(insurer, ROIS_SIMPLE.get(doc_type, {}).get('unknown', {}))
                                if rois:
                                    data = extract_data_with_rois(preprocessed_image_path, rois)
                                    visualize_rois(preprocessed_image_path, rois, doc_type)

                                    relative_path = saved_file_path.split(settings.MEDIA_ROOT)[-1]
                                    # soporte_url = request.build_absolute_uri(default_storage.url(relative_path))
                                    
                                    data['soporte'] = relative_path

                                    if extracted_data.get(doc_type) is None:
                                        extracted_data[doc_type] = data
                                    else:
                                        extracted_data[doc_type].update(data)
                                else:
                                    data = {"error": "No se encontraron ROIs definidos para el tipo de documento y aseguradora detectados."}
                                    if extracted_data.get(doc_type) is None:
                                        extracted_data[doc_type] = data
                                    else:
                                        extracted_data[doc_type].update(data)
                            else:
                                data = {"document_type": "desconocido"}
                                extracted_data[file.name] = data
                    except Exception as e:
                        extracted_data[file.name] = {"error": f"Error al procesar el archivo: {str(e)}"}

                return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error al procesar los archivos: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
