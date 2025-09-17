import os
import sys
import json
import boto3
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timezone
from typing import Dict, List
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    f1_score,
    confusion_matrix
)
from sklearn.utils import resample
from boto3.dynamodb.conditions import Key

sys.path.append('/opt/ml/code')
from subjects import SUBJECT_CATEGORY, SUBJECT_REQUIREMENTS


PASS_STATUSES = {"APR"}

def safe_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    if value is None:
        return default
    try:
        if isinstance(value, float):
            return int(round(value))
        return int(value)
    except (ValueError, TypeError):
        return default

def passfail_from_status(status) -> int:
    s = "" if pd.isna(status) else str(status).strip().upper()
    return 1 if s in PASS_STATUSES else 0

def normalize_call(value) -> str:
    ordinary = {"JUN", "FEB", "JAN", "ORDINARY"}
    if pd.isna(value) or not str(value).strip():
        return "Ordinary"
    v = str(value).strip().upper()
    return "Ordinary" if v in ordinary else "Extraordinary"

def _parse_date(value):
    if value is None:
        return pd.NaT
    try:
        return pd.to_datetime(value, utc=False, errors="coerce")
    except Exception:
        return pd.NaT

def get_degree_plan(degree_id: str) -> dict:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(os.environ.get('DDB_TABLE', 'AdaProjectTable'))
    try:
        response = table.get_item(
            Key={'PK': 'UNIVERSITY#', 'SK': f'DEGREE#{degree_id}'}
        )
        item = response.get('Item')
        if not item:
            raise ValueError(f"No se encontró el plan de carrera para degree_id: {degree_id}")
        return item
    except Exception as e:
        raise ValueError(f"Error obteniendo plan de carrera: {str(e)}")

def query_schooling_items(table_name: str, degree_id: str, page_limit: int = 1000) -> List[dict]:
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(table_name)

    pk_value = f"DEGREE#{degree_id}"
    key_cond = Key("PK").eq(pk_value) & Key("SK").begins_with("STUDENTS#")

    items = []
    start_key = None
    while True:
        params = {"KeyConditionExpression": key_cond, "Limit": page_limit}
        if start_key:
            params["ExclusiveStartKey"] = start_key
        resp = table.query(**params)
        items.extend(resp.get("Items", []))
        start_key = resp.get("LastEvaluatedKey")
        if not start_key:
            break

    print(f"Obtenidos {len(items)} estudiantes de DynamoDB")
    return items

def items_to_cs_format(items: List[dict]) -> pd.DataFrame:
    rows = []

    for item in items:
        student_id = str(item.get("id", "")).strip()
        if not student_id:
            continue

        subjects = item.get("subjects", []) or []
        if not subjects:
            continue

        buckets: Dict[str, List[dict]] = {}
        for s in subjects:
            sid = str(s.get("code", "")).strip()

            if not sid:
                continue
            sid = str(sid).strip()
            s["_parsed_date"] = _parse_date(s.get("date"))
            buckets.setdefault(sid, []).append(s)

        for subj_code, attempts in buckets.items():
            has_apr_dictado_T = any(
                str(s.get("status", "")).upper() == "APR"
                and str(s.get("result_source", "")).strip().lower() == "por dictado"
                and str(s.get("result_type", "")).upper() == "T"
                for s in attempts
            )

            attempts_sorted = sorted(
                attempts,
                key=lambda z: (
                    z.get("_parsed_date", pd.NaT),
                    safe_int(z.get("attempt", 0))
                )
            )
            for i, s in enumerate(attempts_sorted, start=1):
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

                call_raw = s.get("call") or s.get("convocatoria") or s.get("status")
                grade = s.get("grade")
                similarity = s.get("similarity") or s.get("Similarity")

                rows.append({
                    "StudentID": f"student_{student_id}",
                    "Subject": subj_code,
                    "AttemptNumber": i,
                    "DegreeYear": int(safe_int(s.get("semester", 1), 1)),
                    "Call": normalize_call(call_raw),
                    "PassFail": passfail_from_status(status),
                    "Grade": (None if grade is None else safe_float(grade, default=np.nan)),
                    "Similarity": (None if similarity is None else safe_float(similarity, default=np.nan)),
                })

    df = pd.DataFrame(rows)
    return df


