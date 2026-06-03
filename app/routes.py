from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    send_file
)

import pandas as pd

from flask import make_response


from sqlalchemy import text

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle
)

from reportlab.lib import colors

from app.models import (
    db,
    Timetable,
    Subject,
    Teacher,
    Room,
    TeacherExpertise
)

from app.ortools_scheduler import run_ortools

from app.models import Student

main = Blueprint("main", __name__)

# =================================================
# HOME
# =================================================
@main.route("/")
def index():

    return render_template("index.html")


# =================================================
# LOGIN
# =================================================
@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["user"] = "admin"
            session["role"] = "admin"

            return redirect(
                url_for("main.admin")
            )

    return render_template("login.html")


# =================================================
# ADMIN DASHBOARD
# =================================================
@main.route("/admin")
def admin():

    if session.get("role") != "admin":

        return redirect("/login")

    total_subjects = Subject.query.count()

    total_teachers = Teacher.query.count()

    total_rooms = Room.query.count()

    total_routines = Timetable.query.count()

    return render_template(

        "admin_dashboard.html",

        total_subjects=total_subjects,

        total_teachers=total_teachers,

        total_rooms=total_rooms,

        total_routines=total_routines
    )


# =================================================
# LOGOUT
# =================================================
@main.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("main.login")
    )


# =================================================
# ADD TEACHER
# =================================================
@main.route(
    "/add_teacher",
    methods=["GET", "POST"]
)
def add_teacher():

    if session.get("role") != "admin":

        return redirect("/login")

    if request.method == "POST":

        teacher = Teacher(

            teacher_name=request.form[
                "teacher_name"
            ],

            department=request.form[
                "department"
            ],

            email=request.form[
                "email"
            ]
        )

        db.session.add(teacher)

        db.session.commit()

        return redirect(
            url_for("main.view_teachers")
        )

    return render_template(
        "add_teacher.html"
    )


# =================================================
# UPLOAD TEACHERS
# =================================================
@main.route(
    "/upload_teachers",
    methods=["POST"]
)
def upload_teachers():

    file = request.files["file"]

    if not file:

        return "No file uploaded"

    # READ EXCEL
    df = pd.read_excel(file)

    # REMOVE EMPTY ROWS
    df = df.dropna(
        subset=["teacher_name"]
    )

    for _, row in df.iterrows():

        teacher = Teacher(

            teacher_name=str(
                row["teacher_name"]
            ).strip(),

            department=str(
                row["department"]
            ).strip(),

            email=str(
                row["email"]
            ).strip()
        )

        db.session.add(teacher)

    db.session.commit()

    return redirect(
        url_for("main.view_teachers")
    )


# =================================================
# VIEW TEACHERS
# =================================================
@main.route("/view_teachers")
def view_teachers():

    teachers = Teacher.query.order_by(
        Teacher.teacher_name
    ).all()

    return render_template(

        "view_teachers.html",

        teachers=teachers
    )


# =================================================
# EDIT TEACHER
# =================================================
@main.route(
    "/edit_teacher/<int:id>",
    methods=["GET", "POST"]
)
def edit_teacher(id):

    teacher = Teacher.query.get_or_404(id)

    if request.method == "POST":

        teacher.teacher_name = request.form[
            "teacher_name"
        ]

        teacher.department = request.form[
            "department"
        ]

        teacher.email = request.form[
            "email"
        ]

        db.session.commit()

        return redirect(
            url_for("main.view_teachers")
        )

    return render_template(

        "edit_teacher.html",

        teacher=teacher
    )


# =================================================
# DELETE TEACHER
# =================================================
@main.route("/delete_teacher/<int:id>")
def delete_teacher(id):

    teacher = Teacher.query.get_or_404(id)

    db.session.delete(teacher)

    db.session.commit()

    return redirect(
        url_for("main.view_teachers")
    )

# =================================================
# DELETE ALL TEACHERS
# =================================================
@main.route("/delete_all_teachers")
def delete_all_teachers():

    try:

        Teacher.query.delete()

        db.session.commit()

        print("ALL TEACHERS DELETED")

    except Exception as e:

        db.session.rollback()

        print("ERROR =", e)

    return redirect("/view_teachers")

