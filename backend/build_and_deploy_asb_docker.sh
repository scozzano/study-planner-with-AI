#!/bin/bash

# Script para construir y desplegar la imagen Docker de ASB

set -e

# Configuración
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="asb-recommender"
IMAGE_TAG="latest"

echo "🚀 Construyendo y desplegando imagen Docker para ASB Recommender"
echo "Account ID: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo "Repository: $ECR_REPOSITORY"

# 1. Crear repositorio ECR si no existe
echo "📦 Verificando repositorio ECR..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION 2>/dev/null || {
    echo "Creando repositorio ECR..."
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
}

# 2. Autenticar Docker con ECR
echo "🔐 Autenticando Docker con ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 3. Construir imagen Docker
echo "🔨 Construyendo imagen Docker..."
docker build --platform linux/amd64 \
    -f Dockerfile.asb -t $ECR_REPOSITORY:$IMAGE_TAG .

# 4. Etiquetar imagen para ECR
echo "🏷️  Etiquetando imagen para ECR..."
docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# 5. Subir imagen a ECR
echo "⬆️  Subiendo imagen a ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG

# 6. Actualizar función Lambda
echo "🔄 Actualizando función Lambda..."
FUNCTION_NAME=$(aws lambda list-functions --query 'Functions[?contains(FunctionName, `ASBRecommenderUnifiedFunction`)].FunctionName' --output text | head -1)

if [ -n "$FUNCTION_NAME" ]; then
    echo "Actualizando función: $FUNCTION_NAME"
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG \
        --region $AWS_REGION
    
    echo "✅ Función Lambda actualizada exitosamente"
else
    echo "❌ No se encontró la función Lambda ASBRecommenderUnifiedFunction"
fi

echo "🎉 Despliegue completado!"
echo "Imagen: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
