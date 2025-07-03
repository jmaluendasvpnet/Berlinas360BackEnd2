import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(email, first_name, last_name, uidb64, token):

    # Configurar el correo electrónico
    email_origen = "jmaluendasbautista@gmail.com"
    email_destino = email
    ruta_img = "https://saas-cms-admin-sandbox.s3.us-west-2.amazonaws.com/sites/647e59513d04a300028afa72/assets/647e59b33d04a300028afa77/Logo_berlinas_blanco_fondo-transparente_DIGITAL.png"

    message = MIMEMultipart()
    message["From"] = email_origen
    message["To"] = email_destino
    message["Subject"] = "Prueba recuperacion de contraseña"

    body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Portal Propietarios - Envio Link de tutoriales</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; background-color: #fff; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);">
                <div style="text-align: center; background-color: #009944; border-radius: 10px;">
                    <img src="{ruta_img}" alt="Logo de la empresa" style="max-width: 150px; display: block; margin: 20px auto;">
                </div>
                <div style="margin-top: 20px; line-height: 1.6; color: #000;">
                    <p>Estimado(a) {first_name} {last_name},</p>
                    <p color: #000 !important;>Esta es una prueba para el envio de link de restablecimiento de contraseña</p>
                    <p color: #000 !important;>http://localhost:5173/?uidb64={uidb64}&token={token}</p>
                    <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">
                    <p style="color: #009944;"><strong>Cordialmente,</strong></p>
                    <p color: #000 !important;>Jorge Eliecer Maluendas Bautista<br>Programador de Sistemas<br><a style="text-decoration: none; color: #009944;" href="mailto:asistemas@berlinasdelfonce.com">asistemas@berlinasdelfonce.com</a><br>Teléfono: <a style="text-decoration: none; color: #009944;" href="https://api.whatsapp.com/send?phone=+573168756931">3168756931</a><br>Cra. 68D No. 15 – 15<br>Bogotá D.C. - Colombia</p>
                </div>
                <div style="margin-top: 30px; font-style: italic; font-size: 10px; color: #888; text-align: center;">
                    <p>Berlinas del Fonce S.A.</p>
                </div>
            </div>
        </body>
        </html>
    """

    message.attach(MIMEText(body, "html"))

    try:
        # Aca debe ir la zona de envio del correo
        print(f"Correo Enviado a {email}")
    except Exception as e:
        print("No se pudo enviar el correo a ${email} {str(e)}")
