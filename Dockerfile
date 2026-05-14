# Usa la imagen oficial de Playwright que ya tiene Chromium y las dependencias de Linux
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto de Flask
EXPOSE 5000

# Variable de entorno para indicar que estamos en Docker
ENV IN_DOCKER=true
ENV HEADLESS=true

# Comando para iniciar la API
CMD ["python", "app.py"]
