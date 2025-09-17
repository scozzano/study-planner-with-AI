import os
import shutil
import sys

def setup_environment():

    code_dir = "/opt/ml/code"

    os.makedirs(code_dir, exist_ok=True)

    files_to_copy = [
        "asb_train.py",
        "rf_train.py",
        "pm_train.py",
        "spm_train.py",
        "subjects.py"
    ]o



    current_dir = os.path.dirname(os.path.abspath(__file__))

    for filename in files_to_copy:
        source_path = os.path.join(current_dir, filename)
        dest_path = os.path.join(code_dir, filename)

        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"Copiado: {filename}")
        else:
            print(f"Archivo no encontrado: {filename}")

    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)

    print("Setup completado")

if __name__ == "__main__":
    setup_environment()