# =================================================
# ADD SUBJECT
# =================================================
@main.route(
    "/add_subject",
    methods=["GET", "POST"]
)
def add_subject():

    if request.method == "POST":

        years = request.form.getlist(
            "year[]"
        )

        semesters = request.form.getlist(
            "semester[]"
        )

        sections = request.form.getlist(
            "section[]"
        )

        subject_codes = request.form.getlist(
            "subject_code[]"
        )

        subjects = request.form.getlist(
            "subject[]"
        )

        types = request.form.getlist(
            "type[]"
        )

        credits = request.form.getlist(
            "credit[]"
        )

        for i in range(len(subjects)):

            subject_type = types[i]

            credit = int(
                credits[i]
            )

            # =================================
            # AUTO HOURS
            # =================================
            if subject_type == "lab":

                hours = 3

            else:

                hours = credit

            subject = Subject(

                year=years[i],

                semester=int(
                    semesters[i]
                ),

                section=sections[i],

                subject_code=subject_codes[i],

                subject_name=subjects[i],

                subject_type=subject_type,

                credit=credit,

                hours=hours
            )

            db.session.add(subject)

        db.session.commit()

        return redirect(
            url_for("main.subjects")
        )

    return render_template(
        "add_subject.html"
    )


# =================================================
# UPLOAD SUBJECTS
# =================================================
@main.route(
    "/upload_subjects",
    methods=["POST"]
)
def upload_subjects():

    file = request.files["file"]

    if not file:

        return "No File Uploaded"

    df = pd.read_excel(file)

    # =========================================
    # REMOVE EXTRA SPACES FROM HEADERS
    # =========================================
    df.columns = df.columns.str.strip()

    print(df.columns.tolist())

    for _, row in df.iterrows():

        # =====================================
        # SKIP DUPLICATE SUBJECT CODES
        # =====================================
        existing = Subject.query.filter_by(
            subject_code=str(
                row["subject_code"]
            ).strip()
        ).first()

        if existing:

            print(
                "DUPLICATE SKIPPED:",
                row["subject_code"]
            )

            continue

        subject_type = str(
            row["subject_type"]
        ).strip().lower()

        credit = int(
            row["credit"]
        )

        # =====================================
        # AUTO HOURS
        # =====================================
        if subject_type == "lab":

            hours = 3

        else:

            hours = credit

        subject = Subject(

            year=str(
                row["Year"]
            ).strip(),

            semester=int(
                row["semester"]
            ),

            section=str(
                row["section"]
            ).strip(),

            subject_code=str(
                row["subject_code"]
            ).strip(),

            subject_name=str(
                row["subject_name"]
            ).strip(),

            subject_type=subject_type,

            credit=credit,

            hours=hours
        )

        db.session.add(subject)

    db.session.commit()

    print("SUBJECTS UPLOADED")

    return redirect(
        url_for("main.subjects")
    )

# =================================================
# VIEW SUBJECTS
# =================================================
@main.route("/subjects")
def subjects():

    data = Subject.query.order_by(
        Subject.id
    ).all()

    return render_template(

        "subjects.html",

        subjects=data
    )


# =================================================
# EDIT SUBJECT
# =================================================
@main.route(
    "/edit_subject/<int:id>",
    methods=["GET", "POST"]
)
def edit_subject(id):

    subject = Subject.query.get_or_404(id)

    if request.method == "POST":

        subject.year = request.form[
            "year"
        ]

        subject.semester = int(
            request.form["semester"]
        )

        subject.section = request.form[
            "section"
        ]

        subject.subject_code = request.form[
            "subject_code"
        ]

        subject.subject_name = request.form[
            "subject_name"
        ]

        subject.subject_type = request.form[
            "subject_type"
        ]

        subject.credit = int(
            request.form["credit"]
        )

        # =================================
        # AUTO HOURS
        # =================================
        if subject.subject_type == "lab":

            subject.hours = 3

        else:

            subject.hours = subject.credit

        db.session.commit()

        return redirect(
            url_for("main.subjects")
        )

    return render_template(

        "edit_subject.html",

        subject=subject
    )


# =================================================
# DELETE SINGLE SUBJECT
# =================================================
@main.route("/delete_subject/<int:id>")
def delete_subject(id):

    try:

        subject = Subject.query.get_or_404(id)

        Timetable.query.filter_by(
            subject=subject.subject_name
        ).delete()

        TeacherExpertise.query.filter_by(
            subject_name=subject.subject_name
        ).delete()

        db.session.delete(subject)

        db.session.commit()

        print("SUBJECT DELETED")

    except Exception as e:

        db.session.rollback()

        print("DELETE ERROR =", e)

    return redirect("/subjects")


