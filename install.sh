#!/bin/bash

# Imprime un mensaje indicando que la instalación de dlib está comenzando
echo "Instalando dlib desde el archivo .whl..."

# Instalar dlib desde el archivo .whl localizado en la carpeta wheels
pip install ./wheels/dlib-19.24.99-cp312-cp312-linux_x86_64.whl

# Imprime un mensaje indicando que la instalación de dlib ha finalizado
echo "Instalación de dlib completada."

# Imprime un mensaje indicando que la instalación de dependencias desde requirements.txt está comenzando
echo "Instalando dependencias desde requirements.txt..."

# Instalar el resto de las dependencias desde el archivo requirements.txt
pip install -r requirements.txt

# Imprime un mensaje indicando que la instalación de dependencias ha finalizado
echo "Instalación de dependencias completada."
