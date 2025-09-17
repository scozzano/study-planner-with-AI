import os
import sys
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional, Set

import boto3
from boto3.dynamodb.conditions import Key
import joblib

sys.path.append('/opt/ml/code')
try:
    from subjects import SUBJECT_CATEGORY, SUBJECT_REQUIREMENTS
except Exception:
    SUBJECT_CATEGORY = {}
    SUBJECT_REQUIREMENTS = {}


def ddb_table():
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    ddb = boto3.resource("dynamodb", region_name=region)
    table_name = os.environ.get("DDB_TABLE", "AdaProjectTable")
    return ddb.Table(table_name)

def get_student_item(student_id: int, degree_id: str):
    table = ddb_table()
    pk_value = f"DEGREE#{degree_id}"
    sk_value = f"STUDENTS#{student_id}"
    resp = table.get_item(Key={"PK": pk_value, "SK": sk_value})
    return resp.get("Item")


DATE_FORMAT = "%d/%m/%Y"
DATE_KEYS = ["date", "completedAt", "completeTimestamp"]

def parse_ddmmyyyy(value) -> Optional[datetime]:
    if value is None or not isinstance(value, str):
        return None
    s = value.strip()
    try:
        dt = datetime.strptime(s, DATE_FORMAT)
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def normalize_code(v: Any) -> str:
    return (str(v).strip().upper()) if v is not None else ""

def normalize_status(s: Dict[str, Any]) -> str:
    return str(s.get("status") or "").strip().upper()

def normalize_result_type(s: Dict[str, Any]) -> str:
    return str(s.get("result_type") or s.get("resultType") or s.get("type") or "").strip().upper()

def source_is_exam(s: Dict[str, Any]) -> bool:
    txt = str(s.get("result_source") or s.get("source") or "").strip().lower()
    return txt == "por examen" or txt == "examen" or ("exam" in txt)

def subject_sort_key(subject: Dict[str, Any]) -> Tuple[int, float]:
    parsed_dt: Optional[datetime] = None
    for dk in DATE_KEYS:
        if subject.get(dk) is not None:
            parsed_dt = parse_ddmmyyyy(subject[dk])
            if parsed_dt:
                break
    if parsed_dt:
        return (1, parsed_dt.timestamp())
    try:
        sem = subject.get("semester")
        semf = float(sem) if sem is not None else float("-inf")
    except Exception:
        semf = float("-inf")
    return (0, semf)