# =================================================
# DELETE ALL SUBJECTS
# =================================================
@main.route("/delete_all_subjects")
def delete_all_subjects():

    try:

        Timetable.query.delete()

        TeacherExpertise.query.delete()

        Subject.query.delete()

        db.session.commit()

        print(
            "ALL SUBJECTS DELETED"
        )

    except Exception as e:

        db.session.rollback()

        print("ERROR =", e)

    return redirect("/subjects")


# =================================================
# GENERATE ROUTINE
# =================================================
@main.route(
    "/generate",
    methods=["POST"]
)
def generate():

    db.session.query(
        Timetable
    ).delete()

    db.session.commit()

    timetable = run_ortools()

    for row in timetable:

        (
            day,
            period,
            year,
            semester,
            section,
            subject,
            teacher,
            typ,
            room
        ) = row

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

    return redirect(
        url_for("main.view")
    )


# =================================================
# VIEW TIMETABLE
# =================================================
@main.route("/view")
def view():

    timetable = Timetable.query.all()

    formatted = []

    for t in timetable:

        formatted.append(

            (
                t.day,
                t.period,
                t.year,
                t.semester,
                t.section,
                t.subject,
                t.teacher,
                t.class_type,
                t.room
            )
        )

    return render_template(

        "timetable.html",

        timetable=formatted,

        title="All Sections"
    )


# =================================================
# VIEW SECTION TIMETABLE
# =================================================
@main.route(
    "/view/<year>/<semester>/<section>"
)
def view_section(
    year,
    semester,
    section
):

    timetable = Timetable.query.filter_by(

        year=year,

        semester=int(semester),

        section=section

    ).all()

    print(
        "TIMETABLE SIZE =",
        len(timetable)
    )

    formatted = []

    for t in timetable:

        formatted.append(

            (
                t.day,
                t.period,
                t.year,
                t.semester,
                t.section,
                t.subject,
                t.teacher,
                t.class_type,
                t.room
            )
        )

    return render_template(

        "timetable.html",

        timetable=formatted,

        title=f"{year} Sem-{semester} Section-{section}"
    )


# =================================================
# TEACHER LIST
# =================================================
@main.route("/teachers")
def teachers():

    teacher_list = Teacher.query.order_by(
        Teacher.teacher_name
    ).all()

    return render_template(

        "teachers.html",

        teachers=teacher_list
    )


# =================================================
# TEACHER TIMETABLE
# =================================================
@main.route("/teacher/<name>")
def teacher_view(name):

    data = Timetable.query.filter_by(
        teacher=name
    ).order_by(

        Timetable.day,

        Timetable.period
    ).all()

    return render_template(

        "teacher_timetable.html",

        timetable=data,

        teacher=name
    )


# =================================================
# ADD TEACHER EXPERTISE
# =================================================
@main.route(
    "/add_expertise",
    methods=["GET", "POST"]
)
def add_expertise():

    teachers = Teacher.query.all()

    if request.method == "POST":

        expertise = TeacherExpertise(

            teacher_id=int(
                request.form[
                    "teacher_id"
                ]
            ),

            subject_name=request.form[
                "subject_name"
            ]
        )

        db.session.add(expertise)

        db.session.commit()

        return redirect(
            url_for(
                "main.view_expertise"
            )
        )

    return render_template(

        "add_expertise.html",

        teachers=teachers
    )


# =================================================
# UPLOAD EXPERTISE
# =================================================
@main.route(
    "/upload_expertise",
    methods=["POST"]
)
def upload_expertise():

    file = request.files["file"]

    if not file:

        return "No file uploaded"

    df = pd.read_excel(file)

    for _, row in df.iterrows():

        teacher = Teacher.query.filter_by(

            teacher_name=row[
                "teacher_name"
            ]

        ).first()

        if teacher:

            expertise = TeacherExpertise(

                teacher_id=teacher.id,

                subject_name=row[
                    "subject_name"
                ]
            )

            db.session.add(expertise)

    db.session.commit()

    return redirect(
        url_for(
            "main.view_expertise"
        )
    )


# =================================================
# DELETE ALL EXPERTISE
# =================================================
@main.route("/delete_all_expertise")
def delete_all_expertise():

    try:

        TeacherExpertise.query.delete()

        db.session.commit()

        print("ALL EXPERTISE DELETED")

    except Exception as e:

        db.session.rollback()

        print("ERROR =", e)

    return redirect("/view_expertise")


# =================================================
# VIEW EXPERTISE
# =================================================
@main.route("/view_expertise")
def view_expertise():

    expertise = TeacherExpertise.query.all()

    return render_template(

        "view_expertise.html",

        expertise=expertise
    )

