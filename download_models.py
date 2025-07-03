# download_models.py
import whisper
import os

print("--- Iniciando descarga de modelos ---")

download_root = "/models/whisper"
os.makedirs(download_root, exist_ok=True)
print(f"Directorio de descarga: {download_root}")

print("Descargando Whisper 'medium'...")
try:
    model = whisper.load_model("medium", download_root=download_root)
    print("Descarga de Whisper 'medium' completada.")
except Exception as e:
    print(f"Error descargando Whisper 'medium': {e}")


print("--- Descarga de modelos finalizada ---")