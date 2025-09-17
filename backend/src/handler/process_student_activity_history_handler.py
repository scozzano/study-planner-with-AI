import json
import logging

from botocore.exceptions import ClientError

from src.model.records.student_record import StudentRecord
from src.model.records.student_subject_record import StudentSubjectRecord
from src.repository.students_repository import DynamoStudentsRepository
from src.repository.university_repository import DynamoUniversityRepository
from src.services.student_service import StudentService
from src.services.university_service import UniversityService
from src.support.utils.excel_processor import ExcelProcessor

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _safe_int(v, default=0):
    try:
        if v is None or str(v).strip() == "":
            return default
        return int(str(v).strip())
    except Exception:
        return default



def lambda_handler(event, context):
    university_repository = DynamoUniversityRepository()
    university_services = UniversityService(university_repository)
    students_repository = DynamoStudentsRepository()
    students_services = StudentService(students_repository)

    DEGREE_ID = 2491


    try:
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        logger.info(f"Procesando archivo: s3://{bucket}/{key}")

        degree_data = university_services.get_university_degree(DEGREE_ID)
        subjects_required = len(degree_data.subjects)


        wb = ExcelProcessor.get_workbook_from_s3(bucket, key)
        activities_by_student = ExcelProcessor.process_activities_sheet(wb, sheet_name="activities")
        globals_info = ExcelProcessor.process_global_info_sheet(wb, sheet_name="global_info")

        errores = []

        for student_id, info in globals_info.items():
            activities = activities_by_student.get(student_id, [])

            subjects = []
            total_grade = 0
            total_approved_grade = 0
            count_grade = 0
            count_approved = 0
            failed_subjects = 0
            pending_subjects = 0

            for act in activities:
                credit_date = act.get("Fecha Obtención Credito", "")
                start_date = info.get("start_date", "")

                semester = (
                    ExcelProcessor.compute_semester(start_date, credit_date)
                    if start_date and credit_date else "0"
                )

                status_raw = (act.get("RESULTADO_CTA_CTE_ACD") or "").strip()
                status_upper = status_raw.upper()

                result_type_raw = (act.get("TIPO_CREDITO_CTA_CTE_ACD") or "").strip()
                result_type_upper = result_type_raw.upper()

                grade = _safe_int(act.get("CALIFICACION_CTA_CTE_ACD"), default=0)

                total_grade += grade
                count_grade += 1

                if status_upper == "APR" and result_type_upper == "T":
                    total_approved_grade += grade
                    count_approved += 1

                elif status_upper == "APR" and result_type_upper == "P":
                    pending_subjects += 1

                elif status_upper in {"ELI", "NSP", "ABN", "AUS"}:
                    failed_subjects += 1

                subjects.append(
                    StudentSubjectRecord(
                        code=act.get("ID_MATERIA"),
                        name=act.get("DESCRIPCION_MATERIA"),
                        semester=semester,
                        date=credit_date,
                        status=status_raw,
                        grade=grade,
                        result_type=result_type_raw,
                        result_source=act.get("TIPO_DE_OBTENCION")
                    )
                )

            average_grade = int(total_grade / count_grade) if count_grade else 0
            average_approved_grade = int(total_approved_grade / count_approved) if count_approved else 0
            subjects_obtained = count_approved

            student_record = StudentRecord(
                id=student_id,
                name="N/A",
                document="N/A",
                enrollment_number=student_id,
                title=degree_data.degree,
                degreeId=str(DEGREE_ID),
                plan=degree_data.plan,
                start_date=info.get("start_date", ""),
                graduation_date=info.get("graduation_date", ""),
                average_grade=average_grade,
                average_approved_grade=average_approved_grade,
                subjects_required=subjects_required,
                subjects_obtained=subjects_obtained,
                failed_subjects=failed_subjects,
                subjects=subjects
            )

            try:
                students_services.save_schooling(student_record)
                if pending_subjects:
                    logger.info(f"Alumno {student_id}: {pending_subjects} materias pendientes (APR + P)")
            except ClientError as e:
                logger.error(f"Error escribiendo registro {student_id}: {e}")
                errores.append(student_id)

        logger.info(
            f"Guardados {len(globals_info) - len(errores)} registros correctamente. "
            f"Errores en: {errores}"
        )

        return {
            "statusCode": 200 if not errores else 207,
            "body": json.dumps({
                "message": "Datos procesados",
                "errores": errores
            })
        }

    except KeyError as e:
        logger.error(f"Falta clave en evento S3: {e}")
        return {"statusCode": 400, "body": json.dumps({"error": f"Evento inválido: {e}"})}
    except ClientError as e:
        logger.error(f"Error en interacción con AWS: {e}")
        return {"statusCode": 502, "body": json.dumps({"error": "Error AWS interno"})}
    except Exception as e:
        logger.critical(f"Error inesperado: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": "Error interno del servidor"})}