from sqlalchemy import text


# =========================================
# TEACHER ANALYTICS
# =========================================

@main.route("/teacher_analytics")
def teacher_analytics():

    timetable = db.session.execute(text("""

        SELECT *
        FROM timetable

    """)).fetchall()

    teacher_data = {}

    for row in timetable:

        teacher = row[6]

        if teacher not in teacher_data:

            teacher_data[teacher] = {
                "classes": 0,
                "free": 40,
                "load": 0
            }

        teacher_data[teacher]["classes"] += 1

    for teacher in teacher_data:

        teacher_data[teacher]["free"] = \
        40 - teacher_data[teacher]["classes"]

        teacher_data[teacher]["load"] = round(

            (
                teacher_data[teacher]["classes"]
                / 40
            ) * 100,

            2
        )

    return render_template(

        "teacher_analytics.html",

        teacher_data=teacher_data
    )


# =========================================
# SECTION ANALYTICS
# =========================================

@main.route("/section_analytics")
def section_analytics():

    timetable = db.session.execute(text("""

        SELECT *
        FROM timetable

    """)).fetchall()

    section_data = {}

    for row in timetable:

        key = f"Sem {row[3]} - Section {row[4]}"

        if key not in section_data:

            section_data[key] = {

                "total": 0,
                "theory": 0,
                "lab": 0
            }

        section_data[key]["total"] += 1

        if row[7] == "lab":

            section_data[key]["lab"] += 1

        else:

            section_data[key]["theory"] += 1

    return render_template(

        "section_analytics.html",

        section_data=section_data
    )


# =========================================
# TIMETABLE STATS
# =========================================

@main.route("/timetable_stats")
def timetable_stats():

    timetable = db.session.execute(text("""

        SELECT *
        FROM timetable

    """)).fetchall()

    total_slots = 48

    used_slots = len(timetable)

    utilization = round(

        (
            used_slots /
            total_slots
        ) * 100,

        2
    )

    room_usage = 78

    teacher_engagement = 86

    return render_template(

        "timetable_stats.html",

        utilization=utilization,

        room_usage=room_usage,

        teacher_engagement=teacher_engagement
    )

# =================================================
# EXPORT ROUTINE EXCEL
# =================================================
@main.route("/export_excel")
def export_excel():

    import pandas as pd

    import os

    from flask import send_file

    timetable = Timetable.query.all()

    # =========================
    # PERIODS
    # =========================

    periods = {

        1: "9-10",
        2: "10-11",
        3: "11-12",
        4: "12-1",
        5: "1-2",
        6: "2-3",
        7: "3-4",
        8: "4-5"
    }

    # =========================
    # DAYS
    # =========================

    days = [

        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat"
    ]

    # =========================
    # CREATE TABLE
    # =========================

    table_data = []

    for day in days:

        row = {

            "Day": day
        }

        # FREE SLOT DEFAULT
        for p in range(1, 9):

            row[
                periods[p]
            ] = "FREE"

        # ADD SUBJECTS
        for t in timetable:

            if t.day == day:

                row[
                    periods[t.period]
                ] = (

                    f"{t.subject}\n"
                    f"MCA Sem {t.semester} • Section {t.section}\n"
                    f"👨‍🏫 {t.teacher}\n"
                    f"📍 {t.room}"
                )

        table_data.append(row)

    # =========================
    # DATAFRAME
    # =========================

    df = pd.DataFrame(table_data)

    # =========================
    # FILE PATH
    # =========================

    file_path = os.path.join(

        os.getcwd(),

        "routine.xlsx"
    )

    # =========================
    # SAVE EXCEL
    # =========================

    with pd.ExcelWriter(

        file_path,

        engine="openpyxl"

    ) as writer:

        df.to_excel(

            writer,

            index=False,

            sheet_name="Routine"
        )

        ws = writer.sheets[
            "Routine"
        ]

        # =========================
        # COLUMN WIDTH
        # =========================

        for col in ws.columns:

            ws.column_dimensions[
                col[0].column_letter
            ].width = 35

        # =========================
        # ROW HEIGHT
        # =========================

        for row in range(2, 20):

            ws.row_dimensions[
                row
            ].height = 110

    print("ROUTINE EXCEL GENERATED")

    # =========================
    # DOWNLOAD FILE
    # =========================

    return send_file(

        file_path,

        as_attachment=True,

        download_name="routine.xlsx"
    )


