import os
import sys
import boto3
import pandas as pd
import numpy as np

from typing import Dict, Any, List
from boto3.dynamodb.conditions import Key, Attr

sys.path.append('/opt/ml/code')

try:
    from subjects import SUBJECT_CATEGORY, SUBJECT_REQUIREMENTS
except ImportError:
    SUBJECT_CATEGORY = {}
    SUBJECT_REQUIREMENTS = {}


PASS_STATUSES = {"APR"}

def safe_int(v, default=0):
    try:
        if v is None: return default
        if isinstance(v, float): return int(round(v))
        return int(v)
    except Exception:
        return default

def safe_float(v, default=0.0):
    try:
        if v is None: return default
        return float(v)
    except Exception:
        return default

def passfail_from_status(status) -> int:
    s = "" if pd.isna(status) else str(status).strip().upper()
    return 1 if s in PASS_STATUSES else 0

def normalize_call(value: str) -> str:
    ordinary = {"JUN", "FEB", "JAN", "ORDINARY"}
    if value is None or not str(value).strip():
        return "Ordinary"
    v = str(value).strip().upper()
    return "Ordinary" if v in ordinary else "Extraordinary"


def get_student_item(student_id: str, degree_id: str, table_name: str) -> Dict[str, Any]:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    pk_value = f"DEGREE#{degree_id}"
    sk_value = f"STUDENTS#{student_id}"
    resp = table.get_item(Key={'PK': pk_value, 'SK': sk_value})
    return resp.get('Item', {})

def scan_some_students_with_subjects(degree_id: str, table_name: str, limit_items: int = 50) -> List[Dict[str, Any]]:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    items, fetched, start_key = [], 0, None
    pk_value = f"DEGREE#{degree_id}"
    key_condition = Key("PK").eq(pk_value) & Key("SK").begins_with("STUDENTS#")
    filt = Attr("subjects").exists()

    while fetched < limit_items:
        params = {
            "KeyConditionExpression": key_condition,
            "FilterExpression": filt,
            "Limit": min(25, limit_items - fetched)
        }
        if start_key:
            params["ExclusiveStartKey"] = start_key
        resp = table.query(**params)
        chunk = resp.get("Items", [])
        items.extend(chunk)
        fetched += len(chunk)
        start_key = resp.get("LastEvaluatedKey")
        if not start_key or fetched >= limit_items:
            break

    return items


def history_from_student_item(item: Dict[str, Any]) -> pd.DataFrame:
    if not item or "subjects" not in item:
        return pd.DataFrame()

    student_id_raw = item.get('SK', '').replace('STUDENTS#', '')
    student_id = f"student_{student_id_raw}"

    subs = item.get('subjects', []) or []
    by_subj: Dict[str, List[Dict[str, Any]]] = {}
    for s in subs:
        code = s.get("code") or s.get("name") or s.get("subject_id")
        if not code:
            continue
        code = str(code).strip()
        s["_date"] = pd.to_datetime(s.get("date"), utc=False, errors="coerce")
        by_subj.setdefault(code, []).append(s)

    rows = []
    for subj, lst in by_subj.items():
        has_apr_dictado_T = any(
            str(s.get("status", "")).upper() == "APR"
            and str(s.get("result_source", "")).strip().lower() == "por dictado"
            and str(s.get("result_type", "")).upper() == "T"
            for s in lst
        )

        lst_sorted = sorted(lst, key=lambda x: (x.get("_date", pd.NaT), safe_int(x.get("attempt", 0))))
        for i, s in enumerate(lst_sorted, start=1):
            status = s.get("status")
            result_type = s.get("result_type", "")
            result_source = str(s.get("result_source", "")).lower().strip()

            if str(status).upper() in ["REV", "RLI"]:
                continue

            if (has_apr_dictado_T and
                str(status).upper() == "APR" and
                result_source == "por dictado" and
                str(result_type).upper() == "P"):
                continue

            rows.append({
                "StudentID": student_id,
                "Subject": subj,
                "AttemptNumber": i,
                "DegreeYear": safe_int(s.get("semester", 1), 1),
                "PassFail": passfail_from_status(s.get("status")),
                "Category": SUBJECT_CATEGORY.get(subj, "Other"),
                "Call": normalize_call(s.get("call") or s.get("convocatoria") or s.get("status")),
            })
    return pd.DataFrame(rows)

