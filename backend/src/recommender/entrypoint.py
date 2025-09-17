import os
import sys
import subprocess
import json

def main():
    print(f"Argumentos: {sys.argv}")
    print(f"Variables de entorno ALGORITHM: {os.environ.get('ALGORITHM', 'NO_ENCONTRADA')}")

    algorithm = os.environ.get('ALGORITHM', '').lower()
    print(f"Algoritmo desde variable de entorno: {algorithm}")

    try:
        hyperparams_path = '/opt/ml/input/config/hyperparameters.json'
        if os.path.exists(hyperparams_path):
            print("Leyendo hyperparameters.json...")
            with open(hyperparams_path, 'r') as f:
                hyperparams = json.load(f)
                print(f"Hyperparameters encontrados: {hyperparams}")
                if not algorithm:
                    algorithm = hyperparams.get('ALGORITHM', '').lower()
                    print(f"Algoritmo desde hyperparameters: {algorithm}")
        else:
            print("Archivo hyperparameters.json no encontrado, usando variable de entorno")
    except Exception as e:
        print(f"Error leyendo hyperparameters.json: {e}")
        print("Continuando con variable de entorno")

    print(f"Algoritmo final: '{algorithm}'")
    print("=== FIN DEBUGGING ===")

    if algorithm in ['rf', 'pm', 'spm']:
        print(f"Iniciando entrenamiento de {algorithm.upper()}...")

        if algorithm == 'rf':
            script = 'rf_train.py'
        elif algorithm == 'pm':
            script = 'pm_train.py'
        elif algorithm == 'spm':
            script = 'spm_train.py'
        else:
            print(f"Algoritmo {algorithm} no soportado")
            sys.exit(1)

        try:
            result = subprocess.run([sys.executable, script], check=True)
            print(f"Entrenamiento de {algorithm.upper()} completado exitosamente")
            sys.exit(result.returncode)
        except subprocess.CalledProcessError as e:
            print(f"Error en entrenamiento de {algorithm.upper()}: {e}")
            sys.exit(e.returncode)
        except Exception as e:
            print(f"Error ejecutando {script}: {e}")
            sys.exit(1)

    else:
        print("Iniciando servidor de inferencia...")

        if len(sys.argv) > 1 and sys.argv[1] == 'serve':
            try:
                result = subprocess.run([sys.executable, 'inference.py'] + sys.argv[1:], check=True)
                sys.exit(result.returncode)
            except subprocess.CalledProcessError as e:
                print(f"Error en servidor de inferencia: {e}")
                sys.exit(e.returncode)
            except Exception as e:
                print(f"Error ejecutando inference.py: {e}")
                sys.exit(1)
        else:
            print("Comando no reconocido. Use 'serve' para iniciar el servidor.")
            sys.exit(1)

if __name__ == "__main__":
    main()
