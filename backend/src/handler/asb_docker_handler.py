import json
import os
import logging
from src.recommender.asb_recommender import main

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})

        degree_id = body.get('degree_id', '2491')
        sample_size = body.get('sample_size')
        analysis_config = body.get('analysis_config', {})

        logger.info(f"Procesando request ASB para degree_id: {degree_id}")
        logger.info(f"Configuración recibida: {analysis_config}")

        config = {
            'label': analysis_config.get('label', 'Overall GPA'),
            'GPA_grades': 'passed+failed last attempt',
            'is_binary_label': analysis_config.get('is_binary_label', False),
            'model': 'DT',
            'max_depth': analysis_config.get('max_depth', 3),
            'is_atomic': analysis_config.get('is_atomic', True),
            'is_pm': analysis_config.get('is_pm', False),
            'index_type': analysis_config.get('index_type', 'fachsemester'),
            'feature': analysis_config.get('feature', 'Course-Semester'),
            'combinations': analysis_config.get('combinations', ['behav']),
            'label_index': analysis_config.get('label_index', None),
            'course': analysis_config.get('course', None)
        }

        logger.info(f"Configuración ASB: {config}")
        logger.info("Iniciando procesamiento ASB con main...")

        try:
            table_name = os.environ.get('TABLE_NAME', 'AdaProjectTable')
            score_dict, DT_names, figures, parsed, error_msg = main(
                degree_id=degree_id,
                table_name=table_name,
                sample_size=sample_size,
                config=config
            )
            logger.info(f"Procesamiento ASB completado. Error: {error_msg}")
        except Exception as e:
            logger.error(f"Error en procesamiento ASB: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            score_dict, DT_names, figures, parsed, error_msg = {}, [], [], [], f"Error en procesamiento ASB: {str(e)}"

        response_data = {
            'score_dict': score_dict,
            'DT_names': DT_names,
            'figures': figures,
            'parsed': parsed,
            'error_msg': error_msg
        }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data, default=str)
        }

    except Exception as e:
        logger.error(f"Error en lambda_handler: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'score_dict': {},
                'DT_names': [],
                'figures': [],
                'parsed': [],
                'error_msg': f'Error interno del servidor: {str(e)}'
            })
        }




