from ortools.sat.python import cp_model

from app.models import (
    Subject,
    TeacherExpertise
)


# =================================================
# DAYS & PERIODS
# =================================================
DAYS = [
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat"
]

PERIODS = [1, 2, 3, 4, 5, 6, 7, 8]


# =================================================
# TIME SLOTS
# =================================================
TIME_SLOTS = {

    1: "9:00 - 10:00",
    2: "10:00 - 11:00",
    3: "11:00 - 12:00",
    4: "12:00 - 1:00",
    5: "1:00 - 2:00",
    6: "2:00 - 3:00",
    7: "3:00 - 4:00",
    8: "4:00 - 5:00"
}


# =================================================
# ROOMS
# =================================================
THEORY_ROOMS = [
    "G01",
    "G02",
    "G03",
    "G04",
    "G05",
    "G06",
    "G07",
    "G08",
    "G09",
    "G10"
]

LAB_ROOMS = [
    "LAB1",
    "LAB2",
    "LAB3",
    "LAB4",
    "LAB5",
    "LAB6"
]


# =================================================
# FIND TEACHER
# =================================================
def get_teacher(subject_name):

    expertise = TeacherExpertise.query.filter_by(
        subject_name=subject_name
    ).first()

    if expertise:

        return expertise.teacher.teacher_name

    return "Unknown"


# =================================================
# MAIN FUNCTION
# =================================================
def run_ortools():

    model = cp_model.CpModel()

    subjects = Subject.query.all()

    print("TOTAL SUBJECTS =", len(subjects))

    for s in subjects:

        print(
            s.year,
            s.semester,
            s.section,
            s.subject_name
        )

    if not subjects:

        print("❌ No subjects found")

        return []

    timetable = []

    slots = {}

    room_assign = {}

    groups = set(

        (
            s.year,
            s.semester,
            s.section
        )

        for s in subjects
    )

    # =================================================
    # VARIABLES
    # =================================================
    for s in subjects:

        g = (
            s.year,
            s.semester,
            s.section
        )

        for d in range(len(DAYS)):

            for p in range(len(PERIODS)):

                slots[(s.id, g, d, p)] = (
                    model.NewBoolVar(
                        f"slot_{s.id}_{d}_{p}"
                    )
                )

                room_list = (

                    THEORY_ROOMS

                    if s.subject_type == "theory"

                    else LAB_ROOMS
                )

                for r in room_list:

                    room_assign[
                        (s.id, g, d, p, r)
                    ] = model.NewBoolVar(

                        f"room_{s.id}_{d}_{p}_{r}"

                    )

    # =================================================
    # SUBJECT HOURS
    # =================================================
    for s in subjects:

        g = (
            s.year,
            s.semester,
            s.section
        )

        model.Add(

            sum(

                slots[(s.id, g, d, p)]

                for d in range(len(DAYS))

                for p in range(len(PERIODS))

            )

            == s.hours
        )

    # =================================================
    # ONE SUBJECT PER SLOT
    # =================================================
    for g in groups:

        for d in range(len(DAYS)):

            for p in range(len(PERIODS)):

                model.Add(

                    sum(

                        slots[(s.id, g, d, p)]

                        for s in subjects

                        if (
                            s.year,
                            s.semester,
                            s.section
                        ) == g

                    )

                    <= 1
                )

    # =================================================
    # TEACHER CLASH
    # =================================================
    teachers = set(

        get_teacher(s.subject_name)

        for s in subjects
    )

    for d in range(len(DAYS)):

        for p in range(len(PERIODS)):

            for t in teachers:

                model.Add(

                    sum(

                        slots[
                            (
                                s.id,
                                (
                                    s.year,
                                    s.semester,
                                    s.section
                                ),
                                d,
                                p
                            )
                        ]

                        for s in subjects

                        if (
                            get_teacher(
                                s.subject_name
                            ) == t
                        )

                    )

                    <= 1
                )

    # =================================================
    # SAME SUBJECT DAILY LIMIT
    # =================================================
    for s in subjects:

        g = (
            s.year,
            s.semester,
            s.section
        )

        for d in range(len(DAYS)):

            limit = 2

            if s.subject_type == "lab":
                limit = 3

            model.Add(

                sum(

                    slots[(s.id, g, d, p)]

                    for p in range(len(PERIODS))

                )

                <= limit
            )

    # =================================================
    # LAB = 3 CONSECUTIVE PERIODS
    # =================================================
    for s in subjects:

        if s.subject_type == "lab":

            g = (
                s.year,
                s.semester,
                s.section
            )

            lab_starts = []

            for d in range(len(DAYS)):

                for p in range(len(PERIODS) - 2):

                    start_var = model.NewBoolVar(
                        f"lab_{s.id}_{d}_{p}"
                    )

                    lab_starts.append(start_var)

                    model.Add(
                        slots[(s.id, g, d, p)] >= start_var
                    )

                    model.Add(
                        slots[(s.id, g, d, p + 1)] >= start_var
                    )

                    model.Add(
                        slots[(s.id, g, d, p + 2)] >= start_var
                    )

            model.Add(
                sum(lab_starts) == 1
            )

    # =================================================
    # ROOM LINK
    # =================================================
    for s in subjects:

        g = (
            s.year,
            s.semester,
            s.section
        )

        room_list = (

            THEORY_ROOMS

            if s.subject_type == "theory"

            else LAB_ROOMS
        )

        for d in range(len(DAYS)):

            for p in range(len(PERIODS)):

                model.Add(

                    sum(

                        room_assign[
                            (
                                s.id,
                                g,
                                d,
                                p,
                                r
                            )
                        ]

                        for r in room_list

                    )

                    == slots[(s.id, g, d, p)]
                )


