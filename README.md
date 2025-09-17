# Study Planning Recommendation Tool  

## Author
Sofia Cozzano, Ana Fernández

## Thesis Supervisor
Dr. Ing. Daniel Calegari

## Overview  
This repository contains a project that implements various recommendation algorithms within a study planning tool. The system is composed of both a frontend and a backend, designed to provide students with personalized academic planning support.

The backend is responsible for implementing the recommendation logic, managing data, and exposing APIs, while the frontend offers an intuitive interface where students can interact with the planning tool, explore course recommendations, and visualize their academic paths.

Together, these components create a comprehensive solution that helps streamline academic decision-making through data-driven recommendations.

## Technologies  
- **Frontend**: Flutter  
- **Backend**: Python  

## Prerequisites

### Operating System
- **Linux** (Ubuntu 20.04+ recommended)
- **macOS** (10.15+)
- **Windows** (with WSL2 recommended)

### Python
- **Python 3.12** (required)
- **pip** (Python package manager)

### AWS CLI
- **AWS CLI v2** installed and configured
- AWS credentials configured with permissions for:
  - SageMaker
  - S3
  - DynamoDB
  - ECR
  - IAM
  - Lambda
  - API Gateway

### Docker
- **Docker** installed and running
- **Docker Compose** (optional)

### SAM CLI
- **AWS SAM CLI** for infrastructure deployment

### Flutter
- **Flutter SDK** (stable version recommended)
- **Dart SDK** (included with Flutter)

## Installation  
Clone the repository:  
```bash
git clone https://github.com/your-username/study-planning-tool.git
cd study-planning-tool
```

---

## Backend Startup

### 1. Configure virtual environment
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-lambda.txt
```

### 3. Configure AWS CLI
```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json
```

### 4. Configure environment variables
```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=account_id
export S3_BUCKET=bucket_name
export S3_PREFIX=bucket_prefix
export DDB_TABLE=table_name
```

### 5. Build and push Docker images
```bash
# SageMaker image
./build_and_push_ecr.sh

# ASB Lambda image
./build_and_deploy_asb_docker.sh
```

### 6. Deploy infrastructure
```bash
sam build
sam deploy --resolve-image-repos
```

### 7. Train and Predict
Train the models using the endpoints, and create manually the endpoints in sagemaker.

---

## Education Planner Startup


### 1. Environment Configuration

This project contains 3 flavors:

- development
- staging
- production

Before running the application, you need to set up environment-specific configuration files. Each environment requires its own `env_keys` file:


#### 2. Required Environment Files

| Environment | File |
|-------------|------|
| Development | `env_keys.dev.json` |
| Staging | `env_keys.stg.json` |
| Production | `env_keys.prod.json` |

#### 3. Creating Environment Files

**1. Development Environment (`env_keys.dev.json`)**
```json
{
    "API_URL": "http://localhost:3000",
}
```

**2. Staging Environment (`env_keys.stg.json`)**
```json
{
    "API_URL": "https://your-staging-api-url.com",
}
```

**3. Production Environment (`env_keys.prod.json`)**
```json
{
    "API_URL": "https://your-production-api-url.com",
}
```

### 4. Running the Application

#### Option 1: Using VS Code Launch Configurations

1. Open the project in VS Code
2. Go to the Debug panel (Ctrl+Shift+D)
3. Select the desired environment from the dropdown:
   - "Launch development"
   - "Launch staging" 
   - "Launch production"
4. Press F5 or click the play button

#### Option 2: Using Command Line

```sh
# Development
$ flutter run --flavor development --target lib/main_development.dart --dart-define-from-file env_keys.dev.json

# Staging
$ flutter run --flavor staging --target lib/main_staging.dart --dart-define-from-file env_keys.stg.json

# Production
$ flutter run --flavor production --target lib/main_production.dart --dart-define-from-file env_keys.prod.json
```

### 5. Environment Variables

The application reads the following environment variables:

- `API_URL`: The base URL for the API endpoints
- `FLUTTER_DEBUG`: Boolean flag to enable/disable debug features

These variables are automatically loaded from the corresponding `env_keys` file when using the launch configurations.

_\*Education Planner works on Web._



