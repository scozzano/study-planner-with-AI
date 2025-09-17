import os
import json
import random
import boto3
import joblib
from statistics import mean
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Set, Optional
from boto3.dynamodb.conditions import Key, Attr


def ddb_table():
    aws_region = os.getenv("AWS_REGION") or "us-east-1"
    dynamodb = boto3.resource("dynamodb", region_name=aws_region)
    table_name = os.getenv("DDB_TABLE", "AdaProjectTable")
    return dynamodb.Table(table_name)

def query_students_with_subjects(degree_id: str, limit_per_query: int = 1000) -> List[Dict[str, Any]]:
    table = ddb_table()
    partition_key_value = f"DEGREE#{degree_id}"
    key_cond = Key("PK").eq(partition_key_value) & Key("SK").begins_with("STUDENTS#")
    filter_expr = Attr("subjects").exists()

    items: List[Dict[str, Any]] = []
    start_key = None

    while True:
        params: Dict[str, Any] = {
            "KeyConditionExpression": key_cond,
            "FilterExpression": filter_expr,
            "Limit": limit_per_query
        }
        if start_key:
            params["ExclusiveStartKey"] = start_key

        response = table.query(**params)
        items.extend(response.get("Items", []))
        start_key = response.get("LastEvaluatedKey")
        if not start_key:
            break

    print(f"Obtenidos {len(items)} estudiantes de DynamoDB para PM")
    return items


def grade_100_to_gpa4(grade_0_100: float) -> float:
    try:
        value = float(grade_0_100)
    except Exception:
        return 0.0
    gpa = (value / 100.0) * 4.0
    return max(0.0, min(4.0, gpa))


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

    semester_value = subject.get("semester")
    try:
        semester_numeric = float(semester_value) if semester_value is not None else float("-inf")
    except Exception:
        semester_numeric = float("-inf")
    return (0, semester_numeric)

def normalize_code(value: Any) -> str:
    return (str(value).strip().upper()) if value is not None else ""

def normalize_result_type(subject: Dict[str, Any]) -> str:
    return str(subject.get("result_type") or subject.get("resultType") or subject.get("type") or "").strip().upper()

def normalize_status(subject: Dict[str, Any]) -> str:
    return str(subject.get("status") or "").strip().upper()

def source_is_exam(subject: Dict[str, Any]) -> bool:
    source_text = str(subject.get("result_source")).strip().lower()
    return (source_text == "por examen")

