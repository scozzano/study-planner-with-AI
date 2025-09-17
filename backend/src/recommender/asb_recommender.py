import boto3
import math
import statistics
import warnings
import base64
import pandas as pd
import numpy as np

from boto3.dynamodb.conditions import Key
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import classification_report
try:
    import graphviz
    import pydot
    _GRAPHVIZ_OK = True
except Exception:
    _GRAPHVIZ_OK = False

warnings.filterwarnings("ignore", category=DeprecationWarning)

def get_training_data(degree_id: str, table_name: str, page_limit: int = 1000):
    print(f"Obteniendo datos para degree {degree_id} desde tabla {table_name}")
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

    print(f"Obtenidos {len(items)} registros de DynamoDB")
    return items

def map_result_to_status(result):
    r = str(result).upper()
    if r == "APR":
        return "PASSED"
    else:
        return "FAILED"

def map_grade(grade_str):
    if pd.isna(grade_str) or grade_str == "":
        return np.nan
    try:
        g = float(grade_str)
        if g == 0:
            return 5.0
        if 1 <= g <= 100:
            if g >= 90: return 1.0
            if g >= 80: return 2.0
            if g >= 70: return 3.0
            return 5.0
        return np.nan
    except Exception:
        return np.nan

def determine_credit_value(grade, result):
    if pd.isna(grade) or grade == 0:
        return 0
    return 1 if map_result_to_status(result) == "PASSED" else 0

def convert_dynamodb_to_asb_format(items):
    print("Convirtiendo datos al formato ASB...")
    print(f"Total items recibidos: {len(items)}")

    if items:
        print(f"DEBUG: Estructura del primer item: {list(items[0].keys())}")
        print(f"DEBUG: Primer item completo: {items[0]}")

    asb_rows = []
    students_processed = 0
    students_skipped_insufficient_subjects = 0
    subjects_processed = 0
    subjects_skipped = 0
    subjects_filtered_apr = 0

    for item in items:
        student_id = str(item.get("id", ""))
        subjects = item.get("subjects", [])
        date_val = item.get("start_date") or item.get("date")

        if not isinstance(subjects, list) or len(subjects) < 2:
            students_skipped_insufficient_subjects += 1
            continue

        students_processed += 1

        subjects_by_code = {}
        for subject in subjects:
            result_raw = subject.get("status", "")
            if str(result_raw).upper() in ["REV", "RLI"]:
                subjects_skipped += 1
                continue

            subject_code_raw = subject.get("code")
            if subject_code_raw is None or str(subject_code_raw).strip() == "" or str(subject_code_raw).lower() == "nan":
                subjects_skipped += 1
                continue

            subject_code = str(subject_code_raw)
            if subject_code not in subjects_by_code:
                subjects_by_code[subject_code] = []
            subjects_by_code[subject_code].append(subject)

        for subject_code, subject_list in subjects_by_code.items():
            subjects_processed += len(subject_list)

            has_apr_dictado_T = any(
                str(subject.get("status", "")).upper() == "APR"
                and str(subject.get("result_source", "")).strip().lower() == "por dictado"
                and str(subject.get("result_type", "")).upper() == "T"
                for subject in subject_list
            )

            for subject in subject_list:
                try:
                    result_raw = subject.get("status", "")
                    result_type_raw = subject.get("result_type", "")
                    result_source_raw = subject.get("result_source", "")

                    if (has_apr_dictado_T and
                        str(result_raw).upper() == "APR" and
                        str(result_source_raw).lower().strip() == "por dictado" and
                        str(result_type_raw).upper() == "P"):
                        subjects_filtered_apr += 1
                        continue

                    sem_raw = subject.get("semester")
                    try:
                        semester = int(float(sem_raw))
                        print(f"DEBUG: Procesando materia {subject_code} - fachsemester: {semester} (raw: {sem_raw})")
                    except (TypeError, ValueError):
                        print(f"DEBUG: Error procesando semestre para materia {subject_code} - raw: {sem_raw}")
                        subjects_skipped += 1
                        continue

                    grade_raw = subject.get("grade")

                    grade = map_grade(grade_raw)
                    status = map_result_to_status(result_raw)
                    credits = determine_credit_value(grade, result_raw)

                    if pd.notna(grade):
                        asb_rows.append({
                            "studentstudyid": f"student_{student_id}",
                            "Course": subject_code,
                            "fachsemester": semester,
                            "course-grade": grade,
                            "Credit": credits,
                            "Final Course Status": status,
                            "Time-Start": date_val
                        })
                    else:
                        subjects_skipped += 1

                except Exception as e:
                    print(f"Error procesando subject {subject}: {e}")
                    subjects_skipped += 1
                    continue

    df = pd.DataFrame(asb_rows)
    print(f"Datos convertidos: {len(df)} registros")
    print("Estadísticas de procesamiento:")
    print(f"  - Estudiantes procesados: {students_processed}")
    print(f"  - Estudiantes saltados (pocas materias): {students_skipped_insufficient_subjects}")
    print(f"  - Materias procesadas: {subjects_processed}")
    print(f"  - Materias saltadas: {subjects_skipped}")
    print(f"  - Materias APR dictado filtradas (P cuando hay T): {subjects_filtered_apr}")
    return df