def reduce_call_classes(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(Call=df["Call"].map(normalize_call))

def add_category(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(Category=df["Subject"].map(SUBJECT_CATEGORY).fillna("Other"))

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

def compute_requirements_ratio(df: pd.DataFrame) -> pd.DataFrame:
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
    ssr = np.zeros(len(df), dtype=float)
    ssrc = np.zeros(len(df), dtype=float)

    global_pass_rate = df["PassFail"].mean() if len(df) else 0.5
    global_pass_rate_cat = df.groupby("Category")["PassFail"].mean().to_dict()

    for sid, g in df.groupby("StudentID"):
        g_sorted = g.sort_values(["DegreeYear", "AttemptNumber", "Subject"])
        passed_cum = 0
        total_cum = 0
        cat_passed: Dict[str, int] = {}
        cat_total: Dict[str, int] = {}

        for idx in g_sorted.index:
            cat = df.at[idx, "Category"]
            ssr[df.index.get_loc(idx)] = (passed_cum / total_cum) if total_cum > 0 else global_pass_rate
            if cat_total.get(cat, 0) == 0:
                ssrc[df.index.get_loc(idx)] = global_pass_rate_cat.get(cat, global_pass_rate)
            else:
                ssrc[df.index.get_loc(idx)] = cat_passed.get(cat, 0) / max(1, cat_total.get(cat, 0))

            total_cum += 1
            cat_total[cat] = cat_total.get(cat, 0) + 1
            if df.at[idx, "PassFail"] == 1:
                passed_cum += 1
                cat_passed[cat] = cat_passed.get(cat, 0) + 1

    return df.assign(SSR=ssr, SSRC=ssrc)

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = reduce_call_classes(out)
    out = add_category(out)
    out = compute_subject_pass_rate(out)
    out = compute_requirements_ratio(out)
    out = compute_student_success_rates(out)
    return out


def train_best_model(
    df: pd.DataFrame,
    random_state: int = 123,
    test_size: float = 0.2,
    n_estimators: int = 400,
    max_depth: int = None,
) -> list:

    target = "PassFail"
    numeric = ["AttemptNumber", "DegreeYear", "SPR", "RequirementsRatio", "SSR", "SSRC"]
    categorical = ["Subject", "Category", "Call"]

    needed = set(numeric + categorical + [target])
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas para entrenamiento: {missing}")

    X = df[numeric + categorical]
    y = df[target].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )

    train_df = X_train.copy()
    train_df[target] = y_train.values
    counts = train_df[target].value_counts()
    if len(counts) < 2:
        raise ValueError("El set de entrenamiento no tiene ambas clases tras el preprocesamiento; no se puede balancear.")
    maj_label = counts.idxmax()
    min_label = counts.idxmin()
    df_major = train_df[train_df[target] == maj_label]
    df_minor = train_df[train_df[target] == min_label]
    df_minor_up = resample(df_minor, replace=True, n_samples=len(df_major), random_state=42)
    train_bal = pd.concat([df_major, df_minor_up], ignore_index=True)

    X_train_bal = train_bal.drop(columns=[target])
    y_train_bal = train_bal[target].astype(int)

    try:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)

    pre = ColumnTransformer(
        transformers=[
            ("num", RobustScaler(with_centering=True, with_scaling=True), numeric),
            ("cat", ohe, categorical),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        n_jobs=-1,
        random_state=random_state,
        class_weight=None
    )

    pipe = Pipeline(steps=[("prep", pre), ("rf", clf)])

    pipe.fit(X_train_bal, y_train_bal)

    y_pred  = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_per_class = f1_score(y_test, y_pred, average=None)
    report_txt = classification_report(y_test, y_pred, target_names=["Fail", "Pass"])
    cm = confusion_matrix(y_test, y_pred)

    print("===== VALIDATION METRICS =====")
    print(f"Accuracy: {acc:.4f}")
    print(f"F1 macro: {f1_macro:.4f}")
    print(f"F1 per-class [Fail, Pass]: {f1_per_class}")
    print("Classification report:\n", report_txt)
    print("Confusion matrix:\n", cm)

    report_df = pd.DataFrame({
        "y_true": y_test.values,
        "y_pred": y_pred,
        "p_pass": y_proba
    }, index=X_test.index)

    metrics = {
        "accuracy": float(acc),
        "f1_macro": float(f1_macro),
        "f1_fail": float(f1_per_class[0]),
        "f1_pass": float(f1_per_class[1])
    }
    return pipe, report_df, metrics


def train():
    print("🚀 Iniciando entrenamiento RF...")

    n_estimators = int(os.environ.get('n_estimators', 400))
    max_depth = os.environ.get('max_depth')
    if max_depth:
        max_depth = int(max_depth)
    random_state = int(os.environ.get('random_state', 123))
    test_size = float(os.environ.get('test_size', 0.2))

    ddb_table = os.environ.get('DDB_TABLE', 'AdaProjectTable')
    degree_id = os.environ.get('DEGREE_ID', '2491')

    print(f"Config: n_estimators={n_estimators}, max_depth={max_depth}, random_state={random_state}, test_size={test_size}")
    print(f"DynamoDB: table={ddb_table}, degree_id={degree_id}")

    degree_record = get_degree_plan(degree_id)
    if not degree_record or not degree_record.get("subjects"):
        raise ValueError(f"No se pudo obtener el plan de carrera para degree_id={degree_id}")

    items = query_schooling_items(ddb_table, degree_id, page_limit=1000)
    if not items:
        raise ValueError(f"No se encontraron datos para degree_id: {degree_id}")

    df = items_to_cs_format(items)
    if df.empty:
        raise ValueError("No se pudieron procesar los datos de DynamoDB -> DataFrame vacío.")
    print(f"Parse inicial (intentos): filas={len(df)}, estudiantes={df['StudentID'].nunique()}, materias={df['Subject'].nunique()}")

    for col in ["StudentID", "Subject", "AttemptNumber", "DegreeYear", "Call", "PassFail"]:
        if col not in df.columns:
            raise ValueError(f"Falta columna requerida: {col}")

    df = build_features(df)
    print(f"Tras build_features: filas={len(df)}")

    dist = df["PassFail"].value_counts(dropna=False).to_dict()
    print("Distribución Pass/Fail global:", dist)
    if len(dist) < 2:
        raise ValueError("El dataset completo quedó monoclase; revisá el mapeo de status y/o la lógica de intentos.")

    model, report, metrics = train_best_model(
        df=df,
        random_state=random_state,
        test_size=test_size,
        n_estimators=n_estimators,
        max_depth=max_depth
    )

    model_dir = '/opt/ml/model'
    os.makedirs(model_dir, exist_ok=True)

    report_path = os.path.join(model_dir, 'report.csv')
    report.to_csv(report_path, index=False)

    model_path = os.path.join(model_dir, 'model.joblib')
    joblib.dump(model, model_path)

    try:
        feature_names = model.named_steps['prep'].get_feature_names_out()
    except AttributeError:
        feature_names = model.named_steps['prep'].get_feature_names_out()

    metadata = {
        "algorithm": "rf",
        "model_type": "RandomForest",
        "features_count": int(len(feature_names)),
        "samples_count": int(len(df)),
        "feature_columns": {
            "numeric": ["AttemptNumber", "DegreeYear", "SPR", "RequirementsRatio", "SSR", "SSRC"],
            "categorical": ["Subject", "Category", "Call"]
        },
        "hyperparameters": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "random_state": random_state,
            "test_size": test_size
        },
        "model_performance": metrics,
        "training_info": {
            "degree_id": degree_id,
            "ddb_table": ddb_table,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "data_points_used": int(len(df)),
            "unique_students": int(df['StudentID'].nunique()),
            "unique_subjects": int(df['Subject'].nunique())
        },
        "feature_importance": dict(zip(
            feature_names,
            model.named_steps['rf'].feature_importances_.tolist()
        ))
    }

    metadata_path = os.path.join(model_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f" - model.joblib   -> {model_path}")
    print(f" - metadata.json  -> {metadata_path}")
    print(f" - report.csv     -> {report_path}")
    print("Entrenamiento completado.")


if __name__ == "__main__":
    train()