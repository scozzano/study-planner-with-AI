import json
import os
import traceback
from datetime import datetime, timezone
from typing import Dict, Any

import boto3

sagemaker = boto3.client('sagemaker')
ecr = boto3.client('ecr')

def create_training_job_name(algorithm: str, degree_id: str) -> str:
    """Crear nombre único para el training job"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{algorithm}-{degree_id}-{timestamp}"

def get_ecr_image_uri():
    """Obtener URI de la imagen ECR personalizada"""
    return "881490135473.dkr.ecr.us-east-1.amazonaws.com/recommendation-algorithms:latest"

def create_sagemaker_training_job(algorithm: str, degree_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Crear SageMaker Training Job"""

    role_arn = os.environ.get("SAGEMAKER_EXEC_ROLE_ARN")
    s3_bucket = os.environ.get("S3_BUCKET", "recommendation-data-ort")
    s3_prefix = os.environ.get("S3_PREFIX", "recommender")

    if not role_arn:
        raise ValueError("SAGEMAKER_EXEC_ROLE_ARN no está configurado")

    job_name = create_training_job_name(algorithm, degree_id)

    algorithm_configs = {
        "asb": {
            "instance_type": "ml.m5.large",
            "instance_count": 1,
            "max_runtime": 3600,
            "hyperparameters": {
                "ALGORITHM": "asb",
                "DDB_TABLE": os.environ.get("TABLE_NAME", "AdaProjectTable"),
                "DEGREE_ID": degree_id,
                "ASB_FEATURE": config.get("feature", "Course-Semester"),
                "ASB_IS_ATOMIC": str(config.get("is_atomic", True)).lower(),
                "ASB_INDEX_TYPE": config.get("index_type", "fachsemester"),
                "ASB_LABEL": config.get("label", "Overall GPA"),
                "ASB_IS_BINARY": str(config.get("is_binary_label", True)).lower(),
                "ASB_CRITERION": config.get("criterion", "gini"),
                "ASB_RANDOM_STATE": str(config.get("random_state", 42)),
                "ASB_MAX_DEPTH": str(config.get("max_depth", 10)),
                "ASB_MIN_SAMPLES_LEAF": str(config.get("min_samples_leaf", 2)),
                "ASB_MIN_SAMPLES_SPLIT": str(config.get("min_samples_split", 5)),
                "ASB_USE_SMOTE": str(config.get("use_smote", False)).lower(),
                "ASB_COMBINATIONS": ",".join(config.get("combinations", ["behav", "diff", "num"])),
                "ASB_COURSE": config.get("course", "course-1479"),
                "ASB_LABEL_INDEX": str(config.get("label_index", 1)),
                "ASB_IS_PM": str(config.get("is_pm", False)).lower(),
                "ASB_GPA_GRADES": config.get("GPA_grades", "passed+failed last attempt"),
                "ASB_BINARY_THRESHOLD": str(config.get("binary_threshold", 2.0))
            }
        },
        "rf": {
            "instance_type": "ml.m5.large",
            "instance_count": 1,
            "max_runtime": 3600,
            "hyperparameters": {
                "ALGORITHM": "rf",
                "DDB_TABLE": os.environ.get("TABLE_NAME", "AdaProjectTable"),
                "DEGREE_ID": degree_id,
                "n_estimators": str(config.get("n_estimators", 100)),
                "max_depth": str(config.get("max_depth", 10)),
                "random_state": str(config.get("random_state", 42))
            }
        },
        "pm": {
            "instance_type": "ml.m5.large",
            "instance_count": 1,
            "max_runtime": 3600,
            "hyperparameters": {
                "ALGORITHM": "pm",
                "DDB_TABLE": os.environ.get("TABLE_NAME", "AdaProjectTable"),
                "DEGREE_ID": degree_id,
                "GPA_SUCCESS_THRESHOLD": str(config.get("gpa_success_threshold", 3.6)),
                "SIMILARITY_THRESHOLD": str(config.get("similarity_threshold", 0.7)),
                "TOP_K": str(config.get("top_k", 5))
            }
        },
        "spm": {
            "instance_type": "ml.m5.large",
            "instance_count": 1,
            "max_runtime": 3600,
            "hyperparameters": {
                "ALGORITHM": "spm",
                "DDB_TABLE": os.environ.get("TABLE_NAME", "AdaProjectTable"),
                "DEGREE_ID": degree_id,
                "max_pattern_length": str(config.get("max_pattern_length", 3)),
                "min_support": str(config.get("min_support", 0.1))
            }
        }
    }

    if algorithm not in algorithm_configs:
        raise ValueError(f"Algoritmo no soportado: {algorithm}")

    algo_config = algorithm_configs[algorithm]

    training_job_config = {
        "TrainingJobName": job_name,
        "RoleArn": role_arn,
        "AlgorithmSpecification": {
            "TrainingImage": get_ecr_image_uri(),
            "TrainingInputMode": "File",
            "ContainerEntrypoint": ["python", f"{algorithm}_train.py"]
        },
        "ResourceConfig": {
            "InstanceType": algo_config["instance_type"],
            "InstanceCount": algo_config["instance_count"],
            "VolumeSizeInGB": 30
        },
        "OutputDataConfig": {
            "S3OutputPath": f"s3://{s3_bucket}/{s3_prefix}/models/{algorithm}/{degree_id}/"
        },
        "HyperParameters": algo_config["hyperparameters"],
        "StoppingCondition": {
            "MaxRuntimeInSeconds": algo_config["max_runtime"]
        }
    }

    response = sagemaker.create_training_job(**training_job_config)

    return {
        "TrainingJobName": job_name,
        "TrainingJobArn": response["TrainingJobArn"],
        "Status": "InProgress"
    }

def sagemaker_train_handler(event, context):
    """Handler para entrenar modelos con SageMaker"""

    try:
        print(f"Evento recibido: {event}")

        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)

        algorithm = body.get("algorithm")
        degree_id = body.get("degreeId", "2491")
        config = body.get("config", {})

        if not algorithm:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "El parámetro 'algorithm' es requerido"})
            }

        supported_algorithms = ["asb", "rf", "pm", "spm"]
        if algorithm not in supported_algorithms:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"Algoritmo no soportado: {algorithm}. Soportados: {supported_algorithms}"
                })
            }

        job_info = create_sagemaker_training_job(algorithm, degree_id, config)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Training job iniciado para {algorithm}",
                "algorithm": algorithm,
                "degree_id": degree_id,
                "job_name": job_info["TrainingJobName"],
                "job_arn": job_info["TrainingJobArn"],
                "status": job_info["Status"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        }

    except Exception as e:
        error_msg = f"Error iniciando training job: {str(e)}"
        print(error_msg)
        print(f"Traceback: {traceback.format_exc()}")

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
        }