def format_from_dynamodb(degree_id="2491", table_name="AdaProjectTable", sample_size=None):
    items = get_training_data(degree_id, table_name)
    if not items:
        raise ValueError("No se pudieron obtener datos de DynamoDB")

    df = convert_dynamodb_to_asb_format(items)

    if sample_size:
        unique_students = df["studentstudyid"].unique()
        if len(unique_students) > sample_size:
            selected = np.random.choice(unique_students, sample_size, replace=False)
            df = df[df["studentstudyid"].isin(selected)]
            print(f"Muestreados {sample_size} estudiantes: {df.shape}")

    return df

def add_course_index(df, feature, is_atomic, pm_index_type):
    def order(row):
        s_id = row["studentstudyid"]; c = row["Course"]; sem = row["fachsemester"]; status = row["Final Course Status"]
        student = df.loc[df["studentstudyid"] == s_id]
        semesters = sorted(student["fachsemester"].unique())
        idx = semesters.index(sem)
        if is_atomic:
            return c + "_" + str(idx + 1), idx + 1, None
        else:
            first_attempt_sem = sorted(student.loc[student["Course"] == c]["fachsemester"].values)[0]
            if first_attempt_sem == sem:
                if status == "PASSED":
                    return "e_" + c, idx + 1, "s_" + c
                return None, idx + 1, "s_" + c
            else:
                if status == "PASSED":
                    return "e_" + c, idx + 1, None
                return None, None, None

    def distance(row):
        s_id = row["studentstudyid"]; c = row["Course"]; sem = row["fachsemester"]; status = row["Final Course Status"]
        student = df.loc[df["studentstudyid"] == s_id]
        semesters = sorted(student["fachsemester"].unique())
        first_sem = semesters[0]
        if is_atomic:
            return c + "_" + str(sem - first_sem), sem - first_sem, None
        else:
            first_attempt_sem = sorted(student.loc[student["Course"] == c]["fachsemester"].values)[0]
            if first_attempt_sem == sem:
                if status == "PASSED":
                    return "e_" + c, sem - first_sem, "s_" + c
                return None, sem - first_sem, "s_" + c
            else:
                if status == "PASSED":
                    return "e_" + c, sem - first_sem, None
                return None, None, None

    def semester(row):
        s_id = row["studentstudyid"]; c = row["Course"]; sem = row["fachsemester"]; status = row["Final Course Status"]
        student = df.loc[df["studentstudyid"] == s_id]
        if is_atomic:
            return c + "_" + str(sem), sem, None
        else:
            first_attempt_sem = sorted(student.loc[student["Course"] == c]["fachsemester"].values)[0]
            if first_attempt_sem == sem:
                if status == "PASSED":
                    return "e_" + c, sem, "s_" + c
                return None, sem, "s_" + c
            else:
                if status == "PASSED":
                    return "e_" + c, sem, None
                return None, None, None

    if feature == "Course-Order":
        df["course-index"], df["index"], df["start-index"] = zip(*df.apply(lambda r: order(r), axis=1))
    elif feature == "Course-Distance":
        df["course-index"], df["index"], df["start-index"] = zip(*df.apply(lambda r: distance(r), axis=1))
    elif feature == "Course-Semester":
        df["course-index"], df["index"], df["start-index"] = zip(*df.apply(lambda r: semester(r), axis=1))
    else:
        if pm_index_type == "fachsemester":
            df["course-index"], df["index"], df["start-index"] = zip(*df.apply(lambda r: semester(r), axis=1))
        elif pm_index_type == "order":
            df["course-index"], df["index"], df["start-index"] = zip(*df.apply(lambda r: order(r), axis=1))
        else:
            df["course-index"], df["index"], df["start-index"] = zip(*df.apply(lambda r: distance(r), axis=1))

def get_2_label(label, number):
    if number <= 2.5:
        return label + " <= 2.5"
    elif number > 2.5:
        return label + " > 2.5"
    return None

def get_5_label(label, number):
    if number <= 1.5: return label + " Excellent"
    elif number <= 2.5: return label + " Good"
    elif number <= 3.5: return label + " Satisfactory"
    elif number <= 4.0: return label + " Sufficient"
    elif number > 4.0: return label + " Failed"
    return None