def dedupe_subjects(subjects_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped_by_code: Dict[str, List[Dict[str, Any]]] = {}
    for subject in subjects_raw or []:
        code = normalize_code(subject.get("code"))
        if not code or code == "NAN":
            continue
        grouped_by_code.setdefault(code, []).append(subject)

    deduped_subjects: List[Dict[str, Any]] = []

    for code, group in grouped_by_code.items():
        attempts_count = sum(1 for entry in group if source_is_exam(entry))

        has_apr_dictado_T = any(
            normalize_status(e) == "APR"
            and str(e.get("result_source", "")).strip().lower() == "por dictado"
            and normalize_result_type(e) == "T"
            for e in group
        )

        for entry in group:
            status = normalize_status(entry)
            result_type = normalize_result_type(entry)
            result_source = str(entry.get("result_source", "")).lower().strip()

            if status in ["REV", "RLI"]:
                continue

            if has_apr_dictado_T and status == "APR" and result_source == "por dictado" and result_type == "P":
                continue

            entry_with_attempts = dict(entry)
            entry_with_attempts["attempts"] = attempts_count
            deduped_subjects.append(entry_with_attempts)

    return deduped_subjects


def term_index_from_semester_or_date(subject: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    for date_key in DATE_KEYS:
        if date_key in subject and subject[date_key] is not None:
            dt = parse_date(subject[date_key])
            if dt:
                month = dt.month
                half = 1 if month <= 6 else 2
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
            if sem_val is None:
                continue
            sem_int = int(round(float(sem_val)))
            semesters_seen.add(sem_int)
        except Exception:
            continue

    terms: Dict[int, List[str]] = {}

    if len(semesters_seen) >= 2:
        for s in deduped_subjects:
            code_str = str(s.get("code", "")).strip()
            if not code_str or code_str.lower() == "nan":
                continue
            try:
                sem_val = s.get("semester", 1)
                sem_int = 1 if sem_val is None else int(round(float(sem_val)))
            except Exception:
                sem_int = 1
            terms.setdefault(sem_int, []).append(code_str)
        return terms

    term_keys: List[Tuple[int, int]] = []
    code_by_termkey: Dict[Tuple[int, int], List[str]] = {}

    for s in deduped_subjects:
        code_str = str(s.get("code", "")).strip()
        if not code_str or code_str.lower() == "nan":
            continue
        key = term_index_from_semester_or_date(s)
        if key is None:
            key = (0, 1)
        code_by_termkey.setdefault(key, []).append(code_str)

    term_keys = sorted(code_by_termkey.keys())
    for idx, key in enumerate(term_keys, start=1):
        codes = code_by_termkey[key]
        terms[idx] = terms.get(idx, []) + codes

    return terms


def items_to_terms(student_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed_students: List[Dict[str, Any]] = []

    for item in student_items:
        sort_key = item.get("SK", "")
        try:
            student_id = int(str(sort_key).split("#", 1)[-1])
        except Exception:
            try:
                student_id = int(item.get("id"))
            except Exception:
                student_id = 0

        raw_subjects: List[Dict[str, Any]] = item.get("subjects", []) or []
        deduped_subjects: List[Dict[str, Any]] = dedupe_subjects(raw_subjects)

        total_quality_points: float = 0.0
        total_weighted_credits: int = 0

        for subject in deduped_subjects:
            grade_value = subject.get("grade")
            try:
                grade_numeric = float(grade_value)
            except Exception:
                continue

            gpa_0_4 = grade_100_to_gpa4(grade_numeric)

            attempts_for_subject = int(subject.get("attempts", 0) or 0)
            weight = 1 + attempts_for_subject

            total_quality_points += gpa_0_4 * weight
            total_weighted_credits += weight

        global_gpa = round(total_quality_points / total_weighted_credits, 3) if total_weighted_credits > 0 else 0.0

        all_terms_map = assign_terms_for_student(deduped_subjects)

        subjects_by_term: Dict[int, List[str]] = {}
        grade_by_subject_gpa4: Dict[str, float] = {}
        approved_count = 0

        for term_idx in sorted(all_terms_map.keys()):
            for code_str in sorted(all_terms_map[term_idx]):
                subject = next((s for s in deduped_subjects if str(s.get("code", "")).strip() == code_str), None)
                if not subject:
                    continue

                status_value = str(subject.get("status", "")).upper() if subject.get("status") else ""
                if status_value != "APR":
                    continue

                try:
                    grade_value = subject.get("grade")
                    grade_numeric = 0.0 if grade_value is None else float(grade_value)
                except Exception:
                    grade_numeric = 0.0
                grade_gpa4 = grade_100_to_gpa4(grade_numeric)

                subjects_by_term.setdefault(term_idx, []).append(code_str)
                grade_by_subject_gpa4[code_str] = grade_gpa4
                approved_count += 1

        if approved_count == 0:
            continue

        ordered_terms: List[List[str]] = [sorted(subjects_by_term[k]) for k in sorted(subjects_by_term.keys())]

        transformed_students.append({
            "student_id": student_id,
            "subjects_by_term": ordered_terms,
            "grades_by_subject": grade_by_subject_gpa4,
            "gpa": global_gpa
        })

    return transformed_students


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

def next_term_courses_of(success_terms: List[List[str]], target_length: int) -> List[str]:
    next_index = target_length
    if next_index < len(success_terms):
        return list(success_terms[next_index])
    return []


def recommend_by_pm(target_student: Dict[str, Any],
                    successful_students: List[Dict[str, Any]],
                    similarity_threshold: float = 0.7) -> List[Tuple[str, int]]:
    target_terms = target_student["subjects_by_term"]
    num_completed_terms = len(target_terms)
    completed_courses = set([c for term in target_terms for c in term])
    frequency_counter: Dict[str, int] = {}

    for successful in successful_students:
        sim = similarity_of_footprints(target_terms, successful["subjects_by_term"])
        if sim >= similarity_threshold:
            for course in next_term_courses_of(successful["subjects_by_term"], num_completed_terms):
                if course in completed_courses:
                    continue
                frequency_counter[course] = frequency_counter.get(course, 0) + 1

    ranked = sorted(frequency_counter.items(), key=lambda x: (-x[1], x[0]))
    return ranked

def compute_course_stats(successful_students: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    count_by_course: Dict[str, int] = {}
    grade_sum_by_course: Dict[str, float] = {}
    students_with_course: Dict[str, int] = {}
    total_successful = max(1, len(successful_students))

    for student in successful_students:
        seen_in_student: Set[str] = set()
        for term in student["subjects_by_term"]:
            for course in term:
                count_by_course[course] = count_by_course.get(course, 0) + 1
                course_grade = student.get("grades_by_subject", {}).get(course, 0.0)
                grade_sum_by_course[course] = grade_sum_by_course.get(course, 0.0) + course_grade
                seen_in_student.add(course)
        for course in seen_in_student:
            students_with_course[course] = students_with_course.get(course, 0) + 1

    stats: Dict[str, Dict[str, float]] = {}
    for course, cnt in count_by_course.items():
        avg_grade = grade_sum_by_course.get(course, 0.0) / max(1, cnt)
        adoption_rate = students_with_course.get(course, 0) / total_successful
        stats[course] = {
            "avg_grade": round(avg_grade, 3),
            "adoption_rate": round(adoption_rate, 6),
            "count": int(cnt)
        }
    return stats

def evaluate_holdout_last_term(all_students: List[Dict[str, Any]],
                               successful_students: List[Dict[str, Any]],
                               similarity_threshold: float,
                               k: int,
                               gpa_success_threshold: float) -> Dict[str, float]:
    hits = 0
    num_with_label = 0
    tp = fp = tn = fn = 0

    students_with_recommendations = 0
    students_with_similar_peers = 0

    for student in all_students:
        full_terms = student["subjects_by_term"]
        if len(full_terms) < 2:
            continue

        history_terms = full_terms[:-1]
        label_next_term = set(full_terms[-1])

        hist_target = {
            "student_id": student["student_id"],
            "subjects_by_term": history_terms,
            "grades_by_subject": student.get("grades_by_subject", {}),
            "gpa": student["gpa"],
        }

        similar = False
        for s in successful_students:
            if similarity_of_footprints(history_terms, s["subjects_by_term"]) >= similarity_threshold:
                similar = True
                break
        if similar:
            students_with_similar_peers += 1

        recs = recommend_by_pm(hist_target, successful_students, similarity_threshold)[:k]
        if recs:
            students_with_recommendations += 1

        rec_set = {c for c, _ in recs}
        num_with_label += 1
        predicted = bool(rec_set & label_next_term)
        if predicted:
            hits += 1

        is_really_successful = student["gpa"] >= gpa_success_threshold
        if predicted and is_really_successful:
            tp += 1
        elif predicted and not is_really_successful:
            fp += 1
        elif (not predicted) and (not is_really_successful):
            tn += 1
        else:
            fn += 1

    total = tp + tn + fp + fn
    hit_rate = hits / max(1, num_with_label)
    accuracy = (tp + tn) / max(1, total)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, (precision + recall))

    print(f"Students with recommendations: {students_with_recommendations}/{num_with_label}")
    print(f"Students with similar peers: {students_with_similar_peers}/{num_with_label}")
    print(f"Students with next term data: {num_with_label}/{len(all_students)}")

    return {
        "hit_rate_at_k": round(hit_rate, 4),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn
    }


def _term_gpa_from_codes(codes: List[str], grades_by_subject: Dict[str, float]) -> Optional[float]:
    vals = [grades_by_subject.get(c) for c in codes if c in grades_by_subject]
    vals = [v for v in vals if v is not None]
    return round(mean(vals), 3) if vals else None

def _expected_gpa_for_course(code: str,
                             grades_by_subject: Dict[str, float],
                             course_stats: Dict[str, Dict[str, float]],
                             overall_avg: float) -> float:
    if code in grades_by_subject and grades_by_subject[code] is not None:
        return float(grades_by_subject[code])
    stat = course_stats.get(code)
    if stat is not None and "avg_grade" in stat:
        return float(stat["avg_grade"])
    return float(overall_avg)

def recommend_for_history(history_terms: List[List[str]],
                          successful_students: List[Dict[str, Any]],
                          similarity_threshold: float,
                          grades_by_subject: Dict[str, float],
                          top_k: int) -> List[str]:
    completed = set([c for term in history_terms for c in term])
    freq: Dict[str, int] = {}
    L = len(history_terms)
    for s in successful_students:
        sim = similarity_of_footprints(history_terms, s["subjects_by_term"])
        if sim >= similarity_threshold:
            next_courses = next_term_courses_of(s["subjects_by_term"], L)
            for c in next_courses:
                if c in completed:
                    continue
                freq[c] = freq.get(c, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [c for c, _ in ranked[:top_k]]

def simulate_cohort_next_term_gpa(all_students: List[Dict[str, Any]],
                                  successful_students: List[Dict[str, Any]],
                                  course_stats: Dict[str, Dict[str, float]],
                                  similarity_threshold: float,
                                  top_k: int,
                                  cohort_size: int = 200,
                                  seed: int = 42) -> Dict[str, Any]:
    random.seed(seed)
    avg_pool = [v.get("avg_grade", 0.0) for v in course_stats.values()]
    overall_avg = mean(avg_pool) if avg_pool else 0.0

    eligible: List[Dict[str, Any]] = []
    for s in all_students:
        terms = s["subjects_by_term"]
        if len(terms) < 2:
            continue

        history_terms = terms[:-1]
        real_next = list(terms[-1])

        baseline_gpa = _term_gpa_from_codes(real_next, s.get("grades_by_subject", {}))
        if baseline_gpa is None:
            continue

        top_recs = recommend_for_history(history_terms, successful_students,
                                         similarity_threshold, s.get("grades_by_subject", {}), top_k)
        if not top_recs:
            continue

        load = len(real_next)
        accepted = top_recs[:min(top_k, load)]

        exp_grades = [
            _expected_gpa_for_course(c, s.get("grades_by_subject", {}), course_stats, overall_avg)
            for c in accepted
        ]
        if not exp_grades:
            continue
        simulated_gpa = round(mean(exp_grades), 3)

        eligible.append({
            "student_id": s["student_id"],
            "baseline_next_gpa": baseline_gpa,
            "simulated_next_gpa": simulated_gpa,
            "delta": round(simulated_gpa - baseline_gpa, 3)
        })

    if len(eligible) > cohort_size:
        eligible = random.sample(eligible, cohort_size)

    if not eligible:
        return {
            "cohort_size": 0,
            "baseline_avg_gpa": 0.0,
            "simulated_avg_gpa": 0.0,
            "delta_avg": 0.0,
            "details": []
        }

    baseline_avg = round(mean([e["baseline_next_gpa"] for e in eligible]), 3)
    simulated_avg = round(mean([e["simulated_next_gpa"] for e in eligible]), 3)
    delta_avg = round(simulated_avg - baseline_avg, 3)

    return {
        "cohort_size": len(eligible),
        "baseline_avg_gpa": baseline_avg,
        "simulated_avg_gpa": simulated_avg,
        "delta_avg": delta_avg,
        "details": eligible[:20]
    }

def _parse_float_list_env(var_name: str, default_values: List[float]) -> List[float]:
    raw = os.getenv(var_name, "")
    if not raw.strip():
        return default_values
    out: List[float] = []
    for tok in raw.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            out.append(float(tok))
        except Exception:
            pass
    return out or default_values

def tune_parameters_with_simulation(all_students: List[Dict[str, Any]],
                                    top_k: int) -> List[Dict[str, Any]]:
    gpa_grid = _parse_float_list_env("TUNING_GPA_GRID", [3.4, 3.6, 3.8])
    sim_grid = _parse_float_list_env("TUNING_SIM_GRID", [0.6, 0.7, 0.8])
    cohort_size = int(os.getenv("TUNING_COHORT_SIZE", "200"))
    seed = int(os.getenv("TUNING_SEED", "42"))

    results: List[Dict[str, Any]] = []
    for gpa_thr in gpa_grid:
        successful = [s for s in all_students if s["gpa"] >= gpa_thr]
        if not successful:
            print(f"[TUNING] GPA≥{gpa_thr}: 0 exitosos, se omite fila.")
            continue
        stats = compute_course_stats(successful)

        for sim_thr in sim_grid:
            sim_res = simulate_cohort_next_term_gpa(
                all_students=all_students,
                successful_students=successful,
                course_stats=stats,
                similarity_threshold=sim_thr,
                top_k=top_k,
                cohort_size=cohort_size,
                seed=seed
            )
            row = {
                "gpa_threshold": round(gpa_thr, 3),
                "similarity_threshold": round(sim_thr, 3),
                "cohort_size": sim_res["cohort_size"],
                "baseline_avg_gpa": sim_res["baseline_avg_gpa"],
                "simulated_avg_gpa": sim_res["simulated_avg_gpa"],
                "delta_avg": sim_res["delta_avg"]
            }
            results.append(row)
            print(f"[TUNING] GPA≥{row['gpa_threshold']}  SIM≥{row['similarity_threshold']}  "
                  f"N={row['cohort_size']}  Base={row['baseline_avg_gpa']:.3f}  "
                  f"Sim={row['simulated_avg_gpa']:.3f}  Δ={row['delta_avg']:.3f}")

    results.sort(key=lambda r: (-r["delta_avg"], -r["cohort_size"], r["gpa_threshold"], r["similarity_threshold"]))
    if results:
        best = results[0]
        print(f"[TUNING][BEST] GPA≥{best['gpa_threshold']}  SIM≥{best['similarity_threshold']}  "
              f"N={best['cohort_size']}  Base={best['baseline_avg_gpa']:.3f}  "
              f"Sim={best['simulated_avg_gpa']:.3f}  Δ={best['delta_avg']:.3f}")
    else:
        print("[TUNING] Sin resultados (revisar grilla o datos).")

    return results


def train():
    print("Iniciando entrenamiento PM")

    degree_id = os.getenv("DEGREE_ID", "2491")
    try:
        gpa_success_threshold = float(os.getenv("GPA_SUCCESS_THRESHOLD", "3.6"))
    except Exception:
        gpa_success_threshold = 3.6
    try:
        similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    except Exception:
        similarity_threshold = 0.7
    try:
        top_k = int(os.getenv("TOP_K", "5"))
    except Exception:
        top_k = 5

    print(f"Config: DEGREE_ID={degree_id}, GPA_SUCCESS_THRESHOLD={gpa_success_threshold}, "
          f"SIMILARITY_THRESHOLD={similarity_threshold}, TOP_K={top_k}")

    print("Cargando datos de DynamoDB…")
    student_items = query_students_with_subjects(degree_id)
    if not student_items:
        raise ValueError(f"No se encontraron items para DEGREE#{degree_id}")

    transformed_students = items_to_terms(student_items)
    print(f"Estudiantes con trayectoria APR: {len(transformed_students)}")

    successful_students = [s for s in transformed_students if s["gpa"] >= gpa_success_threshold]
    if not successful_students:
        raise ValueError("No hay estudiantes exitosos según el umbral de GPA")
    print(f"Estudiantes exitosos (gpa ≥ {gpa_success_threshold}): {len(successful_students)}")

    course_stats = compute_course_stats(successful_students)

    print("===== PM RECOMMENDER METRICS =====")
    metrics = evaluate_holdout_last_term(
        all_students=transformed_students,
        successful_students=successful_students,
        similarity_threshold=similarity_threshold,
        k=top_k,
        gpa_success_threshold=gpa_success_threshold
    )

    print(f"Hit-Rate@{top_k}: {metrics['hit_rate_at_k']:.4f}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1']:.4f}")
    print(f"TP={metrics['tp']} FP={metrics['fp']} TN={metrics['tn']} FN={metrics['fn']}")

    print("===== PM COHORT SIMULATION =====")
    tuning_results = tune_parameters_with_simulation(
        all_students=transformed_students,
        top_k=top_k
    )

    artifact = {
        "schema_version": 3,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "degree_id": degree_id,
        "successful_students": [
            {
                "student_id": s["student_id"],
                "gpa": s["gpa"],
                "subjects_by_term": s["subjects_by_term"],
                "grades_by_subject": s["grades_by_subject"]
            } for s in successful_students
        ],
        "course_stats": course_stats,
        "params": {
            "gpa_success_threshold": gpa_success_threshold,
            "similarity_threshold": similarity_threshold,
            "top_k": top_k
        },
        "counts": {
            "students_total": len(transformed_students),
            "students_successful": len(successful_students)
        },
        "recommender_metrics": metrics,
        "tuning_results": tuning_results[:10]
    }

    model_dir = "/opt/ml/model"
    os.makedirs(model_dir, exist_ok=True)


    model_path = os.path.join(model_dir, "model.joblib")
    joblib.dump(artifact, model_path)

    metadata_path = os.path.join(model_dir, "metadata.json")
    metadata = {
        "algorithm": "pm",
        "model_type": "SimilarityFootprint",
        "export_time": datetime.now(timezone.utc).isoformat(),
        "model_files": ["model.joblib"],
        "training_info": {
            "degree_id": degree_id,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "students_total": len(transformed_students),
            "students_successful": len(successful_students),
            "gpa_success_threshold": gpa_success_threshold,
            "similarity_threshold": similarity_threshold,
            "top_k": top_k
        },
        "recommender_metrics": metrics,
        "tuning": {
            "grid": {
                "GPA": os.getenv("TUNING_GPA_GRID", "3.4,3.6,3.8"),
                "SIM": os.getenv("TUNING_SIM_GRID", "0.6,0.7,0.8"),
                "COHORT_SIZE": int(os.getenv("TUNING_COHORT_SIZE", "200"))
            },
            "top_results": tuning_results[:10]
        }
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("Entrenamiento completado.")
    print(f"   - model.joblib: {os.path.getsize(model_path)} bytes")
    print(f"   - metadata.json: {os.path.getsize(metadata_path)} bytes")

if __name__ == "__main__":
    train()