# =================================================
# EXPORT ROUTINE PDF
# =================================================
@main.route("/export_pdf")
def export_pdf():

    import pdfkit

    from flask import make_response

    # =========================
    # WKHTMLTOPDF CONFIG
    # =========================

    config = pdfkit.configuration(

        wkhtmltopdf=
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    # =========================
    # OPTIONS
    # =========================

    options = {

        "enable-local-file-access": "",

        "page-size": "A3",

        "orientation": "Landscape",

        "encoding": "UTF-8",

        "margin-top": "0mm",

        "margin-right": "0mm",

        "margin-bottom": "0mm",

        "margin-left": "0mm",

        "zoom": "1.0",

        "disable-smart-shrinking": "",

        "background": ""
    }

    # =========================
    # GENERATED ROUTINE URL
    # =========================

    url = "http://127.0.0.1:5000/view"

    # =========================
    # GENERATE PDF
    # =========================

    pdf = pdfkit.from_url(

        url,

        False,

        configuration=config,

        options=options
    )

    # =========================
    # RESPONSE
    # =========================

    response = make_response(pdf)

    response.headers[
        "Content-Type"
    ] = "application/pdf"

    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=routine.pdf"

    return response


# =================================================
# TEACHER LIST PAGE
# =================================================
@main.route("/teachers")
def teachers_page():

    teachers = Teacher.query.all()

    return render_template(

        "teachers.html",

        teachers=teachers
    )


# =================================================
# SINGLE TEACHER ROUTINE
# =================================================
@main.route("/teacher_routine/<teacher>")
def teacher_routine(teacher):

    timetable = Timetable.query.filter_by(
        teacher=teacher
    ).all()

    return render_template(

        "teacher_routine.html",

        timetable=timetable,

        teacher=teacher
    )



# =================================================

# STUDENT REGISTER

# =================================================

@main.route(
"/student_register",
methods=["GET", "POST"]
)
def student_register():


    if request.method == "POST":

        email = request.form["email"]

        existing = Student.query.filter_by(
            email=email
        ).first()

        if existing:

            return render_template(
            "student_register.html",
            error="Email already registered"
        )

        student = Student(

        name=request.form["name"],

        email=request.form["email"],

        semester=int(
            request.form["semester"]
        ),

        section=request.form["section"],

        password=request.form["password"]

    )

        db.session.add(student)

        db.session.commit()

        return redirect(
        url_for(
            "main.student_login"
        )
    )

    return render_template(
        "student_register.html"
    )



# =================================================
# STUDENT LOGIN
# =================================================

@main.route(
    "/student_login",
    methods=["GET", "POST"]
)
def student_login():

    if request.method == "POST":

        student = Student.query.filter_by(

            email=request.form["email"],

            password=request.form["password"]

        ).first()

        if student:

            session["student_id"] = student.id

            session["semester"] = student.semester

            session["section"] = student.section

            session["role"] = "student"

            return redirect(
                url_for(
                    "main.student_dashboard"
                )
            )

        return render_template(

            "student_login.html",

            error="Invalid Email or Password"

        )

    return render_template(
        "student_login.html"
    )


# =================================================
# STUDENT LOGOUT
# =================================================

@main.route("/student_logout")
def student_logout():

    session.pop(
        "student_id",
        None
    )

    session.pop(
        "semester",
        None
    )

    session.pop(
        "section",
        None
    )

    session.pop(
        "role",
        None
    )

    return redirect(
        url_for(
            "main.student_login"
        )
    )




# =================================================
# STUDENT DASHBOARD
# =================================================

@main.route(
    "/student_dashboard"
)
def student_dashboard():

    if session.get("role") != "student":

        return redirect(
            url_for(
                "main.student_login"
            )
        )

    return render_template(
        "student_dashboard.html"
    )

# =================================================
# STUDENT ROUTINE
# =================================================

@main.route("/student_routine")
def student_routine():

    if session.get("role") != "student":

        return redirect(
            url_for("main.student_login")
        )

    timetable = Timetable.query.filter_by(

        year="MCA",

        semester=session["semester"],

        section=session["section"]

    ).all()

    formatted = []

    for t in timetable:

        formatted.append(

            (
                t.day,
                t.period,
                t.year,
                t.semester,
                t.section,
                t.subject,
                t.teacher,
                t.class_type,
                t.room
            )
        )

    return render_template(

        "timetable.html",

        timetable=formatted,

        title=f"MCA Sem-{session['semester']} Section-{session['section']}"

    )