def get_GPA(row, df, incl_fail):
    s = row["studentstudyid"]
    credit_grades = df.loc[(df["studentstudyid"] == s)][["Credit", "course-grade"]].values
    c_g = [[c, g] for c, g in credit_grades if not pd.isna(g)]
    if not incl_fail:
        c_g = [[c, g] for c, g in c_g if g != 5.0]
    weighted_grade = sum([c * g for c, g in c_g])
    total_credits = sum([c for c, g in c_g])
    GPA = None
    if total_credits > 0:
        GPA = weighted_grade / total_credits
        GPA = math.floor(GPA * 10) / 10.0
    gpa_2 = get_2_label("GPA", GPA) if (GPA is not None and not pd.isna(GPA)) else None
    gpa_5 = get_5_label("GPA", GPA) if (GPA is not None and not pd.isna(GPA)) else None
    return GPA, gpa_2, gpa_5

def compute_exact_GPA(df, GPA_grades):
    incl_fail = True
    if GPA_grades == "passed+failed last attempt":
        df = df.drop_duplicates(subset=["studentstudyid", "Course", "fachsemester"], keep="last")
    elif GPA_grades == "passed":
        incl_fail = False
    df["GPA"], df["GPA-2level"], df["GPA-5level"] = zip(*df.apply(lambda row: get_GPA(row, df, incl_fail), axis=1))
    return df

def get_GPA_label(df, is_binary, GPA_grades):
    students = df["studentstudyid"].unique()
    df = compute_exact_GPA(df, GPA_grades)
    GPAs = []
    for s in students:
        label_GPA = df.loc[df["studentstudyid"] == s]["GPA-2level" if is_binary else "GPA-5level"].values[0]
        GPAs.append(label_GPA)
    return pd.DataFrame(GPAs, columns=pd.Index(["label"])), df

def get_passfail_label(df, course, is_atomic, label_index, is_pm):
    students = df["studentstudyid"].unique()
    pass_fail = []
    if is_atomic:
        for s in students:
            status = list(df.loc[
                (df["studentstudyid"] == s) & (df["course-index"] == f"{course}_{label_index}")
            ]["Final Course Status"])
            pass_fail.append(str(status[0]) if status else None)
    else:
        pass_fail = [None for _ in students]
    return pd.DataFrame(pass_fail, columns=pd.Index(["label"]))

def get_course_grade_label(df, course, is_binary, is_atomic, label_index, is_pm):
    students = df["studentstudyid"].unique()
    grades = []
    for s in students:
        if is_atomic:
            label_index_name = f"{course}_{label_index}"
            grade = list(df.loc[
                (df["studentstudyid"] == s) & (df["course-index"] == label_index_name)
            ]["course-grade"])
        else:
            if is_pm:
                label_index_name = "e_" + course
                grade = list(df.loc[(df["studentstudyid"] == s) & (df["course-index"] == label_index_name)]["course-grade"])
            else:
                label_index_name = f"e_{course}_{label_index}"
                grade = list(df.loc[
                    (df["studentstudyid"] == s) &
                    (df["course-index"] == "e_" + course) &
                    (df["index"] == label_index)
                ]["course-grade"])
        if grade:
            exact = grade[0]
            grades.append(get_2_label(label_index_name, exact) if is_binary else get_5_label(label_index_name, exact))
        else:
            grades.append(None)
    return pd.DataFrame(np.array(grades), columns=pd.Index(["label"]))

def get_label(df, clf_dict):
    label_name = clf_dict["label"]
    if label_name == "Overall GPA":
        return get_GPA_label(df, clf_dict["is_binary_label"], clf_dict["GPA_grades"])[0]
    else:
        return get_course_grade_label(
            df, clf_dict["course"], clf_dict["is_binary_label"],
            clf_dict["is_atomic"], clf_dict["label_index"], clf_dict["is_pm"]
        )

def get_lifecycle_course_index(df, label_index):
    end_indices = df[["course-index", "index"]].values
    start_indices = df[["start-index", "index"]].values
    if pd.isna(label_index):
        all_start_features = list(set([e[0] + "_" + str(int(e[1])) for e in start_indices if pd.notna(e[0])]))
        all_end_features = list(set([e[0] + "_" + str(int(e[1])) for e in end_indices if pd.notna(e[0])]))
    else:
        all_start_features = list(set([e[0] + "_" + str(int(e[1])) for e in start_indices if (pd.notna(e[0]) and e[1] <= int(label_index))]))
        all_end_features = list(set([e[0] + "_" + str(int(e[1])) for e in end_indices if (pd.notna(e[0]) and e[1] <= int(label_index))]))
    return all_start_features + all_end_features

