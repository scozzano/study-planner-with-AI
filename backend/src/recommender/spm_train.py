import os
import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Iterable, Optional, Set

import boto3
from boto3.dynamodb.conditions import Key, Attr

def env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except Exception:
        return default

def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return default

def env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)

def env_floats_csv(name: str, default_csv: str) -> List[float]:
    raw = os.environ.get(name, default_csv)
    vals = []
    for tok in raw.split(","):
        tok = tok.strip()
        if not tok:
            continue
        try:
            vals.append(float(tok))
        except Exception:
            pass
    return vals

def ddb_table():
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    ddb = boto3.resource("dynamodb", region_name=region)
    table_name = os.environ.get("DDB_TABLE", "AdaProjectTable")
    return ddb.Table(table_name)

def query_students_with_subjects(degree_id: str, limit_per_query: int = 1000) -> List[Dict[str, Any]]:
    table = ddb_table()
    pk = f"DEGREE#{degree_id}"
    key_cond = Key("PK").eq(pk) & Key("SK").begins_with("STUDENTS#")
    filt = Attr("subjects").exists()

    items: List[Dict[str, Any]] = []
    start_key = None
    while True:
        params = {"KeyConditionExpression": key_cond, "FilterExpression": filt, "Limit": limit_per_query}
        if start_key:
            params["ExclusiveStartKey"] = start_key
        resp = table.query(**params)
        items.extend(resp.get("Items", []))
        start_key = resp.get("LastEvaluatedKey")
        if not start_key:
            break
    print(f"Obtenidos {len(items)} estudiantes de DynamoDB para SPM")
    return items

def grade_100_to_gpa4(grade_0_100: float) -> float:
    try:
        v = float(grade_0_100)
    except Exception:
        return 0.0
    g = (v / 100.0) * 4.0
    return max(0.0, min(4.0, g))

def gpa4_to_grade100(gpa: float) -> float:
    try:
        v = float(gpa)
    except Exception:
        return 0.0
    x = (v / 4.0) * 100.0
    return max(0.0, min(100.0, x))

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
    """
    Usa 'semester' si hay variedad; si no, arma por fecha (year,half) y enumera.
    """
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

def items_to_sequences_and_stats(items: List[Dict[str, Any]],
                                 grade_min_for_spm: float,
                                 statuses_ok: Optional[Set[str]]) -> Tuple[List[List[List[str]]], Dict[str, Dict[str, float]]]:
    db_seqs: List[List[List[str]]] = []

    count_by_course: Dict[str, int] = {}
    grade_sum_by_course: Dict[str, float] = {}
    students_with_course: Dict[str, int] = {}
    total_students_seen = 0

    for it in items:
        subs_raw = it.get("subjects", []) or []
        dedup = dedupe_subjects(subs_raw)
        all_terms_map = assign_terms(dedup)

        seq_terms: List[List[str]] = []
        seen_in_student: Set[str] = set()

        for t in sorted(all_terms_map.keys()):
            term_codes: List[str] = []
            for code in sorted(all_terms_map[t]):
                s = next((x for x in dedup if normalize_code(x.get("code")) == code), None)
                if not s:
                    continue
                status = normalize_status(s)
                if statuses_ok is not None and status not in statuses_ok:
                    continue
                try:
                    grade = float(s.get("grade", 0.0))
                except Exception:
                    grade = 0.0
                if grade < grade_min_for_spm:
                    continue
                term_codes.append(code)

                g_gpa = grade_100_to_gpa4(grade)
                count_by_course[code] = count_by_course.get(code, 0) + 1
                grade_sum_by_course[code] = grade_sum_by_course.get(code, 0.0) + g_gpa
                seen_in_student.add(code)

            if term_codes:
                seq_terms.append(term_codes)

        if seq_terms:
            db_seqs.append(seq_terms)
            for c in seen_in_student:
                students_with_course[c] = students_with_course.get(c, 0) + 1
            total_students_seen += 1

    stats: Dict[str, Dict[str, float]] = {}
    total_students_seen = max(1, total_students_seen)
    for c, cnt in count_by_course.items():
        avg_g = grade_sum_by_course.get(c, 0.0) / max(1, cnt)
        adoption = students_with_course.get(c, 0) / total_students_seen
        stats[c] = {"avg_grade": round(avg_g, 3), "adoption_rate": round(adoption, 6), "count": int(cnt)}
    return db_seqs, stats

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

