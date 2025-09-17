import os
import sys
import json
import boto3
import joblib
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Set, Optional

def ddb_table():
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    ddb = boto3.resource("dynamodb", region_name=region)
    table_name = os.getenv("DDB_TABLE", "AdaProjectTable")
    return ddb.Table(table_name)

def get_student_item(student_id: int, degree_id: str):
    table = ddb_table()
    pk_value = f"DEGREE#{degree_id}"
    sk_value = f"STUDENTS#{student_id}"
    resp = table.get_item(Key={"PK": pk_value, "SK": sk_value})
    return resp.get("Item")


def grade_100_to_gpa4(grade_0_100: float) -> float:
    try:
        v = float(grade_0_100)
    except Exception:
        return 0.0
    g = (v / 100.0) * 4.0
    return max(0.0, min(4.0, g))

def gpa4_to_grade_100(gpa: float) -> float:
    try:
        v = (float(gpa) / 4.0) * 100.0
    except Exception:
        v = 0.0
    return max(0.0, min(100.0, v))


DATE_FORMAT = "%d/%m/%Y"
DATE_KEYS = ["date", "completedAt", "completeTimestamp"]

def parse_date(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        try:
            dt = datetime.strptime(s, DATE_FORMAT)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None

def subject_sort_key(subject: Dict[str, Any]) -> Tuple[int, float]:
    parsed_dt: Optional[datetime] = None
    for date_key in DATE_KEYS:
        if date_key in subject and subject[date_key] is not None:
            parsed_dt = parse_date(subject[date_key])
            if parsed_dt:
                break
    if parsed_dt is not None:
        return (1, parsed_dt.timestamp())
    sem_val = subject.get("semester")
    try:
        sem_num = float(sem_val) if sem_val is not None else float("-inf")
    except Exception:
        sem_num = float("-inf")
    return (0, sem_num)

def normalize_code(value: Any) -> str:
    return (str(value).strip().upper()) if value is not None else ""

def normalize_result_type(subject: Dict[str, Any]) -> str:
    return str(subject.get("result_type") or subject.get("resultType") or subject.get("type") or "").strip().upper()

def normalize_status(subject: Dict[str, Any]) -> str:
    return str(subject.get("status") or "").strip().upper()

def source_is_exam(subject: Dict[str, Any]) -> bool:
    src = str(subject.get("result_source") or subject.get("source") or "").strip().lower()
    return (src == "por examen") or (src == "examen") or ("exam" in src)

def dedupe_subjects(subjects_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for s in subjects_raw or []:
        code = normalize_code(s.get("code"))
        if not code or code == "NAN":
            continue
        grouped.setdefault(code, []).append(s)

    result: List[Dict[str, Any]] = []
    for code, group in grouped.items():
        attempts_count = sum(1 for e in group if source_is_exam(e))

        has_apr_dictado_T = any(
            normalize_status(e) == "APR"
            and str(e.get("result_source", "")).strip().lower() == "por dictado"
            and normalize_result_type(e) == "T"
            for e in group
        )

        for e in group:
            status = normalize_status(e)
            result_type = normalize_result_type(e)
            result_source = str(e.get("result_source", "")).lower().strip()

            if status in ["REV", "RLI"]:
                continue

            if has_apr_dictado_T and status == "APR" and result_source == "por dictado" and result_type == "P":
                continue

            chosen_out = dict(e)
            chosen_out["attempts"] = attempts_count
            result.append(chosen_out)

    return result


def term_index_from_semester_or_date(subject: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    for date_key in DATE_KEYS:
        if date_key in subject and subject[date_key] is not None:
            dt = parse_date(subject[date_key])
            if dt:
                half = 1 if dt.month <= 6 else 2
                return (dt.year, half)
    try:
        sem_val = subject.get("semester", None)
        if sem_val is None:
            return None
        sem_int = int(round(float(sem_val)))
        return (0, sem_int)
    except Exception:
        return None

def assign_terms_for_student(deduped_subjects: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    semesters_seen: Set[int] = set()
    for s in deduped_subjects:
        try:
            sem_val = s.get("semester", None)
            if sem_val is not None:
                semesters_seen.add(int(round(float(sem_val))))
        except Exception:
            pass

    terms: Dict[int, List[str]] = {}

    if len(semesters_seen) >= 2:
        for s in deduped_subjects:
            code = str(s.get("code", "")).strip()
            if not code or code.lower() == "nan":
                continue
            try:
                sem_val = s.get("semester", 1)
                sem_int = 1 if sem_val is None else int(round(float(sem_val)))
            except Exception:
                sem_int = 1
            terms.setdefault(sem_int, []).append(code)
        return terms

    code_by_termkey: Dict[Tuple[int, int], List[str]] = {}
    for s in deduped_subjects:
        code = str(s.get("code", "")).strip()
        if not code or code.lower() == "nan":
            continue
        key = term_index_from_semester_or_date(s) or (0, 1)
        code_by_termkey.setdefault(key, []).append(code)

    for idx, key in enumerate(sorted(code_by_termkey.keys()), start=1):
        terms[idx] = code_by_termkey[key]

    return terms


def build_target_terms(item: Dict[str, Any]) -> List[List[str]]:
    subjects_raw = item.get("subjects", []) or []
    deduped = dedupe_subjects(subjects_raw)
    all_terms_map = assign_terms_for_student(deduped)

    subjects_by_term: Dict[int, List[str]] = {}
    for term_idx in sorted(all_terms_map.keys()):
        for code in sorted(all_terms_map[term_idx]):
            subj = next((s for s in deduped if str(s.get("code", "")).strip() == code), None)
            if not subj:
                continue
            status = str(subj.get("status", "")).upper() if subj.get("status") else ""
            if status != "APR":
                continue
            subjects_by_term.setdefault(term_idx, []).append(code)

    return [sorted(subjects_by_term[k]) for k in sorted(subjects_by_term.keys())]


REL_DIRECT = "->"
REL_INDIRECT = "->>"
REL_REV_DIRECT = "<-"
REL_REV_INDIRECT = "<<-"
REL_SAME = "||"
REL_OTHER = "#"

def index_terms_by_course(sequence_of_terms: List[List[str]]) -> Dict[str, Tuple[int, int]]:
    index: Dict[str, Tuple[int, int]] = {}
    for term_index, term_courses in enumerate(sequence_of_terms):
        for position_in_term, course_code in enumerate(term_courses):
            index[course_code] = (term_index, position_in_term)
    return index

def relation_between_courses(a: str, b: str, index_map: Dict[str, Tuple[int, int]]) -> str:
    if a == b or a not in index_map or b not in index_map:
        return REL_OTHER

    term_a, _ = index_map[a]
    term_b, _ = index_map[b]

    if term_a == term_b:
        return REL_SAME
    if term_b == term_a + 1:
        return REL_DIRECT
    if term_b > term_a + 1:
        return REL_INDIRECT
    if term_a == term_b + 1:
        return REL_REV_DIRECT
    if term_a > term_b + 1:
        return REL_REV_INDIRECT
    return REL_OTHER

def build_footprint_map(sequence_of_terms: List[List[str]], universe: Set[str]) -> Dict[Tuple[str, str], str]:
    index_map = index_terms_by_course(sequence_of_terms)
    footprint: Dict[Tuple[str, str], str] = {}
    for course_a in universe:
        for course_b in universe:
            if course_a == course_b:
                continue
            footprint[(course_a, course_b)] = relation_between_courses(course_a, course_b, index_map)
    return footprint

def similarity_of_footprints(seq_a: List[List[str]], seq_b: List[List[str]]) -> float:
    length = min(len(seq_a), len(seq_b))
    if length == 0:
        return 0.0

    truncated_a = seq_a[:length]
    truncated_b = seq_b[:length]

    universe: Set[str] = set([c for term in truncated_a for c in term] + [c for term in truncated_b for c in term])
    if len(universe) <= 1:
        return 1.0

    fp_a = build_footprint_map(truncated_a, universe)
    fp_b = build_footprint_map(truncated_b, universe)

    total_pairs = len(fp_a)
    differences = sum(1 for key, value in fp_a.items() if value != fp_b.get(key))
    return 1.0 - (differences / max(1, total_pairs))


def candidates_from_peer(peer_terms: List[List[str]], target_last_term: int) -> List[str]:
    idx = target_last_term
    if idx < len(peer_terms):
        return list(peer_terms[idx])
    return []

def rank_candidates(candidates: Dict[str, Dict[str, Any]],
                    course_stats: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    ranked = []
    for code, agg in candidates.items():
        stat = course_stats.get(code, {})
        avg_gpa = float(stat.get("avg_grade", 0.0))
        support = int(agg.get("support", 0))
        sim_sum = float(agg.get("sim_sum", 0.0))
        score = sim_sum * (1.0 + (avg_gpa / 4.0))
        ranked.append({
            "subject": code,
            "support": support,
            "avg_grade_gpa": round(avg_gpa, 3),
            "avg_grade_100": round(gpa4_to_grade_100(avg_gpa), 1),
            "adoption_rate": float(stat.get("adoption_rate", 0.0)),
            "score": round(score, 6),
        })
    ranked.sort(key=lambda r: (-r["score"], -r["support"], r["subject"]))
    return ranked

def load_model(model_dir: str = "/opt/ml/model") -> Dict[str, Any]:
    model_path = os.path.join(model_dir, "model.joblib")
    model = joblib.load(model_path)
    metadata_path = os.path.join(model_dir, "metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    return {"model": model, "metadata": metadata}

def predict_pm(input_data: Dict[str, Any], model_pack: Dict[str, Any]) -> Dict[str, Any]:
    model = model_pack["model"]
    model_params = model.get("params", {})
    degree_id = str(input_data.get("degree_id") or input_data.get("degreeId") or
                    model.get("degree_id", os.getenv("DEGREE_ID", "2491")))
    gpa_success_threshold = float(model_params.get("gpa_success_threshold", 3.6))
    similarity_threshold = float(model_params.get("similarity_threshold", 0.7))
    top_k_default = int(model_params.get("top_k", 5))

    try:
        k = int(input_data.get("k", top_k_default))
    except Exception:
        k = top_k_default
    try:
        min_sim = float(input_data.get("min_sim", similarity_threshold))
    except Exception:
        min_sim = similarity_threshold

    student_id = input_data.get("student_id") or input_data.get("studentId")
    if student_id is None:
        return {"error": "Falta student_id o studentId"}
    try:
        student_id = int(student_id)
    except Exception:
        return {"error": "student_id inválido"}

    item = get_student_item(student_id, degree_id)
    if not item or "subjects" not in item:
        return {"error": f"No se encontraron datos para el estudiante {student_id} / degree {degree_id}"}

    target_terms = build_target_terms(item)
    if not target_terms:
        return {"error": "El estudiante no tiene materias APR válidas para analizar."}

    successful_students = model.get("successful_students", [])
    if not successful_students:
        return {"error": f"No hay estudiantes exitosos en el modelo (gpa ≥ {gpa_success_threshold})"}

    L_target = len(target_terms)
    similar_peers = []
    for peer in successful_students:
        peer_terms = peer.get("subjects_by_term", [])
        if not peer_terms:
            continue
        sim = similarity_of_footprints(target_terms, peer_terms)
        if sim >= min_sim:
            similar_peers.append({
                "student_id": peer.get("student_id"),
                "gpa": float(peer.get("gpa", 0.0)),
                "sim": float(round(sim, 6)),
                "terms": peer_terms
            })
    similar_peers.sort(key=lambda x: x["sim"], reverse=True)

    completed_courses = set([c for term in target_terms for c in term])
    candidates: Dict[str, Dict[str, Any]] = {}
    for sp in similar_peers:
        for c in candidates_from_peer(sp["terms"], L_target):
            if c in completed_courses:
                continue
            agg = candidates.setdefault(c, {"support": 0, "sim_sum": 0.0})
            agg["support"] += 1
            agg["sim_sum"] += sp["sim"]

    if not candidates:
        return {
            "algorithm": "pm",
            "model_version": model_pack.get("metadata", {}).get("export_time",
                             datetime.now(timezone.utc).isoformat()),
            "degree_id": degree_id,
            "student_id": student_id,
            "params": {"k": k, "min_sim": min_sim, "gpa_success_threshold": gpa_success_threshold},
            "similar_peers": [{"student_id": s["student_id"], "sim": round(s["sim"], 4)} for s in similar_peers[:20]],
            "recommendations": [],
            "message": "No se encontraron candidatos (el próximo término de pares similares coincide con cursos ya completados)."
        }

    course_stats = model.get("course_stats", {})
    ranked = rank_candidates(candidates, course_stats)
    topk = ranked[:k]

    for r in topk:
        reasons = [f"aparece como siguiente en {r['support']} trayectorias similares"]
        if r["avg_grade_gpa"] > 0:
            reasons.append(f"promedio histórico {r['avg_grade_gpa']} (GPA), {r['avg_grade_100']} (0–100)")
        r["reason"] = "; ".join(reasons)

    return {
        "algorithm": "pm",
        "model_version": model_pack.get("metadata", {}).get("export_time",
                         datetime.now(timezone.utc).isoformat()),
        "degree_id": degree_id,
        "student_id": student_id,
        "params": {"k": k, "min_sim": min_sim, "gpa_success_threshold": gpa_success_threshold},
        "similar_peers": [{"student_id": s["student_id"], "sim": round(s["sim"], 4)} for s in similar_peers[:20]],
        "recommendations": topk
    }


if __name__ == "__main__":
    try:
        input_str = sys.stdin.read().strip()
        if input_str:
            inp = json.loads(input_str)
            model_pack = load_model("/opt/ml/model")
            out = predict_pm(inp, model_pack)
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "Proveer JSON por STDIN"}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": f"Fallo en main: {e}"}, ensure_ascii=False))