def feature_non_pm(df, clf_dict):
    students = df["studentstudyid"].unique()
    is_atomic = clf_dict["is_atomic"]
    label = clf_dict["label"]
    label_index = clf_dict["label_index"]
    if label == "Overall GPA":
        all_feature_names = df["course-index"].unique() if is_atomic else get_lifecycle_course_index(df, None)
    else:
        if is_atomic:
            all_feature_names = df.loc[(df["index"] <= label_index)]["course-index"].unique()
        else:
            all_feature_names = get_lifecycle_course_index(df, label_index)
    rows = []
    for s in students:
        student_df = df.loc[(df["studentstudyid"] == s)]
        student_features = student_df["course-index"].values if is_atomic else get_lifecycle_course_index(student_df, None)
        rows.append([1 if f in student_features else 0 for f in all_feature_names])
    return pd.DataFrame(np.array(rows), columns=pd.Index(all_feature_names))

def get_all_pm_feature_names(df, clf_dict):
    is_atomic = clf_dict["is_atomic"]
    course = clf_dict["course"]
    label = clf_dict["label"]
    label_index = clf_dict["label_index"]
    if is_atomic:
        dfg_node_names = df["course-index"].unique()
        right_course = dfg_node_names if label == "Overall GPA" else [f"{course}_{label_index}"]
    else:
        dfg_node_names = []
        for c in df["Course"].unique():
            dfg_node_names.extend(["s_" + c, "e_" + c])
        right_course = dfg_node_names if label == "Overall GPA" else ["e_" + course]
    names = []
    for left in dfg_node_names:
        for right in right_course:
            if is_atomic:
                try:
                    i = int(str(left).split("_")[-1]); j = int(str(right).split("_")[-1])
                except Exception:
                    continue
                if i <= j:
                    names.append(left + "->" + right)
            else:
                names.append(left + "->" + right)
    return names

def student_pm_feature(student_df, clf_dict):
    label = clf_dict["label"]; course = clf_dict["course"]
    is_atomic = clf_dict["is_atomic"]; label_index = clf_dict["label_index"]
    feature = clf_dict["feature"]
    if is_atomic:
        node_index_df = student_df[["course-index", "index"]]
    else:
        end_indices = student_df[["course-index", "index"]].dropna()
        start_indices = student_df[["start-index", "index"]].dropna()
        node_index_df = pd.concat([start_indices.rename(columns={"start-index": "course-index"}), end_indices], axis=0)
    all_indices = sorted(node_index_df["index"].unique())
    node_index_list = node_index_df.values
    if label == "Overall GPA":
        right_list = node_index_list
        index = 0
    else:
        if is_atomic:
            index_list = student_df.loc[student_df["course-index"] == f"{course}_{label_index}"].values
            index = label_index if index_list.size > 0 else ""
            right_list = [(f"{course}_{label_index}", index)]
        else:
            index_list = student_df.loc[student_df["course-index"] == "e_" + course]["index"].values
            index = index_list[0] if index_list.size > 0 else ""
            right_list = [("e_" + course, index)]
    if index == "":
        return [], []
    pm_features, path_lengths = [], []
    for left, idx1 in node_index_list:
        for right, idx2 in right_list:
            if feature == "Path Length":
                if idx1 <= idx2:
                    pl = all_indices.index(idx2) - all_indices.index(idx1)
                    pm_features.append(left + "->" + right); path_lengths.append(pl)
            elif feature == "Directly Follows":
                if idx1 + 1 == idx2:
                    pm_features.append(left + "->" + right)
            else:
                if idx1 < idx2:
                    pm_features.append(left + "->" + right)
    return pm_features, path_lengths

def feature_pm(df, clf_dict):
    students = df["studentstudyid"].unique()
    all_feature_names = get_all_pm_feature_names(df, clf_dict)
    feature = clf_dict["feature"]
    rows = []
    for s in students:
        student_df = df.loc[(df["studentstudyid"] == s)]
        student_features, path_lens = student_pm_feature(student_df, clf_dict)
        l = []
        for f_name in all_feature_names:
            if feature == "Path Length":
                if f_name in student_features:
                    idx = student_features.index(f_name)
                    l.append(path_lens[idx])
                else:
                    l.append(-1)
            else:
                l.append(1 if f_name in student_features else 0)
        rows.append(l)
    return pd.DataFrame(np.array(rows), columns=pd.Index(all_feature_names))

def get_behavioral_features(df, clf_dict):
    feature = clf_dict["feature"]; is_atomic = clf_dict["is_atomic"]
    if feature in ["Course-Order", "Course-Semester", "Course-Distance"]:
        return feature_non_pm(df, clf_dict)
    elif feature in ["Path Length", "Directly Follows", "Eventually Follows"]:
        return feature_pm(df, clf_dict)
    else:
        raise ValueError(f"Feature desconocida: {feature}")