def dedupe_subjects(subjects_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for s in subjects_raw or []:
        code = normalize_code(s.get("code"))
        if not code or code == "NAN":
            continue
        grouped.setdefault(code, []).append(s)

    result: List[Dict[str, Any]] = []
    for code, group in grouped.items():
        attempts_count = sum(1 for x in group if source_is_exam(x))

        has_apr_dictado_T = any(
            normalize_status(x) == "APR"
            and str(x.get("result_source", "")).strip().lower() == "por dictado"
            and normalize_result_type(x) == "T"
            for x in group
        )

        for x in group:
            status = normalize_status(x)
            result_type = normalize_result_type(x)
            result_source = str(x.get("result_source", "")).lower().strip()

            if status in ["REV", "RLI"]:
                continue

            if has_apr_dictado_T and status == "APR" and result_source == "por dictado" and result_type == "P":
                continue

            chosen_out = dict(x)
            chosen_out["attempts"] = attempts_count
            result.append(chosen_out)

    return result

def term_key_from_semester_or_date(s: Dict[str, Any]) -> Tuple[int, int]:
    for dk in DATE_KEYS:
        if s.get(dk) is not None:
            dt = parse_ddmmyyyy(s[dk])
            if dt:
                half = 1 if dt.month <= 6 else 2
                return (dt.year, half)
    try:
        sem_val = s.get("semester")
        sem_int = 1 if sem_val is None else int(round(float(sem_val)))
    except Exception:
        sem_int = 1
    return (0, sem_int)

def assign_terms(deduped_subjects: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    semesters_seen: Set[int] = set()
    for s in deduped_subjects:
        try:
            v = s.get("semester")
            if v is not None:
                semesters_seen.add(int(round(float(v))))
        except Exception:
            pass

    terms: Dict[int, List[str]] = {}
    if len(semesters_seen) >= 2:
        for s in deduped_subjects:
            c = normalize_code(s.get("code"))
            if not c or c == "NAN":
                continue
            try:
                sem = s.get("semester", 1)
                semi = 1 if sem is None else int(round(float(sem)))
            except Exception:
                semi = 1
            terms.setdefault(semi, []).append(c)
        return terms

    bucket: Dict[Tuple[int,int], List[str]] = {}
    for s in deduped_subjects:
        c = normalize_code(s.get("code"))
        if not c or c == "NAN":
            continue
        key = term_key_from_semester_or_date(s)
        bucket.setdefault(key, []).append(c)
    for idx, key in enumerate(sorted(bucket.keys()), start=1):
        terms[idx] = bucket[key]
    return terms


def load_model(model_dir: str = "/opt/ml/model") -> Dict[str, Any]:
    model_path = os.path.join(model_dir, "model.joblib")
    model = joblib.load(model_path)
    metadata_path = os.path.join(model_dir, "metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    return {"model": model, "metadata": metadata}


def build_target_terms_from_dynamo(student_id: int,
                                   degree_id: str,
                                   statuses_ok: Optional[Set[str]],
                                   grade_min_100: float) -> List[List[str]]:
    item = get_student_item(student_id, degree_id)
    if not item or "subjects" not in item:
        return []

    deduped = dedupe_subjects(item.get("subjects", []) or [])
    terms_map = assign_terms(deduped)

    filtered_terms: Dict[int, List[str]] = {}
    for term_idx in sorted(terms_map.keys()):
        for code in sorted(terms_map[term_idx]):
            subj = next((s for s in deduped if normalize_code(s.get("code")) == code), None)
            if not subj:
                continue
            status = normalize_status(subj)
            if statuses_ok is not None and status not in statuses_ok:
                continue
            try:
                grade = float(subj.get("grade", 0.0))
            except Exception:
                grade = 0.0
            if grade < grade_min_100:
                continue
            filtered_terms.setdefault(term_idx, []).append(code)

    if not filtered_terms:
        return []

    ordered = [sorted(filtered_terms[k]) for k in sorted(filtered_terms.keys())]
    ordered = [t for t in ordered if t]
    return ordered


def pattern_occurs_and_end_index(pattern: List[str], seq_terms: List[List[str]]) -> Optional[int]:
    if not pattern:
        return -1
    start = 0
    for p in pattern:
        found = False
        for term_idx in range(start, len(seq_terms)):
            if p in seq_terms[term_idx]:
                start = term_idx + 1
                found = True
                break
        if not found:
            return None
    return start - 1


def recommend_spm_for_terms(target_terms: List[List[str]],
                            patterns: List[Dict[str, Any]],
                            top_k: int = 5) -> Tuple[int, List[Dict[str, float]]]:
    completed = {c for term in target_terms for c in term}

    best_len = 0
    bucket: List[Dict[str, Any]] = []

    for p in patterns:
        pat = [x[0] for x in p.get("sequence", [])]
        if not pat:
            continue
        end_idx = pattern_occurs_and_end_index(pat, target_terms)
        if end_idx is None:
            continue
        L = len(pat)
        if L > best_len:
            best_len = L
            bucket = [p]
        elif L == best_len:
            bucket.append(p)

    if best_len == 0 or not bucket:
        return 0, []

    candidates: Dict[str, Dict[str, float]] = {}
    for p in bucket:
        for nxt in p.get("next_items", []):
            subj = nxt.get("subject")
            if not subj or subj in completed:
                continue
            support_next = float(nxt.get("support_next", 0.0))
            confidence = float(nxt.get("confidence", 0.0))
            score = confidence * support_next
            agg = candidates.setdefault(subj, {"score": 0.0, "confidence_max": 0.0, "support_next_max": 0.0})
            agg["score"] += score
            if confidence > agg["confidence_max"]:
                agg["confidence_max"] = confidence
            if support_next > agg["support_next_max"]:
                agg["support_next_max"] = support_next

    ranked = [
        {
            "subject": subj,
            "score": round(agg["score"], 6),
            "confidence_max": round(agg["confidence_max"], 6),
            "support_next_max": round(agg["support_next_max"], 6),
        }
        for subj, agg in candidates.items()
    ]
    ranked.sort(key=lambda r: (-r["score"], -r["confidence_max"], -r["support_next_max"], r["subject"]))
    return best_len, ranked[:top_k]


def predict_spm(input_data: Dict[str, Any], model_dict: Dict[str, Any]) -> Dict[str, Any]:
    model = model_dict["model"]
    params = model.get("params", {})

    degree_id = str(
        input_data.get("degree_id")
        or input_data.get("degreeId")
        or model.get("degree_id")
        or os.environ.get("DEGREE_ID", "2491")
    )
    top_k_default = int(params.get("top_k", 5))
    k = int(input_data.get("k", top_k_default))
    min_matched_len = int(input_data.get("min_matched_len", 1))

    grade_min_for_spm = float(params.get("grade_min_for_spm", 86.0))
    statuses_ok_list = params.get("statuses_ok_for_spm", ["APR"]) or ["APR"]
    statuses_ok = set(s.strip().upper() for s in statuses_ok_list)

    student_id = input_data.get("student_id") or input_data.get("studentId")
    if student_id is None:
        return {"error": "Falta student_id o studentId"}
    try:
        student_id_int = int(student_id)
    except Exception:
        return {"error": "student_id inválido"}

    target_terms = build_target_terms_from_dynamo(student_id_int, degree_id, statuses_ok, grade_min_for_spm)
    if not target_terms:
        return {"error": "El estudiante no tiene materias válidas (tras filtro de estado/nota) para analizar."}

    patterns = model.get("patterns", [])
    if not patterns:
        return {"error": "El modelo SPM no contiene patrones."}

    best_len, prelim = recommend_spm_for_terms(target_terms, patterns, top_k=max(k, 20))

    if best_len < min_matched_len or not prelim:
        return {
            "algorithm": "spm",
            "model_version": model_dict.get("metadata", {}).get("export_time",
                             datetime.now(timezone.utc).isoformat()),
            "degree_id": degree_id,
            "student_id": student_id,
            "params": {
                "k": k,
                "min_matched_len": min_matched_len,
                "grade_min_for_spm": grade_min_for_spm,
                "statuses_ok_for_spm": list(statuses_ok)
            },
            "matched_pattern_length": best_len,
            "recommendations": [],
            "message": "No hay patrones con match completo suficiente o no hay candidatos."
        }

    course_stats: Dict[str, Dict[str, float]] = model.get("course_stats", {}) or {}
    recommendations = []
    for r in prelim:
        subj = r["subject"]
        stats = course_stats.get(subj, {})
        expected_gpa = float(stats.get("avg_grade", 0.0))
        adoption = float(stats.get("adoption_rate", 0.0))
        key_course = subj in SUBJECT_REQUIREMENTS

        recommendations.append({
            "subject": subj,
            "score": r["score"],
            "confidence_max": r["confidence_max"],
            "support_next_max": r["support_next_max"],
            "expected_avg_gpa": round(expected_gpa, 3),
            "adoption_rate": round(adoption, 6),
            "key_course": key_course
        })

    recommendations.sort(
        key=lambda x: (
            not x["key_course"],
            -x["score"],
            -x["expected_avg_gpa"],
            -x["adoption_rate"],
            -x["confidence_max"],
            -x["support_next_max"],
            x["subject"]
        )
    )
    topk = recommendations[:k]

    for r in topk:
        reasons = [f"prefijo más largo coincidente = {best_len} (match completo)"]
        if r["key_course"]:
            reasons.append("materia clave (prerrequisito)")
        if r["confidence_max"] > 0:
            reasons.append(f"confidence_max {r['confidence_max']}")
        if r["support_next_max"] > 0:
            reasons.append(f"support_next_max {r['support_next_max']}")
        if r["expected_avg_gpa"] > 0:
            reasons.append(f"promedio histórico esperado GPA {r['expected_avg_gpa']}")
        r["reason"] = "; ".join(reasons)

    return {
        "algorithm": "spm",
        "model_version": model_dict.get("metadata", {}).get("export_time",
                         datetime.now(timezone.utc).isoformat()),
        "degree_id": degree_id,
        "student_id": student_id,
        "params": {
            "k": k,
            "min_matched_len": min_matched_len,
            "grade_min_for_spm": grade_min_for_spm,
            "statuses_ok_for_spm": list(statuses_ok)
        },
        "matched_pattern_length": best_len,
        "recommendations": topk
    }


if __name__ == "__main__":
    try:
        input_str = sys.stdin.read().strip()
        if input_str:
            inp = json.loads(input_str)
            model_dict = load_model("/opt/ml/model")
            out = predict_spm(inp, model_dict)
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "Proveer JSON por STDIN"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": f"Fallo en main: {e}"}, ensure_ascii=False))