# =================================================
# THEORY CONSECUTIVE SAME ROOM
# =================================================

    for s in subjects:

        if s.subject_type == "theory":

            g = (
            s.year,
            s.semester,
            s.section
        )

            for d in range(len(DAYS)):

                for p in range(len(PERIODS) - 1):

                    for r in THEORY_ROOMS:

                        current_room = room_assign[
                        (
                            s.id,
                            g,
                            d,
                            p,
                            r
                        )
                    ]

                        next_room = room_assign[
                        (
                            s.id,
                            g,
                            d,
                            p + 1,
                            r
                        )
                    ]

                        model.Add(
                        current_room == next_room
                    ).OnlyEnforceIf([
                        slots[(s.id, g, d, p)],
                        slots[(s.id, g, d, p + 1)]
                    ])

# =================================================
# ROOM CLASH
# =================================================
    for d in range(len(DAYS)):

        for p in range(len(PERIODS)):

            for r in THEORY_ROOMS:

                model.Add(

                sum(

                    room_assign[
                        (
                            s.id,
                            (
                                s.year,
                                s.semester,
                                s.section
                            ),
                            d,
                            p,
                            r
                        )
                    ]

                        for s in subjects

                        if s.subject_type == "theory"

                )

                    <= 1
                )



# =================================================
# LAB SAME ROOM CONSTRAINT
# =================================================
    for s in subjects:

        if s.subject_type == "lab":

            g = (
            s.year,
            s.semester,
            s.section
        )

            for d in range(len(DAYS)):

                room_used = []

                for r in LAB_ROOMS:

                    room_var = model.NewBoolVar(
                    f"lab_room_{s.id}_{d}_{r}"
                )

                    room_slots = []

                    for p in range(len(PERIODS)):

                        room_slots.append(

                        room_assign[
                            (
                                s.id,
                                g,
                                d,
                                p,
                                r
                            )
                        ]

                    )

                    model.Add(
                        sum(room_slots) <= 3 * room_var
                    )

                    model.Add(
                        sum(room_slots) >= room_var
                    )

                    room_used.append(
                        room_var
                    )

                model.Add(
                    sum(room_used) <= 1
                )
    # =================================================
    # MAX 7 CLASSES PER DAY
    # =================================================
    for g in groups:

        for d in range(len(DAYS)):

            model.Add(

                sum(

                    slots[(s.id, g, d, p)]

                    for s in subjects

                    for p in range(len(PERIODS))

                    if (
                        s.year,
                        s.semester,
                        s.section
                    ) == g

                )

                <= 7
            )

    # =================================================
    # COMPACTNESS BONUS
    # =================================================
    compact_bonus = []

    for g in groups:

        for d in range(len(DAYS)):

            for p in range(len(PERIODS) - 1):

                pair = model.NewBoolVar(
                    f"pair_{g}_{d}_{p}"
                )

                current_slot = sum(

                    slots[(s.id, g, d, p)]

                    for s in subjects

                    if (
                        s.year,
                        s.semester,
                        s.section
                    ) == g
                )

                next_slot = sum(

                    slots[(s.id, g, d, p + 1)]

                    for s in subjects

                    if (
                        s.year,
                        s.semester,
                        s.section
                    ) == g
                )

                model.Add(
                    current_slot + next_slot >= 2
                ).OnlyEnforceIf(pair)

                model.Add(
                    current_slot + next_slot <= 1
                ).OnlyEnforceIf(
                    pair.Not()
                )

                compact_bonus.append(pair)
    # =================================================
    # NO GAP DAYS
    # =================================================
    day_used = {}

    for g in groups:

        for d in range(len(DAYS)):

            day_used[(g, d)] = model.NewBoolVar(
                f"day_used_{g}_{d}"
            )

            daily_slots = []

            for s in subjects:

                if (
                    s.year,
                    s.semester,
                    s.section
                ) == g:

                    for p in range(len(PERIODS)):

                        daily_slots.append(
                            slots[(s.id, g, d, p)]
                        )

            # If any class exists -> day used
            model.Add(
                sum(daily_slots) >= 1
            ).OnlyEnforceIf(
                day_used[(g, d)]
            )

            # If no class -> not used
            model.Add(
                sum(daily_slots) == 0
            ).OnlyEnforceIf(
                day_used[(g, d)].Not()
            )

    # =========================================
    # CONTINUOUS DAYS
    # =========================================
    for g in groups:

        for d in range(len(DAYS) - 1):

            model.Add(
                day_used[(g, d)] >=
                day_used[(g, d + 1)]
            )

    # =================================================
    # OBJECTIVE
    # =================================================
    model.Maximize(

        sum(slots.values())

        +

        3 * sum(compact_bonus)
    )

    # =================================================
    # SOLVER
    # =================================================
    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = 20

    status = solver.Solve(model)

    print("STATUS =", status)

    if status == cp_model.OPTIMAL:

        print("OPTIMAL SOLUTION FOUND")

    elif status == cp_model.FEASIBLE:

        print("FEASIBLE SOLUTION FOUND")

    elif status == cp_model.INFEASIBLE:

        print("INFEASIBLE")

    else:

        print("UNKNOWN STATUS")

    if status not in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ]:

        return []

    # =================================================
    # BUILD TIMETABLE
    # =================================================
    for s in subjects:

        g = (
            s.year,
            s.semester,
            s.section
        )

        room_list = (

            THEORY_ROOMS

            if s.subject_type == "theory"

            else LAB_ROOMS
        )

        for d in range(len(DAYS)):

            for p in range(len(PERIODS)):

                if solver.Value(
                    slots[(s.id, g, d, p)]
                ):

                    room = None

                    for r in room_list:

                        if solver.Value(

                            room_assign[
                                (
                                    s.id,
                                    g,
                                    d,
                                    p,
                                    r
                                )
                            ]

                        ):

                            room = r
                            break

                    timetable.append(

                        (
                            DAYS[d],
                            PERIODS[p],

                            s.year,
                            s.semester,
                            s.section,

                            s.subject_name,

                            get_teacher(
                                s.subject_name
                            ),

                            s.subject_type,

                            room
                        )

                    )

    print("TOTAL CLASSES:", len(timetable))

    return timetable