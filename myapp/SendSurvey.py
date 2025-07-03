import pandas as pd
import requests
from django.http import JsonResponse

def send_survey(to, name):
    key_mb = 'Ydq4jG2Xps6cA0ZKkdHT1MG1V'
    
    url = f"https://conversations.messagebird.com/v1/send"
    headers = {
        'Authorization': f'AccessKey {key_mb}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "content": {
            "hsm": {
                "language": {
                    "code": "es"
                },
                "namespace": "VPNet_a322d",
                "params": [
                    {
                        "default": name
                    }
                ],
                "templateName": "encuesta_servicio_al_cliente",
            }
        },
        "to": f"+1{to}",
        "type": "hsm",
        "from": "f9b70a29-f331-4941-8a39-810502291210"
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print(f"Encuesta enviada a {name} ({to}) correctamente.")
        return {"status": "success", "message": f"Encuesta enviada a {name} ({to}) correctamente."}
    except requests.RequestException as e:
        print(f"Error enviando encuesta a {name} ({to}): {e}")
        return {"status": "error", "message": f"Error enviando encuesta a {name} ({to}): {e}"}

def process_excel(request):
    excel_file = r'C:\Users\JMaluendas\Downloads\numbres_name.xlsx'
    
    try:
        df = pd.read_excel(excel_file, sheet_name='junio julio agosto 2024')
        print(df)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
    df.columns = ['ID', 'Name', 'Phone Number']
    df['First Name'] = df['Name'].str.split().str[0]

    df['Phone Number'] = df['Phone Number'].fillna('')
    df['Phone Number'] = df['Phone Number'].astype(str)
    df['Phone Number'] = df['Phone Number'].str.replace(' ', '')
    df['Phone Number'] = df['Phone Number'].str.split('|')

    filtered_rows = []
    
    for index, row in df.iterrows():
        phone_numbers = row['Phone Number']
        if isinstance(phone_numbers, list):
            for number in phone_numbers:
                if number.startswith('787') or number.startswith('939') or number.startswith('215') or number.startswith('320') or number.startswith('954') or number.startswith('939' or number.startswith('954')):
                    filtered_rows.append({
                        'First Name': row['First Name'],
                        'Phone Number': number
                    })
                    break

    df_filtered = pd.DataFrame(filtered_rows)
    
    print("Filas filtradas:")
    print(df_filtered)

    if df_filtered.empty:
        print("No hay filas que comiencen con 787.")
        return JsonResponse({"results": "No hay números que comiencen con 787."})

    results = []
    for _, row in df_filtered.iterrows():
        first_name = row['First Name']
        phone_number = row['Phone Number']
        try:
            result = send_survey(phone_number, first_name)
            results.append(result)
        except:
            print(f"Encuesta Nooooooooo enviada a {first_name} ({phone_number})")

    return JsonResponse({"results": results})


# import subprocess
# from django.http import HttpResponse
# import os
# import tempfile
# import shutil
# from django.views.decorators.csrf import csrf_exempt


# @csrf_exempt
# def docx_to_pdf_view(request):
#     docx_file = r'C:/Users/JMaluendas/Desktop/DocumentoConTabla.docx'
#     if not os.path.exists(docx_file):
#         print('No existe el archivo')
#         return HttpResponse("El archivo DOCX no existe", status=404)

#     soffice_path = r'C:\Program Files\LibreOffice\program\soffice.exe'

#     temp_dir = tempfile.gettempdir()
#     pdf_output_path = os.path.join(temp_dir, 'DocumentoConTabla.pdf')

#     result = subprocess.run([
#         soffice_path, '--headless', '--convert-to', 'pdf', docx_file, '--outdir', temp_dir
#     ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

#     print("STDOUT:", result.stdout)
#     print("STDERR:", result.stderr)

#     if result.returncode != 0:
#         error_message = f"Error en LibreOffice: {result.stderr}"
#         return HttpResponse(error_message, status=500)