def full_data_from_some_students(items: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for it in items:
        df = history_from_student_item(it)
        if not df.empty:
            rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def compute_subject_pass_rate(df: pd.DataFrame) -> pd.DataFrame:
    spr = df.groupby("Subject")["PassFail"].mean().rename("SPR")
    return df.merge(spr, on="Subject", how="left")

def _past_mask(student_df: pd.DataFrame, idx: int) -> pd.Series:
    order_cols = ["DegreeYear", "AttemptNumber"]
    ordered = student_df.sort_values(order_cols).reset_index(drop=False)
    current_row = ordered.loc[ordered["index"] == idx]
    if current_row.empty:
        return student_df.index < idx
    pos = current_row.index[0]
    past_idx = set(ordered.loc[:pos-1, "index"].tolist())
    return student_df.index.to_series().isin(past_idx)

def compute_requirements_ratio_on_history(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(RequirementsRatio=np.nan)
    ratios = np.zeros(len(df), dtype=float)
    for sid, g in df.groupby("StudentID"):
        for i in g.index:
            subj = df.at[i, "Subject"]
            reqs = SUBJECT_REQUIREMENTS.get(subj, [])
            if not reqs:
                ratios[df.index.get_loc(i)] = 1.0
                continue
            mask_past = _past_mask(g, i)
            past_rows = g.loc[mask_past]
            passed = set(past_rows.loc[past_rows["PassFail"] == 1, "Subject"])
            done = sum(1 for r in reqs if r in passed)
            ratios[df.index.get_loc(i)] = done / len(reqs)
    return df.assign(RequirementsRatio=ratios)

def compute_student_success_rates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(SSR=np.nan, SSRC=np.nan)

    ssr = np.zeros(len(df), dtype=float)
    ssrc = np.zeros(len(df), dtype=float)

    global_pass = df["PassFail"].mean() if len(df) else 0.5
    global_cat = df.groupby("Category")["PassFail"].mean().to_dict()

    for sid, g in df.groupby("StudentID"):
        g_sorted = g.sort_values(["DegreeYear", "AttemptNumber", "Subject"])
        passed_cum, total_cum = 0, 0
        cat_passed, cat_total = {}, {}
        for idx in g_sorted.index:
            cat = df.at[idx, "Category"]
            ssr[df.index.get_loc(idx)] = (passed_cum / total_cum) if total_cum > 0 else global_pass
            ssrc[df.index.get_loc(idx)] = (
                cat_passed.get(cat, 0) / max(1, cat_total.get(cat, 0))
                if cat_total.get(cat, 0) > 0 else
                global_cat.get(cat, global_pass)
            )
            total_cum += 1
            cat_total[cat] = cat_total.get(cat, 0) + 1
            if df.at[idx, "PassFail"] == 1:
                passed_cum += 1
                cat_passed[cat] = cat_passed.get(cat, 0) + 1

    return df.assign(SSR=ssr, SSRC=ssrc)

def build_features_like_train(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "Call" in out.columns:
        out["Call"] = out["Call"].map(normalize_call)
    if "Category" not in out.columns:
        out["Category"] = out["Subject"].map(SUBJECT_CATEGORY).fillna("Other")
    out = compute_subject_pass_rate(out)
    out = compute_requirements_ratio_on_history(out)
    out = compute_student_success_rates(out)
    return out


def make_candidate_rows(student_hist_feat: pd.DataFrame,
                        full_feat: pd.DataFrame,
                        candidate_subjects: List[str],
                        degree_year: int) -> pd.DataFrame:
    if student_hist_feat.empty and full_feat.empty:
        return pd.DataFrame()

    student_id = (student_hist_feat["StudentID"].iloc[0]
                  if not student_hist_feat.empty else "student_unknown")

    global_pass = full_feat["PassFail"].mean() if len(full_feat) else 0.5
    spr_by_subj = full_feat.groupby("Subject")["PassFail"].mean().to_dict()
    global_cat = full_feat.groupby("Category")["PassFail"].mean().to_dict()

    passed_set = set()
    if not student_hist_feat.empty:
        passed_set = set(student_hist_feat.loc[student_hist_feat["PassFail"] == 1, "Subject"])

    prev_attempts = {}
    if not student_hist_feat.empty:
        prev_attempts = student_hist_feat.groupby("Subject")["AttemptNumber"].max().to_dict()

    rows = []
    for subj in candidate_subjects:
        subj = str(subj).strip()
        cat = SUBJECT_CATEGORY.get(subj, "Other")

        attempt_num = int(prev_attempts.get(subj, 0)) + 1

        spr_val = float(spr_by_subj.get(subj, global_pass))

        reqs = SUBJECT_REQUIREMENTS.get(subj, [])
        if reqs:
            done = sum(1 for r in reqs if r in passed_set)
            req_ratio = done / len(reqs)
        else:
            req_ratio = 1.0

        if not student_hist_feat.empty:
            ssr_val = float(student_hist_feat["SSR"].iloc[-1])
        else:
            ssr_val = global_pass

        if not student_hist_feat.empty:
            ssrc_hist = student_hist_feat.loc[student_hist_feat["Category"] == cat, "SSRC"]
            if len(ssrc_hist) > 0 and pd.notna(ssrc_hist.iloc[-1]):
                ssrc_val = float(ssrc_hist.iloc[-1])
            else:
                ssrc_val = float(global_cat.get(cat, global_pass))
        else:
            ssrc_val = float(global_cat.get(cat, global_pass))

        rows.append({
            "StudentID": student_id,
            "Subject": subj,
            "AttemptNumber": attempt_num,
            "DegreeYear": int(safe_int(degree_year, 1)),
            "Call": "Ordinary",
            "Category": cat,
            "SPR": spr_val,
            "RequirementsRatio": req_ratio,
            "SSR": ssr_val,
            "SSRC": ssrc_val,
        })

    return pd.DataFrame(rows)


def predict_rf(input_data: Dict[str, Any], model_dict: Dict[str, Any]) -> Dict[str, Any]:
    model = model_dict['model']
    metadata = model_dict.get('metadata', {})

    student_id = str(input_data.get('student_id'))
    candidate_subjects = input_data.get('candidate_subjects')
    degree_year = input_data.get('degree_year')
    degree_id = str(input_data.get('degree_id', '2491'))
    table_name = os.environ.get('DDB_TABLE', 'AdaProjectTable')

    if not candidate_subjects or not isinstance(candidate_subjects, list):
        return {"error": "candidate_subjects debe ser una lista no vacía"}

    unknown = [s for s in candidate_subjects if s not in SUBJECT_CATEGORY]
    if unknown:
        print("WARNING: materias candidatas sin categoría en subjects.py:", unknown)

    try:
        student_item = get_student_item(student_id, degree_id, table_name)
        student_history = history_from_student_item(student_item)
        if student_history.empty:
            return {"error": f"No se encontraron datos del estudiante {student_id} para degree {degree_id}"}
    except Exception as e:
        return {"error": f"Error obteniendo histórico del estudiante: {e}"}

    try:
        some_items = scan_some_students_with_subjects(degree_id, table_name, limit_items=50)
        full_data = full_data_from_some_students(some_items)
        if full_data.empty:
            print("WARNING: full_data vacío; se usarán defaults globales 0.5")
    except Exception as e:
        return {"error": f"Error obteniendo datos globales: {e}"}

    student_hist_feat = build_features_like_train(student_history)
    full_feat = build_features_like_train(full_data)

    cand = make_candidate_rows(student_hist_feat, full_feat, candidate_subjects, degree_year)
    if cand.empty:
        return {"error": "No se pudieron construir features de candidatos"}

    numeric = ["AttemptNumber", "DegreeYear", "SPR", "RequirementsRatio", "SSR", "SSRC"]
    categorical = ["Subject", "Category", "Call"]
    needed = numeric + categorical
    missing = [c for c in needed if c not in cand.columns]
    if missing:
        return {"error": f"Faltan columnas para inferencia: {missing}"}

    X_cand = cand[needed]

    try:
        p_pass = model.predict_proba(X_cand)[:, 1]
    except Exception as e:
        return {"error": f"Error del modelo en predict_proba: {e}"}

    recs = []
    for i, subj in enumerate(cand["Subject"].tolist()):
        recs.append({
            "subject": subj,
            "p_pass": round(float(p_pass[i]), 3),
            "rank": i + 1
        })
    recs.sort(key=lambda x: x["p_pass"], reverse=True)
    for i, r in enumerate(recs):
        r["rank"] = i + 1

    return {
        "student_id": student_id,
        "degree_id": degree_id,
        "recommendations": recs
    }