def get_exams_per_semester(df, s, max_sem):
    ex_sem = []
    ex_sem_dict = dict(df.loc[(df["studentstudyid"] == s)][["fachsemester"]].value_counts())
    for i in range(1, max_sem + 1):
        ex_sem.append(ex_sem_dict.get((i,), 0))
    return ex_sem

def get_numerical_features(df, clf_dict):
    max_sem = int(max(df["fachsemester"].values))
    students = df["studentstudyid"].unique()
    label = clf_dict["label"]

    if label == "Overall GPA":
        rows = []
        for s in students:
            exams_semester = get_exams_per_semester(df, s, max_sem)
            exams = str(sum(exams_semester))
            med_exams_per_sem = int(np.median(exams_semester))
            non_zero_sems = int(np.count_nonzero(exams_semester))
            rows.append([exams, med_exams_per_sem, non_zero_sems])
        return pd.DataFrame(np.array(rows), columns=pd.Index(["exams", "med_exams_per_sem", "non_zero_sems"]))
    else:
        course = clf_dict["course"]; label_index = clf_dict["label_index"]; is_atomic = clf_dict["is_atomic"]; is_pm = clf_dict["is_pm"]
        rows = []
        for s in students:
            lab_idx = label_index
            if not is_atomic and is_pm:
                lab_idx_arr = df.loc[(df["studentstudyid"] == s) & (df["course-index"] == "e_" + course)]["index"].values
                lab_idx = lab_idx_arr[0] if lab_idx_arr.size > 0 else ""
            exams = len(df.loc[(df["studentstudyid"] == s) & (df["index"] == lab_idx)])
            rows.append([str(exams)])
        return pd.DataFrame(np.array(rows), columns=pd.Index(["exams"]))

def get_course_grade_dict(df, courses):
    course_dict = {}
    for c in courses:
        grades = df.loc[df["Course"] == c]["course-grade"].values
        grades = np.asarray([g for g in grades if ~np.isnan(g)])
        course_dict[c] = {"grades": grades}
        try:
            course_dict[c]["median-grade"] = statistics.median(grades)
        except Exception:
            course_dict[c]["median-grade"] = np.nan
    return course_dict

def get_course_difficulties(course_dict, courses):
    very_easy, easy, difficult, very_difficult = [], [], [], []
    for c in courses:
        g = course_dict[c]["median-grade"]
        if pd.isna(g):
            very_difficult.append(c)
        elif g <= 1.5:
            very_easy.append(c)
        elif 1.6 <= g <= 2.5:
            easy.append(c)
        elif 2.6 <= g <= 3.5:
            difficult.append(c)
        else:
            very_difficult.append(c)
    return very_easy, easy, difficult, very_difficult

def get_difficulty_features(df, clf_dict):
    courses = df["Course"].unique()
    students = df["studentstudyid"].unique()
    course_dict = get_course_grade_dict(df, courses)
    very_easy, easy, difficult, very_difficult = get_course_difficulties(course_dict, courses)
    cols = ["very easy exams", "easy exams", "difficult exams", "very difficult exams"]
    rows = []
    label = clf_dict["label"]

    if label == "Overall GPA":
        for s in students:
            l = [0, 0, 0, 0]
            s_courses = df.loc[df["studentstudyid"] == s]["Course"].values
            for c in s_courses:
                if c in very_easy: l[0] += 1
                elif c in easy: l[1] += 1
                elif c in difficult: l[2] += 1
                else: l[3] += 1
            rows.append(l)
    else:
        course = clf_dict["course"]; label_index = clf_dict["label_index"]; is_atomic = clf_dict["is_atomic"]; is_pm = clf_dict["is_pm"]
        for s in students:
            lab_idx = label_index
            if not is_atomic and is_pm:
                lab_idx_arr = df.loc[(df["studentstudyid"] == s) & (df["course-index"] == "e_" + course)]["index"].values
                lab_idx = lab_idx_arr[0] if lab_idx_arr.size > 0 else ""
            l = [0, 0, 0, 0]
            s_courses = df.loc[(df["studentstudyid"] == s) & (df["index"] == lab_idx)]["Course"].values
            for c in s_courses:
                if c == course:
                    continue
                if c in very_easy: l[0] += 1
                elif c in easy: l[1] += 1
                elif c in difficult: l[2] += 1
                else: l[3] += 1
            rows.append(l)
    return pd.DataFrame(np.array(rows), columns=pd.Index(cols))

