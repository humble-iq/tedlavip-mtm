from flask import Flask, request, jsonify, render_template
import pandas as pd

app = Flask(__name__)

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

# ================= EDITOR =================
@app.route("/editor")
def editor():
    return render_template("editor.html")

# ================= UPLOAD =================
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files.get("file")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        df = pd.read_excel(file)

        # ================= CLEAN COLUMNS =================
        df.columns = df.columns.astype(str).str.strip()

        # ================= TIME → 24 HOUR =================
        if "Time" in df.columns:
            df["Time"] = pd.to_datetime(df["Time"], errors="coerce").dt.strftime("%H:%M")

        # ================= GET LEG =================
        if "Trip Number" in df.columns:
            df["LEG_SORT"] = df["Trip Number"].astype(str).str[-1].str.upper()
        elif "Trip ID" in df.columns:
            df["LEG_SORT"] = df["Trip ID"].astype(str).str[-1].str.upper()
        else:
            df["LEG_SORT"] = ""

        # convert LEG letter → number for sorting
        df["LEG_SORT"] = df["LEG_SORT"].map({
            "A": 1,
            "B": 2,
            "C": 3,
            "D": 4,
            "E": 5,
            "F": 6,
            "G": 7,
            "H": 8,
        }).fillna(99)

        # ================= DETECT NAME COLUMNS =================
        first_col = "Member's First Name" if "Member's First Name" in df.columns else "First Name"
        last_col = "Member's Last Name" if "Member's Last Name" in df.columns else "Last Name"

        # ================= FINAL SORT =================
        df = df.sort_values(
            by=[first_col, last_col, "LEG_SORT"],
            key=lambda col: col.astype(str).str.lower() if col.name != "LEG_SORT" else col,
            ascending=True
        ).drop(columns=["LEG_SORT"]).reset_index(drop=True)

        # ================= RETURN =================
        return jsonify({
            "columns": df.columns.tolist(),
            "data": df.fillna("").to_dict(orient="records")
        })

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5050)
    