def projected_db_after(pattern: List[str], db: List[List[List[str]]]) -> List[Tuple[int, List[List[str]]]]:
    proj = []
    for seq in db:
        end_idx = pattern_occurs_and_end_index(pattern, seq)
        if end_idx is not None:
            proj.append((end_idx, seq))
    return proj

def frequent_extensions(pattern: List[str],
                        proj_db: List[Tuple[int, List[List[str]]]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    seen_per_seq: Set[str] = set()
    for seq_idx, (end_idx, seq_terms) in enumerate(proj_db):
        next_term = end_idx + 1
        if next_term >= len(seq_terms):
            continue
        key_base = f"seq{seq_idx}-"
        seen_local: Set[str] = set()
        for c in seq_terms[next_term]:
            if c in seen_local:
                continue
            seen_local.add(c)
            uniq = key_base + c
            if uniq not in seen_per_seq:
                seen_per_seq.add(uniq)
                counts[c] = counts.get(c, 0) + 1
    return counts

def prefixspan_mine(db: List[List[List[str]]],
                    min_support: float,
                    min_support_next: float,
                    max_pattern_len: int) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    nseq = max(1, len(db))
    supp_abs = max(1, int(round(min_support * nseq)))
    supp_next_abs = max(1, int(round(min_support_next * nseq)))

    freq1: Dict[str, int] = {}
    for seq in db:
        seen = set()
        for term in seq:
            for c in term:
                seen.add(c)
        for c in seen:
            freq1[c] = freq1.get(c, 0) + 1
    stack: List[Tuple[List[str], int]] = [([c], cnt) for c, cnt in freq1.items() if cnt >= supp_abs]

    while stack:
        pat, supp_abs_pat = stack.pop()
        supp = supp_abs_pat / nseq

        proj = projected_db_after(pat, db)
        ext_counts = frequent_extensions(pat, proj)

        next_items = []
        for c, cnt in ext_counts.items():
            if cnt >= supp_next_abs:
                next_items.append({
                    "subject": c,
                    "support_next": round(cnt / nseq, 6),
                    "confidence": round(cnt / supp_abs_pat if supp_abs_pat > 0 else 0.0, 6)
                })

        results.append({
            "sequence": [[x] for x in pat],
            "support": round(supp, 6),
            "next_items": next_items
        })

        if len(pat) >= max_pattern_len:
            continue

        for c, cnt in ext_counts.items():
            if cnt >= supp_abs:
                stack.append((pat + [c], cnt))

    results.sort(key=lambda r: (-len(r["sequence"]), -r["support"]))
    return results

def longest_prefix_match_len(pattern: List[str], seq_terms: List[List[str]]) -> int:
    if not pattern: return 0
    m = 0
    for i in range(1, len(pattern)+1):
        if pattern_occurs_and_end_index(pattern[:i], seq_terms) is not None:
            m = i
        else:
            break
    return m

def recommend_spm_for_terms(target_terms: List[List[str]],
                            patterns: List[Dict[str, Any]],
                            top_k: int = 4) -> Tuple[int, List[Tuple[str, float, float]]]:
    completed = {c for term in target_terms for c in term}
    best_len = 0
    bucket: List[Dict[str, Any]] = []

    for p in patterns:
        pat = [x[0] for x in p.get("sequence", [])]
        m = longest_prefix_match_len(pat, target_terms)
        if m <= 0:
            continue
        if m > best_len:
            best_len = m
            bucket = [p]
        elif m == best_len:
            bucket.append(p)

    candidates: Dict[str, Tuple[float, float]] = {}
    for p in bucket:
        pat = [x[0] for x in p.get("sequence", [])]
        if best_len >= len(pat):
            continue
        next_symbol = pat[best_len]
        if next_symbol in completed:
            continue
        conf = 0.0
        supp_next = 0.0
        for ni in p.get("next_items", []):
            if ni.get("subject") == next_symbol:
                conf = max(conf, float(ni.get("confidence", 0.0)))
                supp_next = max(supp_next, float(ni.get("support_next", 0.0)))
        score = conf * supp_next
        old = candidates.get(next_symbol)
        if old is None or score > old[0]:
            candidates[next_symbol] = (score, conf)

    ranked = sorted(candidates.items(), key=lambda kv: (-kv[1][0], -kv[1][1], kv[0]))[:top_k]
    out = [(code, sc, conf) for code, (sc, conf) in ranked]
    return best_len, out

def compute_spm_metrics(patterns: List[Dict[str, Any]], db: List[List[List[str]]]) -> Dict[str, float]:
    if not patterns or not db:
        return {
            "pattern_coverage": 0.0, "pattern_quality": 0.0,
            "sequence_diversity": 0.0, "pattern_completeness": 0.0,
            "total_patterns": 0, "avg_support": 0.0, "avg_confidence": 0.0
        }
    total_sequences = len(db)
    covered_seqs: Set[int] = set()
    supports = []
    confidences = []

    for idx, seq in enumerate(db):
        for p in patterns:
            pat = [x[0] for x in p["sequence"]]
            if pattern_occurs_and_end_index(pat, seq) is not None:
                covered_seqs.add(idx)
        supports.append(p.get("support", 0.0))
        for ni in p.get("next_items", []):
            confidences.append(ni.get("confidence", 0.0))

    coverage = len(covered_seqs) / max(1, total_sequences)
    avg_support = sum(supports) / max(1, len(supports))
    avg_conf = sum(confidences) / max(1, len(confidences)) if confidences else 0.0
    quality = (avg_support * 0.6) + (avg_conf * 0.4)

    length_counts: Dict[int, int] = {}
    for seq in db:
        L = len(seq)
        length_counts[L] = length_counts.get(L, 0) + 1
    probs = [cnt / total_sequences for cnt in length_counts.values()]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    diversity = entropy / math.log2(max(1, len(length_counts))) if length_counts else 0.0

    pat_lens = [len(p["sequence"]) for p in patterns] if patterns else []
    if pat_lens:
        max_len = max(pat_lens)
        completeness = len(set(pat_lens)) / max(1, max_len)
    else:
        completeness = 0.0

    return {
        "pattern_coverage": round(coverage, 4),
        "pattern_quality": round(quality, 4),
        "sequence_diversity": round(diversity, 4),
        "pattern_completeness": round(completeness, 4),
        "total_patterns": len(patterns),
        "avg_support": round(avg_support, 4),
        "avg_confidence": round(avg_conf, 4)
    }

def global_baseline_gpa(course_stats: Dict[str, Dict[str, float]]) -> float:
    if not course_stats:
        return 0.0
    num = 0.0
    den = 0.0
    for c, st in course_stats.items():
        g = float(st.get("avg_grade", 0.0))
        a = float(st.get("adoption_rate", 0.0))
        num += g * a
        den += a
    return round(num / den, 3) if den > 0 else round(sum(st.get("avg_grade", 0.0) for st in course_stats.values()) / max(1, len(course_stats)), 3)

def prefix_baseline_gpa(target_terms: List[List[str]],
                        patterns: List[Dict[str, Any]],
                        course_stats: Dict[str, Dict[str, float]]) -> float:
    best_len = 0
    bucket: List[Dict[str, Any]] = []
    for p in patterns:
        pat = [x[0] for x in p.get("sequence", [])]
        m = longest_prefix_match_len(pat, target_terms)
        if m <= 0:
            continue
        if m > best_len:
            best_len = m
            bucket = [p]
        elif m == best_len:
            bucket.append(p)
    if best_len == 0 or not bucket:
        return global_baseline_gpa(course_stats)

    num = 0.0
    den = 0.0
    for p in bucket:
        pat = [x[0] for x in p.get("sequence", [])]
        if best_len >= len(pat):
            continue
        next_symbol = pat[best_len]
        stat = course_stats.get(next_symbol, {})
        g = float(stat.get("avg_grade", 0.0))
        w = 0.0
        for ni in p.get("next_items", []):
            if ni.get("subject") == next_symbol:
                w = max(w, float(ni.get("support_next", 0.0)))
        if w > 0:
            num += g * w
            den += w
    if den == 0:
        return global_baseline_gpa(course_stats)
    return round(num / den, 3)

def simulate_cohort_spm(db: List[List[List[str]]],
                        patterns: List[Dict[str, Any]],
                        course_stats: Dict[str, Dict[str, float]],
                        cohort_size: int = 200,
                        top_k: int = 4,
                        baseline_mode: str = "global") -> Tuple[float, float, int]:
    if not db or not patterns:
        return (0.0, 0.0, 0)

    chosen = [seq for seq in db if len(seq) >= 1][:cohort_size]
    gpas_sim: List[float] = []
    gpas_base: List[float] = []

    for seq in chosen:
        if baseline_mode == "prefix":
            gpa_base_i = prefix_baseline_gpa(seq, patterns, course_stats)
        else:
            gpa_base_i = global_baseline_gpa(course_stats)
        gpas_base.append(gpa_base_i)

        best_len, recs = recommend_spm_for_terms(seq, patterns, top_k=top_k)
        if not recs:
            continue
        gpas = []
        for (code, _score, _conf) in recs:
            stat = course_stats.get(code, {})
            gpas.append(float(stat.get("avg_grade", 0.0)))
        if gpas:
            gpas_sim.append(sum(gpas) / len(gpas))

    n_eff = len(gpas_sim)
    if n_eff == 0:
        g_base = round(sum(gpas_base) / max(1, len(gpas_base)), 3) if gpas_base else global_baseline_gpa(course_stats)
        return (g_base, g_base, 0)

    g_base = round(sum(gpas_base[:n_eff]) / n_eff, 3)
    g_sim = round(sum(gpas_sim) / n_eff, 3)
    return (g_base, g_sim, n_eff)

def tune_support_and_simulate(db: List[List[List[str]]],
                              course_stats: Dict[str, Dict[str, float]],
                              support_values: List[float],
                              min_support_next: float,
                              max_pattern_len: int,
                              cohort_size: int = 200,
                              top_k: int = 4,
                              baseline_mode: str = "global") -> List[Dict[str, Any]]:
    results = []
    for sup in support_values:
        patterns = prefixspan_mine(db, min_support=sup, min_support_next=min_support_next, max_pattern_len=max_pattern_len)
        g_base, g_sim, n_eff = simulate_cohort_spm(
            db=db,
            patterns=patterns,
            course_stats=course_stats,
            cohort_size=cohort_size,
            top_k=top_k,
            baseline_mode=baseline_mode
        )
        delta = round(g_sim - g_base, 3)
        print(f"[TUNING][SPM] SUP={sup:.2f} N={n_eff} Base={g_base:.3f} Sim={g_sim:.3f} Δ={delta:+.3f}")
        results.append({
            "support": sup,
            "n_effective": n_eff,
            "gpa_base": g_base,
            "gpa_sim": g_sim,
            "delta": delta,
            "total_patterns": len(patterns)
        })
    return results

def train():
    print("🚀 Iniciando entrenamiento SPM...")

    degree_id = env_str("DEGREE_ID", "2491")
    min_support = env_float("MIN_SUPPORT", 0.20)
    min_support_next = env_float("MIN_SUPPORT_NEXT", 0.05)
    max_pattern_length = env_int("MAX_PATTERN_LENGTH", 6)
    grade_min = env_float("GRADE_MIN_FOR_SPM", 86.0)
    statuses_ok_env = env_str("STATUSES_OK_FOR_SPM", "APR")
    statuses_ok = set(s.strip().upper() for s in statuses_ok_env.split(",")) if statuses_ok_env else None
    top_k = env_int("TOP_K", 4)
    cohort_n = env_int("COHORT_SIZE", 200)
    baseline_mode = env_str("BASELINE_MODE", "global").lower()
    support_grid = env_floats_csv("TUNING_SUPPORT_GRID", "0.10,0.20,0.30")

    print(f"Config: DEGREE_ID={degree_id}, MIN_SUPPORT={min_support}, MIN_SUPPORT_NEXT={min_support_next}, "
          f"MAX_PATTERN_LENGTH={max_pattern_length}, GRADE_MIN_FOR_SPM={grade_min}, "
          f"STATUSES_OK_FOR_SPM={statuses_ok_env}, TOP_K={top_k}, COHORT_SIZE={cohort_n}, "
          f"BASELINE_MODE={baseline_mode}, TUNING_SUPPORT_GRID={support_grid}")

    print("📊 Cargando datos de DynamoDB…")
    items = query_students_with_subjects(degree_id)
    if not items:
        raise ValueError(f"No se encontraron items para DEGREE#{degree_id}")

    db, course_stats = items_to_sequences_and_stats(items, grade_min_for_spm=grade_min, statuses_ok=statuses_ok)
    print(f"✅ Secuencias por término (post-filtro): {len(db)} estudiantes")

    if not db:
        raise ValueError("No hay secuencias válidas para minar patrones")

    print("🔍 Minando patrones (PrefixSpan simplificado)…")
    patterns = prefixspan_mine(db, min_support=min_support, min_support_next=min_support_next, max_pattern_len=max_pattern_length)
    print(f"✅ Patrones descubiertos: {len(patterns)}")

    spm_metrics = compute_spm_metrics(patterns, db)
    print("===== SPM PATTERN METRICS =====")
    print(f"Pattern Coverage: {spm_metrics['pattern_coverage']:.4f}")
    print(f"Pattern Quality:  {spm_metrics['pattern_quality']:.4f}")
    print(f"Sequence Diversity: {spm_metrics['sequence_diversity']:.4f}")
    print(f"Pattern Completeness: {spm_metrics['pattern_completeness']:.4f}")
    print(f"Total Patterns: {spm_metrics['total_patterns']}, Avg Support: {spm_metrics['avg_support']:.4f}, Avg Confidence: {spm_metrics['avg_confidence']:.4f}")

    print("===== SPM COHORT SIMULATION (paper-style) =====")
    tuning_results = tune_support_and_simulate(
        db=db,
        course_stats=course_stats,
        support_values=support_grid,
        min_support_next=min_support_next,
        max_pattern_len=max_pattern_length,
        cohort_size=cohort_n,
        top_k=top_k,
        baseline_mode=baseline_mode
    )

    model_dir = "/opt/ml/model"
    os.makedirs(model_dir, exist_ok=True)

    import joblib
    model_path = os.path.join(model_dir, "model.joblib")
    artifact = {
        "algorithm": "spm",
        "model_type": "PrefixSpanSimplified_LongestMatchReco",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "degree_id": degree_id,
        "params": {
            "min_support": min_support,
            "min_support_next": min_support_next,
            "max_pattern_length": max_pattern_length,
            "grade_min_for_spm": grade_min,
            "statuses_ok_for_spm": list(statuses_ok) if statuses_ok else None,
            "top_k": top_k,
            "cohort_size": cohort_n,
            "baseline_mode": baseline_mode,
            "tuning_support_grid": support_grid
        },
        "patterns": patterns,
        "course_stats": course_stats,
        "pattern_metrics": spm_metrics,
        "tuning_simulation": tuning_results
    }
    joblib.dump(artifact, model_path)

    metadata_path = os.path.join(model_dir, "metadata.json")
    metadata = {
        "algorithm": "spm",
        "model_type": "PrefixSpanSimplified_LongestMatchReco",
        "export_time": datetime.now(timezone.utc).isoformat(),
        "model_files": ["model.joblib"],
        "training_info": {
            "degree_id": degree_id,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "total_sequences": len(db),
            "min_support": min_support,
            "min_support_next": min_support_next,
            "max_pattern_length": max_pattern_length,
            "grade_min_for_spm": grade_min,
            "statuses_ok_for_spm": statuses_ok_env,
            "top_k": top_k,
            "cohort_size": cohort_n,
            "baseline_mode": baseline_mode,
            "tuning_support_grid": support_grid
        },
        "pattern_metrics": spm_metrics,
        "tuning_simulation": tuning_results
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("🎉 Entrenamiento completado.")
    print(f"   - model.joblib: {os.path.getsize(model_path)} bytes")
    print(f"   - metadata.json: {os.path.getsize(metadata_path)} bytes")

if __name__ == "__main__":
    train()