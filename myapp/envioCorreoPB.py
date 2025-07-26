import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Función para enviar correo electrónico


def send_email(email, first_name, last_name):

    # Configurar el correo electrónico
    email_origen = "asistemas@berlinasdelfonce.com"
    email_destino = email

    # Direcciones de correo para la copia
    cc_emails = ["peti@berlinasdelfonce.com", "pjcobos@berlinasdelfonce.co"]

    ruta_img = "https://saas-cms-admin-sandbox.s3.us-west-2.amazonaws.com/sites/647e59513d04a300028afa72/assets/647e59b33d04a300028afa77/Logo_berlinas_blanco_fondo-transparente_DIGITAL.png"

    message = MIMEMultipart()
    message["From"] = email_origen
    message["To"] = email_destino
    # message["Cc"] = ", ".join(cc_emails)
    message["Subject"] = "Acceso a Nuevo Aplicativo(5Apps) Para la Creación de Informes"

    body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Acceso a Nuevo Aplicativo(5Apps) Para la Creación de Informes</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 700px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; background-color: #fff; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);">
                <div style="text-align: center; background-color: #009944; border-radius: 10px;">
                    <img src="{ruta_img}" alt="Logo de la empresa" style="max-width: 150px; display: block; margin: 20px auto;">
                </div>
                <div style="margin-top: 20px; line-height: 1.6; color: #000;">
                    <p>Estimado {first_name} {last_name},</p>
                    <p color: #000 !important;>De antemano, reciba un cordial saludo del Departamento de Tecnologías de Berlinas del Fonce S.A.,</p>
                    <p color: #000 !important;>Nos complace notificarle su acceso al nuevo aplicativo(<strong style="color: #009944">5Apps</strong>), donde va a poder visualizar y descargar información importante y necesaria para el desarrollo de sus operaciones.</p>
                    <p color: #000 !important;>Cabe recalcar que la capacitación se va a realizar de manera presencial donde se darán las instrucciones de acceso y manejo del aplicativo, por lo tanto, le solicito, me indique la fecha y hora para brindarla(No durará más de 10 minutos).</p>
                    <p color: #000 !important;>A continuación el link de acceso a <strong style="color: #009944">5Apps</strong> y su respectivo usuario y contraseña</p>
                    <p color: #000 !important;>Link de acceso: <a style="color: #009944" href="http://wsdx.berlinasdelfonce.com">wsdx.berlinasdelfonce.com</a><br/>
                    Usuario: PBECERRA<br/>
                    Contraseña: PBECERRA</p>
                    <p color: #000 !important;>Se le ha dado acceso a 7 módulos de operaciones, los cuales son:</p>
                    <p color: #000 !important;>
                    <strong style="color: #009944">> </strong>Busquedas por Fechas<br/>
                    <strong style="color: #009944">> </strong>Consolidado Combustible<br/>
                    <strong style="color: #009944">> </strong>Detallado Combustible<br/>
                    <strong style="color: #009944">> </strong>Informe Pasajeros Movilizados<br/>
                    <strong style="color: #009944">> </strong>Primeras Lineas Colibertador<br/>
                    <strong style="color: #009944">> </strong>Primeras Lineas Por Empresa<br/>
                    <strong style="color: #009944">> </strong>Viajes</p>
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
        smtp = smtplib.SMTP_SSL("mail.berlinasdelfonce.com")
        smtp.login(email_origen, "PRUEBA2023")
        smtp.sendmail(
            email_origen, [email_destino] + cc_emails, message.as_string())
        smtp.quit()
        print(f"Correo Enviado a {email_destino}")
    except Exception as e:
        print("No se pudo enviar el correo a ${email} {str(e)}")


# send_email("operaciones@berlinasdelfonce.com", "Pedro", "Becerra")