#     if not os.path.exists(pdf_output_path):
#         return HttpResponse("El archivo PDF no fue creado", status=500)

#     with open(pdf_output_path, 'rb') as pdf:
#         response = HttpResponse(pdf.read(), content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename=salida.pdf'
#         return response


import os
import subprocess
import tempfile
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def docx_to_pdf_view(request):
    if request.method == 'POST' and 'file' in request.FILES:
        docx_file = request.FILES['file']

        temp_dir = tempfile.gettempdir()
        temp_docx_path = os.path.join(temp_dir, 'temp_docx.docx')

        with open(temp_docx_path, 'wb') as temp_file:
            for chunk in docx_file.chunks():
                temp_file.write(chunk)

        pdf_output_path = os.path.splitext(temp_docx_path)[0] + '.pdf'

        result = subprocess.run([
            'soffice', '--headless', '--convert-to', 'pdf', temp_docx_path, '--outdir', temp_dir
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            error_message = f"Error en LibreOffice: {result.stderr}"
            return HttpResponse(error_message, status=500)

        if not os.path.exists(pdf_output_path):
            return HttpResponse("El archivo PDF no fue creado", status=500)

        with open(pdf_output_path, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=converted_file.pdf'
            return response

    return HttpResponse("Solicitud inválida o archivo no encontrado", status=400)

HOST_OCULTO = 'berlinasdelfonce'
PASS_OCULTO = 'akpa ecrt crgj uert'

from django.conf import settings
from .models import ActaConciliacion
from datetime import datetime

import os
import tempfile
import subprocess
import smtplib
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from .models import ActaConciliacion

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_CONTENT_SID = os.getenv('TWILIO_CONTENT_SID')
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_VOICE_FROM = "+1234567890"
HOST = HOST_OCULTO
PASS = PASS_OCULTO
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
from .consumers import broadcast_siniestro_update
@csrf_exempt
def docx_to_pdf_and_save_in_model(request):
    if request.method == 'POST' and 'file' in request.FILES and 'acta_id' in request.POST:
        acta_id = request.POST['acta_id']
        firma_conductor2 = request.POST.get('firma_conductor2', '')
        docx_file = request.FILES['file']
        try:
            temp_dir = tempfile.gettempdir()
            temp_docx_path = os.path.join(temp_dir, f'temp_docx_{acta_id}.docx')
            with open(temp_docx_path, 'wb') as temp_file:
                for chunk in docx_file.chunks():
                    temp_file.write(chunk)

            pdf_filename = f"Acta_Conciliacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_output_dir = os.path.join(settings.MEDIA_ROOT, 'conciliaciones')
            if not os.path.exists(pdf_output_dir):
                os.makedirs(pdf_output_dir, exist_ok=True)

            expected_temp_pdf = os.path.join(pdf_output_dir, f'temp_docx_{acta_id}.pdf')
            final_pdf_path = os.path.join(pdf_output_dir, pdf_filename)

            cmd = [
                'soffice', '--headless',
                '--convert-to', 'pdf:writer_pdf_Export',
                temp_docx_path, '--outdir', pdf_output_dir
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                return HttpResponse(f"Error en LibreOffice: {result.stderr}", status=500)

            if not os.path.exists(expected_temp_pdf):
                return HttpResponse("El archivo PDF no fue creado o no tiene el nombre esperado", status=500)

            os.rename(expected_temp_pdf, final_pdf_path)

            try:
                acta = ActaConciliacion.objects.get(id=acta_id)
                acta.pdf_conciliacion = os.path.join('conciliaciones', pdf_filename)
                if firma_conductor2:
                    acta.firma_conductor2 = firma_conductor2
                acta.save()
                broadcast_siniestro_update(acta.siniestro.id)
            except ActaConciliacion.DoesNotExist as e:
                print("ERROR:", str(e))
                return HttpResponse("No se encontró el acta especificada", status=404)

            pdf_url = f"https://c45a-186-96-97-246.ngrok-free.app/media/conciliaciones/{pdf_filename}"
            try:
                client.messages.create(
                    body="Su documento de conciliación se ha registrado exitosamente. Adjunto encontrará el PDF.",
                    from_=TWILIO_WHATSAPP_FROM,
                    to="whatsapp:+573203339694",
                    media_url=[pdf_url]
                )
            except Exception as twilio_e:
                return HttpResponse(f"Error al enviar mensaje de WhatsApp: {str(twilio_e)}", status=500)

            email_destino = acta.email_conductor2
            if email_destino:
                try:
                    email_origen = "jmaluendasbautista@gmail.com"
                    ruta_img = "https://saas-cms-admin-sandbox.s3.us-west-2.amazonaws.com/sites/647e59513d04a300028afa72/assets/647e59b33d04a300028afa77/Logo_berlinas_blanco_fondo-transparente_DIGITAL.png"
                    asunto = "Acta de Conciliación Firmada"

                    mensaje = MIMEMultipart()
                    mensaje["From"] = email_origen
                    mensaje["To"] = email_destino
                    mensaje["Subject"] = asunto

                    cuerpo_html = f"""
                    <!DOCTYPE html>
                    <html lang="es">
                    <head>
                        <meta charset="UTF-8">
                        <title>Acta de Conciliación</title>
                    </head>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                        <div style="max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; background-color: #fff; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);">
                            <div style="text-align: center; background-color: #009944; border-radius: 10px;">
                                <img src="{ruta_img}" alt="Logo" style="max-width: 150px; display: block; margin: 20px auto;">
                            </div>
                            <div style="margin-top: 20px; line-height: 1.6; color: #000;">
                                <p>Estimado(a),</p>
                                <p style="color: #000 !important;">
                                    Le informamos que su Acta de Conciliación ha sido registrada exitosamente. Adjunto encontrará el documento en formato PDF.
                                </p>
                                <p style="color: #000 !important;">
                                    Para mayor información, puede contactarnos respondiendo a este correo.
                                </p>
                                <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">
                                <p style="color: #009944;"><strong>Cordialmente,</strong></p>
                                <p style="color: #000 !important;">
                                    Departamento de Juridica<br>
                                    <a style="text-decoration: none; color: #009944;" href="mailto:juridica@berlinasdelfonce.com">juridica@berlinasdelfonce.com</a><br>
                                    Celular: <a style="text-decoration: none; color: #009944;" href="https://api.whatsapp.com/send?phone=+573165269210">3165269210</a><br>
                                    Teléfono: <a style="text-decoration: none; color: #009944;" href="">Teléfono: (601) 743 5050 ext. 1003</a><br>
                                    Cra. 68D No.15-15 Zona Industrial Montevideo<br>
                                    Bogota D.C. - Colombia
                                </p>
                            </div>
                            <div style="margin-top: 30px; font-style: italic; font-size: 10px; color: #888; text-align: center;">
                                <p>© 2025 - Todos los derechos reservados</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """

                    mensaje.attach(MIMEText(cuerpo_html, "html"))

                    with open(final_pdf_path, "rb") as f:
                        pdf_attach = MIMEApplication(f.read(), _subtype="pdf")
                    pdf_attach.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
                    mensaje.attach(pdf_attach)

                    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)

                    smtp.login(email_origen, PASS)
                    smtp.sendmail(email_origen, email_destino, mensaje.as_string())
                    smtp.quit()
                except Exception as email_error:
                    return HttpResponse(f"Error al enviar el correo: {str(email_error)}", status=500)

            with open(final_pdf_path, 'rb') as f:
                pdf_data = f.read()
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={pdf_filename}'
            return response

        except Exception as e:
            return HttpResponse(f"Error interno: {str(e)}", status=500)

    return HttpResponse("Solicitud inválida o parámetros faltantes", status=400)
