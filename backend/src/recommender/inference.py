import os
import json
import joblib
import sys
import argparse
from flask import Flask, request, jsonify

sys.path.append('/opt/ml/code')

from rf_inference import predict_rf
from pm_inference import predict_pm
from spm_inference import predict_spm


def get_model(model_dir):
    metadata_path = os.path.join(model_dir, 'metadata.json')

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    model_path = os.path.join(model_dir, 'model.joblib')
    model = joblib.load(model_path)

    return {'model': model, 'metadata': metadata}

def get_prediction(input_data, model_dict):
    algorithm = input_data.get('algorithm', '').lower()

    if algorithm == 'rf':
        return predict_rf(input_data, model_dict)
    elif algorithm == 'pm':
        return predict_pm(input_data, model_dict)
    elif algorithm == 'spm':
        return predict_spm(input_data, model_dict)
    else:
        raise ValueError(f"Algoritmo '{algorithm}' no soportado")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=str, default='/opt/ml/model')
    parser.add_argument('--model-name', type=str, default='model')
    args, unknown_args = parser.parse_known_args()

    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        print("Iniciando servidor SageMaker...")
        model_dict = get_model(args.model_dir)
        print("Modelo cargado exitosamente")
        print(f"Algoritmo: {model_dict['metadata']['algorithm']}")
        print(f"Tipo de modelo: {model_dict['metadata']['model_type']}")
        app = Flask(__name__)

        @app.route('/ping', methods=['GET'])
        def ping():
            return jsonify({'status': 'healthy'})

        @app.route('/invocations', methods=['POST'])
        def invoke():
            try:
                input_data = request.get_json()
                if not input_data:
                    return jsonify({'error': 'No se proporcionaron datos'}), 400
                prediction = get_prediction(input_data, model_dict)
                return jsonify(prediction)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        print("Iniciando servidor en puerto 8080...")
        app.run(host='0.0.0.0', port=8080, debug=False)
    else:
        print("Comando no reconocido. Use 'serve' para iniciar el servidor.")
        sys.exit(1)
