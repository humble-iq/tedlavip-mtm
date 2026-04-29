import os
import re
import pandas as pd
import chardet


# ---------------- CLEAN TEXT ----------------
def clean_text(value):
    if value is None:
        return ""

    value = str(value)

    value = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", value)

    if "PK" in value and "<?xml" in value:
        return ""

    return value.strip()


# ---------------- SAFE READER ----------------
def read_file_safely(path):
    with open(path, "rb") as f:
        raw = f.read()
        encoding = chardet.detect(raw)["encoding"] or "utf-8"

    return raw.decode(encoding, errors="ignore")


# ---------------- MTM PARSER (WITH STATUS) ----------------
def parse_mtm(text):
    lines = text.split("\n")
    trips = []
    current = {}

    for line in lines:
        line = clean_text(line)
        if not line:
            continue

        # NEW TRIP
        if line[:2].isdigit() and "-" in line:
            if current:
                trips.append(current)
            current = {"Trip ID": line.split()[0]}

        # NAME
        if "Age:" in line:
            current["Rider Name"] = line.split("Age:")[0].strip()

        # PU
        if "PU" in line:
            current["PU Address"] = line

        # DO
        if "DO" in line:
            current["DO Address"] = line

        # MILES
        if "Miles:" in line:
            current["Miles"] = line.split("Miles:")[-1].strip()

        # STATUS DETECTION (NEW 🔥)
        if "NEW" in line:
            current["Status"] = "NEW"
        elif "CANCEL" in line:
            current["Status"] = "CANCEL"
        elif "COMPLETED" in line:
            current["Status"] = "COMPLETED"

    if current:
        trips.append(current)

    return trips


# ---------------- MAIN PROCESS ----------------
def process_file(input_path, output_folder):

    text = read_file_safely(input_path)
    trips = parse_mtm(text)

    df = pd.DataFrame(trips)

    # ensure all columns exist
    cols = ["Trip ID", "Rider Name", "PU Address", "DO Address", "Miles", "Status"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    df = df.astype(str).apply(lambda col: col.map(clean_text))

    txt_path = os.path.join(output_folder, "converted.txt")
    excel_path = os.path.join(output_folder, "converted.xlsx")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(df.to_string(index=False))

    df.to_excel(excel_path, index=False, engine="openpyxl")

    return txt_path, excel_path, df.to_dict(orient="records")