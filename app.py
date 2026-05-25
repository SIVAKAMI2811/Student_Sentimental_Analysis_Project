import pickle
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "student_feedback_secret"

# Load ML model
model, vectorizer = pickle.load(open("model/sentiment_model.pkl", "rb"))

# ---------------- DATABASE CONNECTION ---------------- #

def get_db_connection():
    db_path = os.path.abspath("database/feedback.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- LOGIN ---------------- #
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "student":
                return redirect("/student")
            elif user["role"] == "staff":
                return redirect("/staff")
            elif user["role"] == "principal":
                return redirect("/principal")

        return "Invalid login credentials"

    return render_template("login.html")


# ---------------- STUDENT DASHBOARD ---------------- #
@app.route("/student", methods=["GET", "POST"])
def student_dashboard():
    if session.get("role") != "student":
        return "Unauthorized access"

    student_id = session["username"]
    conn = get_db_connection()

    status = conn.execute(
        "SELECT has_submitted FROM student_status WHERE student_id=?",
        (student_id,)
    ).fetchone()

    if not status:
        conn.execute(
            "INSERT INTO student_status (student_id, has_submitted) VALUES (?, 0)",
            (student_id,)
        )
        conn.commit()
        has_submitted = 0
    else:
        has_submitted = status["has_submitted"]

    if has_submitted == 1:
        conn.close()
        return render_template("feedback_closed.html")

    if request.method == "POST":

        subjects = ["Tamil", "English", "Mathematics", "Science", "Social Science"]

        for subject in subjects:
            feedback_text = request.form.get(subject)

            if feedback_text:
                X = vectorizer.transform([feedback_text])
                probs = model.predict_proba(X)[0]
                labels = model.classes_

                sentiment = labels[probs.argmax()].capitalize()

                student = conn.execute(
    "SELECT class FROM users WHERE username=?",
    (student_id,)
).fetchone()

                student_class = student["class"]
                

                conn.execute(
                    """INSERT INTO feedback
                       (student_id, class, subject, teacher, feedback_text, sentiment)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (student_id, student_class, subject, subject + " Teacher", feedback_text, sentiment)
                )

        conn.execute(
            "UPDATE student_status SET has_submitted=1 WHERE student_id=?",
            (student_id,)
        )

        conn.commit()

        current_time = datetime.now().strftime("%d %B %Y, %I:%M %p")
        conn.close()

        return render_template("success.html", time=current_time)

    conn.close()
    return render_template("student.html")


# ---------------- STAFF DASHBOARD ---------------- #
@app.route("/staff")
def staff_dashboard():
    if session.get("role") != "staff":
        return "Unauthorized access"

    teacher_username = session["username"]
    conn = get_db_connection()

    teacher = conn.execute(
        "SELECT subject FROM users WHERE username=?",
        (teacher_username,)
    ).fetchone()

    if not teacher:
        conn.close()
        return "Teacher subject not found"

    subject = teacher["subject"]

    feedbacks = conn.execute(
        "SELECT feedback_text, sentiment FROM feedback WHERE subject=?",
        (subject,)
    ).fetchall()

    pos = neg = neu = 0
    for row in feedbacks:
        if row["sentiment"] == "Positive":
            pos += 1
        elif row["sentiment"] == "Negative":
            neg += 1
        else:
            neu += 1

    conn.close()

    return render_template(
        "staff_dashboard.html",
        subject=subject,
        feedbacks=feedbacks,
        pos=pos,
        neg=neg,
        neu=neu
    )


# ---------------- PRINCIPAL: CLASS LIST ---------------- #
@app.route("/principal")
def principal_classes():
    if session.get("role") != "principal":
        return "Unauthorized access"

    conn = get_db_connection()

    classes = conn.execute(
        "SELECT DISTINCT class FROM feedback"
    ).fetchall()

    conn.close()

    return render_template("principal_classes.html", classes=classes)


# ---------------- PRINCIPAL: CLASS DASHBOARD ---------------- #
@app.route("/principal/<class_name>")
def principal_dashboard(class_name):
    if session.get("role") != "principal":
        return "Unauthorized access"

    conn = get_db_connection()

    overall = conn.execute("""
        SELECT subject, sentiment, COUNT(*) as count
        FROM feedback
        WHERE class=?
        GROUP BY subject, sentiment
    """, (class_name,)).fetchall()

    data_dict = {}

    for row in overall:
        subject = row["subject"]
        sentiment = row["sentiment"]
        count = row["count"]

        if subject not in data_dict:
            data_dict[subject] = {"Positive": 0, "Negative": 0, "Neutral": 0}

        data_dict[subject][sentiment] = count

    # ✅ FIX: TOTAL FEEDBACK COUNT
    total_feedback = sum(
        v["Positive"] + v["Negative"] + v["Neutral"]
        for v in data_dict.values()
    )

    # -------- AI SUMMARY -------- #
    summary_dict = {}

    for subject in data_dict:
        feedbacks = conn.execute(
            "SELECT feedback_text FROM feedback WHERE subject=? AND class=?",
            (subject, class_name)
        ).fetchall()

        texts = [row["feedback_text"].lower() for row in feedbacks]

        pos_words = ["good", "excellent", "clear", "great"]
        neg_words = ["bad", "poor", "worst", "confusing", "not interactive"]

        pos = sum(any(w in t for w in pos_words) for t in texts)
        neg = sum(any(w in t for w in neg_words) for t in texts)

        if pos > neg:
            summary = "Students are mostly satisfied with teaching."
        elif neg > pos:
            summary = "Students expect improvement in teaching."
        else:
            summary = "Mixed feedback from students."

        summary_dict[subject] = summary

    conn.close()

    return render_template(
        "principal_dashboard.html",
        data=data_dict,
        summary=summary_dict,
        class_name=class_name,
        total_feedback=total_feedback   # ✅ VERY IMPORTANT
    )

# ---------------- LOGOUT ---------------- #
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ---------------- #
if __name__ == "__main__":
    app.run(debug=True)