def get_features(df, clf_dict):
    features = []
    combinations = clf_dict["combinations"]
    behav_feature = diff_feature = num_feature = None

    if set(combinations) & {"behav", "diff+behav", "num+behav", "diff+num+behav", "all"}:
        behav_feature = get_behavioral_features(df, clf_dict)
    if set(combinations) & {"diff", "diff+num", "diff+behav", "diff+num+behav", "all"}:
        diff_feature = get_difficulty_features(df, clf_dict)
    if set(combinations) & {"num", "diff+num", "num+behav", "diff+num+behav", "all"}:
        num_feature = get_numerical_features(df, clf_dict)

    for comb in combinations:
        if comb == "diff":
            features.append(diff_feature)
        elif comb == "behav":
            features.append(behav_feature)
        elif comb == "num":
            features.append(num_feature)
        elif comb == "diff+num":
            features.append(pd.concat([diff_feature, num_feature], axis=1))
        elif comb == "diff+behav":
            features.append(pd.concat([diff_feature, behav_feature], axis=1))
        elif comb == "num+behav":
            features.append(pd.concat([num_feature, behav_feature], axis=1))
        elif comb == "diff+num+behav":
            features.append(pd.concat([diff_feature, num_feature, behav_feature], axis=1))
        elif comb == "all":
            features.append(pd.concat([diff_feature, num_feature, behav_feature], axis=1))
        else:
            raise ValueError(f"Combinación desconocida: {comb}")

    return features

def is_leaf(inner_tree, index):
    return inner_tree.children_left[index] == -1 and inner_tree.children_right[index] == -1

def prune_index(inner_tree, decisions, index=0):
    if not is_leaf(inner_tree, inner_tree.children_left[index]):
        prune_index(inner_tree, decisions, inner_tree.children_left[index])
    if not is_leaf(inner_tree, inner_tree.children_right[index]):
        prune_index(inner_tree, decisions, inner_tree.children_right[index])
    if (is_leaf(inner_tree, inner_tree.children_left[index]) and
        is_leaf(inner_tree, inner_tree.children_right[index]) and
        (decisions[index] == decisions[inner_tree.children_left[index]]) and
        (decisions[index] == decisions[inner_tree.children_right[index]])):
        inner_tree.children_left[index] = -1
        inner_tree.children_right[index] = -1
        inner_tree.feature[index] = -2

def prune_duplicate_leaves(clf):
    decisions = clf.tree_.value.argmax(axis=2).flatten().tolist()
    prune_index(clf.tree_, decisions)

def get_leaves(clf):
    n_nodes = clf.tree_.node_count
    children_left = clf.tree_.children_left
    children_right = clf.tree_.children_right
    return [nid for nid in range(n_nodes) if children_left[nid] == children_right[nid]]

def prepare_DT(clf, X, label_values):
    if not _GRAPHVIZ_OK:
        return None
    prune_duplicate_leaves(clf)
    leaves = get_leaves(clf)
    from sklearn import tree as _tree
    dot_data = _tree.export_graphviz(
        clf,
        feature_names=list(X.columns),
        class_names=label_values,
        filled=True,
        rounded=True,
        out_file=None,
    )
    if dot_data is None:
        return None
    graph_source = graphviz.Source(dot_data)
    graphs = pydot.graph_from_dot_data(graph_source.source)
    if not graphs:
        return None
    graph = graphs[0]
    colmap = {name: n for n, name in enumerate(set(label_values))}
    color = ["PaleGreen", "plum", "khaki", "coral", "skyblue"]
    for node in graph.get_nodes():
        if hasattr(node, "get_name") and hasattr(node, "get_label"):
            node_id = node.get_name()
            if node_id in ("node", "edge"):
                continue
            old_label = node.get_label()
            if old_label and old_label != "None" and node_id != '"\\n"':
                if int(node_id) in leaves:
                    new_label = old_label.split("class = ")[-1][:-1]
                    if hasattr(node, "set_fillcolor"):
                        node.set_fillcolor(color[colmap.get(new_label, 0)])
                    if hasattr(node, "set_color"):
                        node.set_color("black")
                    if hasattr(node, "set_label"):
                        node.set_label(new_label)
                else:
                    new_label = old_label.split("\\n", 1)[0][1:]
                    if hasattr(node, "set_fillcolor"):
                        node.set_fillcolor("white")
                    if hasattr(node, "set_color"):
                        node.set_color("black")
                    if hasattr(node, "set_label"):
                        node.set_label(new_label)
    updated_source = graph.to_string()
    updated_dot = graphviz.Source(updated_source)
    updated_dot.format = "png"
    return updated_dot

def decision_tree_to_base64(dot_obj):
    if (dot_obj is None) or (not _GRAPHVIZ_OK):
        return None
    png_bytes = dot_obj.pipe(format="png")
    b64_str = base64.b64encode(png_bytes).decode("utf-8")
    return b64_str

