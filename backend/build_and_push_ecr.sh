#!/bin/bash

# Configuración
ECR_REPO="881490135473.dkr.ecr.us-east-1.amazonaws.com/recommendation-algorithms"
IMAGE_TAG="latest"
REGION="us-east-1"

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

echo "🔨 Construyendo imagen Docker para plataforma linux/amd64..."
docker buildx build --platform linux/amd64 \
    -t $ECR_REPO:$IMAGE_TAG \
    -f sagemaker/Dockerfile \
    --load \
    sagemaker/

echo "📤 Subiendo imagen a ECR..."
docker push $ECR_REPO:$IMAGE_TAG

echo "✅ Imagen ECR actualizada exitosamente!"
echo "URI de la imagen: $ECR_REPO:$IMAGE_TAG"ECR_REPO="881490135473.dkr.ecr.us-east-1.amazonaws.com/asb-recomm-sagemaker"

