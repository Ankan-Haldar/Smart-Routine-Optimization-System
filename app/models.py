from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# =================================================
# USER
# =================================================
class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="user"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<User {self.username}>"


# =================================================
# TEACHER
# =================================================
class Teacher(db.Model):

    __tablename__ = "teachers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    teacher_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    email = db.Column(
        db.String(100),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Teacher {self.teacher_name}>"


# =================================================
# TEACHER EXPERTISE
# =================================================
class TeacherExpertise(db.Model):

    __tablename__ = "teacher_expertise"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teachers.id"),
        nullable=False
    )

    subject_name = db.Column(
        db.String(100),
        nullable=False
    )

    teacher = db.relationship(
        "Teacher",
        backref="expertise"
    )

    def __repr__(self):
        return f"<Expertise {self.subject_name}>"


# =================================================
# SUBJECT
# =================================================
class Subject(db.Model):

    __tablename__ = "subjects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    year = db.Column(
        db.String(10),
        nullable=False
    )

    semester = db.Column(
        db.Integer,
        nullable=False
    )

    section = db.Column(
        db.String(5),
        nullable=False
    )

    subject_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    subject_name = db.Column(
        db.String(100),
        nullable=False
    )

    subject_type = db.Column(
        db.String(20),
        nullable=False
    )

    # NEW
    credit = db.Column(
        db.Integer,
        nullable=False
    )

    # AUTO GENERATED HOURS
    hours = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Subject {self.subject_name}>"


# =================================================
# ROOM
# =================================================
class Room(db.Model):

    __tablename__ = "rooms"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    room_name = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    room_type = db.Column(
        db.String(20),
        nullable=False
    )

    capacity = db.Column(
        db.Integer,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Room {self.room_name}>"


# =================================================
# TIMETABLE
# =================================================
class Timetable(db.Model):

    __tablename__ = "timetable"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    day = db.Column(
        db.String(20),
        nullable=False
    )

    period = db.Column(
        db.Integer,
        nullable=False
    )

    year = db.Column(
        db.String(10),
        nullable=False
    )

    semester = db.Column(
        db.Integer,
        nullable=False
    )

    section = db.Column(
        db.String(5),
        nullable=False
    )

    subject = db.Column(
        db.String(100),
        nullable=False
    )

    teacher = db.Column(
        db.String(100),
        nullable=False
    )

    class_type = db.Column(
        db.String(20),
        nullable=False
    )

    room = db.Column(
        db.String(20),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Timetable {self.day} Period-{self.period}>"
    

class Student(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100)
    )

    email = db.Column(
        db.String(120),
        unique=True
    )

    semester = db.Column(
        db.Integer
    )

    section = db.Column(
        db.String(10)
    )

    password = db.Column(
        db.String(100)
    )