def get_rules(tree, feature_names, class_names):
    tree_ = tree.tree_
    feature_name = [feature_names[i] if i != -2 else "undefined!" for i in tree_.feature]
    N = tree_.n_node_samples[0]
    paths, path = [], []

    def recurse(node, path, paths):
        if tree_.feature[node] != -2:
            name = feature_name[node]
            threshold = tree_.threshold[node]
            p1, p2 = list(path), list(path)
            p1 += [f"{name} <= {np.round(threshold, 3)}"]
            recurse(tree_.children_left[node], p1, paths)
            p2 += [f"{name} > {np.round(threshold, 3)}"]
            recurse(tree_.children_right[node], p2, paths)
        else:
            path += [(tree_.value[node], tree_.n_node_samples[node])]
            paths += [path]

    recurse(0, path, paths)

    rules, all_sample_perc, all_acc = [], [], []
    for p in paths:
        rule_str = ", ".join(p[:-1])
        classes = p[-1][0][0]
        l = int(np.argmax(classes))
        acc = float(np.round(100.0 * classes[l] / np.sum(classes), 2))
        samples = int(p[-1][1])
        samples_perc = float(np.round(100.0 * samples / N, 2))
        rules.append([f"{rule_str}, class: {class_names[l] if class_names else str(l)}", acc, samples_perc, 0.0, (samples, N)])
        all_acc.append(acc); all_sample_perc.append(samples_perc)

    all_acc = np.array(all_acc); all_sample_perc = np.array(all_sample_perc)
    acc_norm = np.ones_like(all_acc) if (all_acc.max() - all_acc.min()) == 0 else (all_acc - all_acc.min()) / (all_acc.max() - all_acc.min())
    sp_norm = np.ones_like(all_sample_perc) if (all_sample_perc.max() - all_sample_perc.min()) == 0 else (all_sample_perc - all_sample_perc.min()) / (all_sample_perc.max() - all_sample_perc.min())
    for i in range(len(rules)):
        rules[i][3] = float(np.round(((acc_norm[i] + sp_norm[i]) / 2) * 100, 2))
    return rules

def cross_val(model, X, y, cv, score_dict, combi, max_depth, feature_name):
    score_dict[combi] = {"class": {}, "accuracy": []}
    Xv = X.values
    yv = y.values
    kfold = KFold(n_splits=cv, shuffle=True, random_state=100)
    clf_all = DecisionTreeClassifier(random_state=100, max_depth=max_depth, min_samples_leaf=1, min_samples_split=2)
    for _, (train, test) in enumerate(kfold.split(Xv, yv)):
        X_train, X_test = Xv[train], Xv[test]
        y_train, y_test = yv[train], yv[test]
        clf = DecisionTreeClassifier(random_state=100, max_depth=max_depth, min_samples_leaf=1, min_samples_split=2)
        clf.fit(X_train, np.ravel(y_train))
        y_pred = clf.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True)
        if report and isinstance(report, dict):
            acc = float(report.get("accuracy", 0.0))
            score_dict[combi]["accuracy"].append(round(acc, 4))
            labels = list(report.keys())[:-3]
            for lab in labels:
                if lab in report and isinstance(report[lab], dict):
                    prec = float(report[lab].get("precision", 0.0))
                    rec = float(report[lab].get("recall", 0.0))
                    if lab not in score_dict[combi]["class"]:
                        score_dict[combi]["class"][lab] = {"precision": [], "recall": []}
                    score_dict[combi]["class"][lab]["precision"].append(round(prec, 4))
                    score_dict[combi]["class"][lab]["recall"].append(round(rec, 4))
    clf_all.fit(Xv, np.ravel(yv))
    return score_dict, clf_all

def classify(features, labels, clf_dict):
    model = clf_dict["model"]
    combinations = clf_dict["combinations"]
    max_depth = clf_dict["max_depth"]

    label_values = sorted(labels[0]["label"].dropna().unique())

    score_dict = {}
    DT_names, figures, parsed = [], [], []
    error_msg = ""

    for i, feature in enumerate(features):
        X = feature
        y = labels[i].astype(str)

        if len(X) < 4:
            error_msg = f"4-fold CV requiere >= 4 muestras. Recibidas: {len(X)}"
            return score_dict, DT_names, figures, parsed, error_msg

        score_dict, clf = cross_val(model, X, y, 4, score_dict, combinations[i], max_depth, clf_dict["feature"])

        DT_dot = prepare_DT(clf, X, label_values)
        b64_img = decision_tree_to_base64(DT_dot)
        figures.append(b64_img)
        DT_names.append(combinations[i])

        try:
            rules = get_rules(clf, list(X.columns), label_values)
        except Exception as e:
            rules = f"Error generando reglas: {e}"
        parsed.append(rules)

    return score_dict, DT_names, figures, parsed, error_msg

