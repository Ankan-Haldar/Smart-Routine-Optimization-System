from flask import Blueprint, render_template, redirect, url_for, request, session
from app.ga_optimizer import run_ga
from app.models import db, Timetable, Subject, User
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import pandas as pd
from flask import send_file
from io import BytesIO
import pandas as pd
from app.ortools_scheduler import run_ortools
from app.models import Subject


main = Blueprint("main", __name__)


# ---------------- HOME ----------------
@main.route("/")
def index():
    return render_template("index.html")


# ---------------- LOGIN ----------------
@main.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = "admin"
            session["role"] = "admin"   # IMPORTANT
            return redirect(url_for("main.index"))

    return render_template("login.html")

# ---------------- ADMIN DASHBOARD ----------------
@main.route("/admin")
def admin():

    if session.get("role") != "admin":
        return redirect("/login")

    return render_template("admin_dashboard.html")


# ---------------- LOGOUT ----------------
@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


# ---------------- ADD SUBJECT ----------------
@main.route("/add_subject", methods=["GET", "POST"])
def add_subject():

    if session.get("role") != "admin":
        return redirect("/login")

    if request.method == "POST":

        years = request.form.getlist("year[]")
        semesters = request.form.getlist("semester[]")
        sections = request.form.getlist("section[]")
        subjects = request.form.getlist("subject[]")
        teachers = request.form.getlist("teacher[]")
        types = request.form.getlist("type[]")
        hours = request.form.getlist("hours[]")

        for i in range(len(subjects)):

            row = Subject(
                year=years[i],
                semester=semesters[i],
                section=sections[i],
                subject_name=subjects[i],
                teacher=teachers[i],
                subject_type=types[i],
                hours=hours[i]
            )

            db.session.add(row)

        db.session.commit()
        return redirect("/subjects")

    return render_template("add_subject.html")


# ---------------- UPLOAD SUBJECTS ----------------
@main.route("/upload_subjects", methods=["POST"])
def upload_subjects():

    file = request.files["file"]
    df = pd.read_excel(file)

    # normalize headers
    df.columns = df.columns.str.strip().str.lower()

    # IMPORTANT: clear old data
    db.session.query(Subject).delete()
    db.session.commit()

    for _, row in df.iterrows():

        if pd.isna(row["subject"]):
            continue

        subject = Subject(
            year=str(row["year"]).strip(),
            semester=str(row["semester"]).strip(),
            section=str(row["section"]).strip(),
            subject_name=str(row["subject"]).strip(),
            teacher=str(row["teacher"]).strip(),
            subject_type=str(row["subject_type"]).strip(),
            hours=int(row["hours"])
        )

        db.session.add(subject)

    db.session.commit()
    return redirect("/subjects")
# ---------------- GENERATE ROUTINE ----------------
@main.route("/generate", methods=["POST"])
def generate():

    db.session.query(Timetable).delete()
    db.session.commit()

    from app.ortools_scheduler import run_ortools
    timetable = run_ortools()

    for row in timetable:

        day, period, year, semester, section, subject, teacher, typ, room = row

        db.session.add(
            Timetable(
                day=day,
                period=period,
                year=year,
                semester=semester,
                section=section,
                subject=subject,
                teacher=teacher,
                class_type=typ,
                room=room
            )
        )

    db.session.commit()

    return redirect(url_for("main.view"))
# ---------------- VIEW ALL ----------------
@main.route("/view")
def view():

    data = Timetable.query.order_by(
        Timetable.day,
        Timetable.period
    ).all()

    return render_template(
        "timetable.html",
        timetable=data,
        title="All Sections"
    )


# ---------------- VIEW SECTION ----------------
@main.route("/view/<year>/<semester>/<section>")
def view_section(year, semester, section):

    data = Timetable.query.filter_by(
        year=year,
        semester=semester,
        section=section
    ).order_by(
        Timetable.day,
        Timetable.period
    ).all()

    return render_template(
        "timetable.html",
        timetable=data,
        title=f"{year} Sem{semester}-{section}"
    )


# ---------------- SUBJECT LIST ----------------
@main.route("/subjects")
def subjects():

    if session.get("role") != "admin":
        return redirect("/login")

    data = Subject.query.order_by(Subject.id).all()

    return render_template(
        "subjects.html",
        subjects=data
    )

# ---------------- EDIT SUBJECT ----------------
@main.route("/edit_subject/<int:id>", methods=["GET", "POST"])
def edit_subject(id):

    if session.get("role") != "admin":
        return redirect("/login")

    subject = Subject.query.get_or_404(id)

    if request.method == "POST":

        subject.year = request.form["year"]
        subject.semester = request.form["semester"]
        subject.section = request.form["section"]

        # ✅ FIXED
        subject.subject_name = request.form["subject_name"]

        subject.teacher = request.form["teacher"]

        # ✅ FIXED
        subject.subject_type = request.form["subject_type"]

        subject.hours = request.form["hours"]

        db.session.commit()

        return redirect(url_for("main.subjects"))

    return render_template(
        "edit_subject.html",
        subject=subject
    )


# ---------------- DELETE SUBJECT ----------------
@main.route("/delete_subject/<int:id>")
def delete_subject(id):

    if session.get("role") != "admin":
        return redirect("/login")

    subject = Subject.query.get_or_404(id)

    db.session.delete(subject)
    db.session.commit()

    return redirect(url_for("main.subjects"))




@main.route("/teacher")
def teacher_select():

    name = request.args.get("name")

    if not name:
        return "No teacher selected"

    data = run_ortools()

    teacher_data = [
        x for x in data
        if x[6].strip().lower() == name.strip().lower()
    ]

    return render_template(
        "teacher_timetable.html",
        timetable=teacher_data,
        teacher=name
    )



@main.route("/teacher/<name>")
def teacher_view(name):

    data = run_ortools()

    teacher_data = [
        x for x in data
        if x[6].strip().lower() == name.strip().lower()
    ]

    return render_template(
        "teacher_timetable.html",
        timetable=teacher_data,
        teacher=name
    )

from app.models import Subject

@main.route("/teachers")
def teachers():

    subjects = Subject.query.all()

    teacher_list = list(set([s.teacher for s in subjects]))

    return render_template(
        "teachers.html",
        teachers=teacher_list
    )
@main.route("/view_teachers")
def view_teachers():
    from app.models import Subject

    teachers = {}

    for s in Subject.query.all():
        if s.teacher:   
            teachers[s.teacher] = teachers.get(s.teacher, 0) + 1

    total = len(teachers)   

    return render_template(
        "view_teachers.html",
        teachers=teachers,
        total=total
    )