import fitz
import re
import logging
from datetime import datetime
from typing import List, Dict, Any
from src.model.records.student_subject_record import StudentSubjectRecord
from src.model.records.student_record import StudentRecord

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def clean_subject_name(name: str) -> str:
    if not name:
        return ""

    name = re.sub(r"√\s*", "", name)

    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

    name = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", name)
    name = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", name)

    common_words = [
        "Programacion", "Algoritmos", "Estructuras", "Datos", "Bases", "Sistemas",
        "Ingenieria", "Software", "Computacion", "Matematicas", "Fisica", "Quimica",
        "Estadistica", "Probabilidad", "Calculo", "Algebra", "Geometria", "Analisis"
    ]

    for word in common_words:
        pattern = f"({word})([A-Z][a-z]+)"
        name = re.sub(pattern, r"\1 \2", name)

    name = re.sub(r"\s{2,}", " ", name)

    name = name.strip()

    return name


def extract_schooling_data(pdf_bytes: bytes) -> StudentRecord:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.page_count == 0:
            raise ValueError("El PDF no contiene páginas válidas")

        full_text = "\n".join([page.get_text() for page in doc])
        if not full_text.strip():
            raise ValueError("No se pudo extraer texto del PDF")

        lines = full_text.splitlines()
        doc.close()
    except Exception as e:
        logger.error(f"Error al procesar PDF: {str(e)}")
        raise ValueError(f"Error al procesar PDF: {str(e)}")

    name_match = re.search(r"Estudiante:\s*(.*?)\s*\(", full_text)
    document_match = re.search(r"Documento:\s*(\S+)", full_text)
    student_id_match = re.search(r"Estudiante:.*\((\d+)\)", full_text)
    title_match = re.search(r"Título:\s*(.*?)\s*\((\d+)\)", full_text)
    plan_match = re.search(r"Plan:\s*(\d+)", full_text)
    start_date_match = re.search(r"Comienzo:\s*(\d{2}/\d{2}/\d{4})", full_text)
    graduation_match = re.search(r"Fecha de graduación:\s*(\S+)", full_text)

    subjects_required_match = re.search(r"Materias requeridas:\s*(\d+)", full_text)
    subjects_obtained_match = re.search(r"Materias obtenidas:\s*(\d+)", full_text)
    failed_subjects_match = re.search(r"Reprobaciones:\s*(\d+)", full_text)
    avg_grade_match = re.search(r"Promedio de calificaciones:\s*(\d+)%", full_text)
    avg_approved_match = re.search(r"Promedio de calificaciones de materias aprobadas:\s*(\d+)%", full_text)

    subjects: List[StudentSubjectRecord] = []
    current_semester = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        semester_match = re.match(r"Semestre\s+(\d+(?:\.\d)?)", line)
        if semester_match:
            current_semester = semester_match.group(1)
            i += 1
            continue

        if line.startswith("√"):
            name_line = line
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            third_line = lines[i + 2].strip() if i + 2 < len(lines) else ""

            code_match = re.search(r"\((\d+)\)", name_line)
            if code_match and re.match(r"\d{2}/\d{2}/\d{4}", next_line) and "Aprobada" in third_line:
                raw_name = name_line.split('(')[0].strip()
                name = clean_subject_name(raw_name)
                code = code_match.group(1)
                try:
                    date = datetime.strptime(next_line, "%d/%m/%Y").date().isoformat()
                except ValueError:
                    logger.warning(f"Fecha inválida encontrada: {next_line}")
                    date = None
                grade_match = re.search(r"(\d+)%", third_line)
                grade = int(grade_match.group(1)) if grade_match else None
                if current_semester is None:
                    logger.warning(f"Materia sin semestre: {name} ({code})")
                    current_semester = "0"
                subjects.append(StudentSubjectRecord(
                    code=code,
                    name=name,
                    semester=current_semester,
                    date=date,
                    status="APR",
                    grade=grade
                ))
                i += 3
                continue

            next_name_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            code_match = re.search(r"\((\d+)\)", next_name_line)
            if code_match and (i + 3 < len(lines)):
                raw_name = next_name_line.split('(')[0].strip()
                name = clean_subject_name(raw_name)
                code = code_match.group(1)
                date_line = lines[i + 2].strip()
                grade_line = lines[i + 3].strip()
                try:
                    date = datetime.strptime(date_line, "%d/%m/%Y").date().isoformat() if re.match(r"\d{2}/\d{2}/\d{4}", date_line) else None
                except ValueError:
                    logger.warning(f"Fecha inválida encontrada: {date_line}")
                    date = None
                grade_match = re.search(r"(\d+)%", grade_line)
                grade = int(grade_match.group(1)) if grade_match else None
                if current_semester is None:
                    logger.warning(f"Materia sin semestre: {name} ({code})")
                    current_semester = "0"
                subjects.append(StudentSubjectRecord(
                    code=code,
                    name=name,
                    semester=current_semester,
                    date=date,
                    status="APR",
                    grade=grade
                ))
                i += 4
                continue

        code_match = re.search(r"\((\d+)\)", line)
        if code_match:
            name_line = line
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

            if next_line.startswith("------------"):
                raw_name = name_line.split('(')[0].strip()
                name = clean_subject_name(raw_name)
                code = code_match.group(1)
                subjects.append(StudentSubjectRecord(
                    code=code,
                    name=name,
                    semester=current_semester if current_semester else "0",
                    date=None,
                    status="NAPR",
                    grade=None
                ))
                i += 2
                continue

        i += 1

    logger.info(f"Materias extraídas: {len(subjects)}")

    if not student_id_match:
        raise ValueError("No se pudo extraer el ID del estudiante del PDF")
    if not name_match:
        raise ValueError("No se pudo extraer el nombre del estudiante del PDF")
    if not title_match:
        raise ValueError("No se pudo extraer información del título/carrera del PDF")

    try:
        return StudentRecord(
            id=student_id_match.group(1),
            name=name_match.group(1).strip(),
            document=document_match.group(1) if document_match else "N/A",
            enrollment_number=student_id_match.group(1),
            title=title_match.group(1).strip(),
            degreeId=title_match.group(2),
            plan=plan_match.group(1) if plan_match else "N/A",
            start_date=start_date_match.group(1) if start_date_match else "N/A",
            graduation_date=None if not graduation_match or graduation_match.group(1) == "---------" else graduation_match.group(1),
            average_grade=int(avg_grade_match.group(1)) if avg_grade_match else 0,
            average_approved_grade=int(avg_approved_match.group(1)) if avg_approved_match else 0,
            subjects_required=int(subjects_required_match.group(1)) if subjects_required_match else 0,
            subjects_obtained=int(subjects_obtained_match.group(1)) if subjects_obtained_match else 0,
            failed_subjects=int(failed_subjects_match.group(1)) if failed_subjects_match else 0,
            subjects=subjects
        )
    except Exception as e:
        logger.error(f"Error al crear StudentRecord: {str(e)}")
        raise ValueError(f"Error al crear registro del estudiante: {str(e)}")