def drop_rows(features, label_df):
    new_features = []
    mask = label_df["label"].notnull()
    for feature in features:
        new_features.append(feature[mask])
    return new_features, label_df[mask]

def get_features_label_from_dataframe(df, config):
    try:
        feature = config["feature"]
        is_atomic = config["is_atomic"]
        pm_index_type = config["index_type"]

        add_course_index(df, feature, is_atomic, pm_index_type)

        label = get_label(df, config)

        unique_labels = label["label"].dropna().unique()
        count_labels = label["label"].value_counts()
        num_labels = len(unique_labels)
        total_samples = len(label["label"].dropna())

        print(f"\n=== Class Distribution Analysis ===")
        print(f"Total samples: {total_samples}")
        print(f"Number of classes: {num_labels}")
        print("Class counts:")
        for class_val, count in count_labels.items():
            percentage = (count / total_samples) * 100
            print(f"  - Class {class_val}: {count} samples ({percentage:.1f}%)")

        if num_labels < 2:
            if num_labels > 0:
                return [], [], f"Classification not helpful:\n\nLabel needs >1 class. Got {num_labels}: {unique_labels[0]}\n{count_labels}"
            else:
                return [], [], "Classification not helpful:\n\nLabel needs >1 class. Got 0 classes."

        min_percentage = 5.0
        for class_val, count in count_labels.items():
            percentage = (count / total_samples) * 100
            if percentage < min_percentage:
                return [], [], f"Extreme class imbalance detected:\n\nClass '{class_val}' has only {count} samples ({percentage:.1f}%), which is below the minimum threshold of {min_percentage}%.\n\nThis may lead to poor recall performance as reported in the paper (Section 6.1).\nConsider:\n- Increasing sample size\n- Adjusting class thresholds\n- Using different labeling strategy\n\nClass distribution:\n{count_labels}"

        features = get_features(df, config)

        features, label = drop_rows(features, label)

        labels = [label] * len(features)
        return features, labels, ""
    except Exception as e:
        return [], [], f"Error procesando DataFrame: {str(e)}"

def submit_handler_standalone_with_dataframe(df, config):
    score_dict, DT_names, figures, parsed, error_msg = {}, [], [], [], ""
    try:
        features, labels, error_msg = get_features_label_from_dataframe(df, config)
        if features != []:
            score_dict, DT_names, figures, parsed, error_msg = classify(features, labels, config)
    except Exception as e:
        error_msg = f"Error en análisis: {str(e)}"
    return score_dict, DT_names, figures, parsed, error_msg

def main(degree_id, table_name, sample_size, config):
    try:
        print(f"Obteniendo datos para degree_id: {degree_id}")
        df_asb = format_from_dynamodb(degree_id=degree_id, table_name=table_name, sample_size=sample_size)

        print("\n=== Data Statistics ===")
        print(f"Total records: {len(df_asb)}")
        print(f"Students: {df_asb['studentstudyid'].nunique()}")
        print(f"Courses: {df_asb['Course'].nunique()}")
        print(f"Passed: {len(df_asb[df_asb['Final Course Status'] == 'PASSED'])}")
        print(f"Failed: {len(df_asb[df_asb['Final Course Status'] == 'FAILED'])}")
        print("\n=== Sample of Formatted Data ===")
        print(df_asb.head(10).to_string())
        print(f"\nSuccessfully formatted data for degree {degree_id}")

        score_dict, DT_names, figures, parsed, error_msg = submit_handler_standalone_with_dataframe(df_asb.copy(), config)
        if error_msg:
            print(f"Error: {error_msg}")
        else:
            print("Analysis completed successfully!")
            print(f"Trained models: {DT_names}")
            print(f"Scores: {score_dict}")
            if figures and figures[0]:
                print(f"Base64 image length (first): {len(figures[0])} chars")

        return score_dict, DT_names, figures, parsed, error_msg

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {}, [], [], [], f"Error en main_with_params: {str(e)}"

if __name__ == "__main__":
    degree_id = "2491"
    table_name = "AdaProjectTable"
    sample_size = None
    config = {
        "label": "Course grade",
        "course": "course-1479",
        "GPA_grades": "",
        "is_binary_label": True,
        "model": "DT",
        "max_depth": 5,
        "is_atomic": True,
        "is_pm": False,
        "index_type": "fachsemester",
        "feature": "Course-Semester",
        "label_index": 1,
        "combinations": ["behav"]
    }
    main(degree_id, table_name, sample_size, config)
