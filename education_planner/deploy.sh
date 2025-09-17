#!/bin/bash

# Configuración
BUCKET_NAME="ada-project-frontend"
REGION="us-east-1"

# 1. Compilar la app Flutter para Web
echo "🔨 Compilando app Flutter para web..."
flutter build web --target=lib/main_staging.dart --dart-define-from-file env_keys.stg.json

# 2. Verificar si la compilación fue exitosa
if [ $? -ne 0 ]; then
  echo "❌ Error al compilar la app Flutter"
  exit 1
fi

# 3. Subir archivos a S3
echo "☁️ Subiendo a S3: s3://$BUCKET_NAME"
aws s3 sync build/web/ s3://$BUCKET_NAME --delete

# 4. Verificar si la subida fue exitosa
if [ $? -ne 0 ]; then
  echo "❌ Error al subir archivos a S3"
  exit 1
fi

# 5. Mostrar URL del sitio
URL="http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
echo "✅ Deploy completo. Tu sitio está disponible en:"
echo "$URL"
