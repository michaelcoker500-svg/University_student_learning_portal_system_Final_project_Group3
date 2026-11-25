"""Database operations for the trusted portal service. All data values are bound parameters."""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import text


class PortalError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def rows(conn, statement, **params):
    return [dict(r) for r in conn.execute(text(statement), params).mappings()]


def one(conn, statement, **params):
    result = conn.execute(text(statement), params).mappings().first()
    if result is None:
        raise PortalError("This record is unavailable or has changed. Refresh the page.", 409)
    return dict(result)


def label(value, maximum):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        raise PortalError(f"Enter a value between 1 and {maximum} characters.")
    return value.strip()


def positive(value, maximum=2**63 - 1):
    if type(value) is not int or not 1 <= value <= maximum:
        raise PortalError("Enter a positive whole number within the allowed range.")
    return value


def dates(start, end):
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except (TypeError, ValueError):
        raise PortalError("Enter valid dates in YYYY-MM-DD format.") from None
    if last < first:
        raise PortalError("The end date must be on or after the start date.")
    return first, last


STAFF = {"Administrator", "Registrar", "Super Administrator"}


@dataclass
class Access:
    user_id: int
    username: str
    name: str
    roles: set
    permissions: set

    @property
    def staff(self):
        return bool(self.roles & STAFF)

    @classmethod
    def load(cls, conn, uid):
        user = (
            conn.execute(
                text("""
            SELECT u.username, coalesce(u.display_name, s.full_name,
                       nullif(concat_ws(' ',l.first_name,l.last_name),''), u.username) AS name
            FROM uslp.users u
            LEFT JOIN uslp.student_accounts a ON a.user_id=u.user_id
            LEFT JOIN uslp_portal.students s ON s.student_id=a.student_id
            LEFT JOIN uslp.lecturers l ON l.user_id=u.user_id
            WHERE u.user_id=:uid AND u.is_active AND
                  (u.locked_until IS NULL OR u.locked_until <= now()) FOR SHARE OF u
        """),
                {"uid": uid},
            )
            .mappings()
            .first()
        )
        if user is None:
            raise PortalError("Your session has ended. Please sign in again.", 401)
        roles = set(
            conn.execute(
                text(
                    "SELECT r.role_name FROM uslp.user_roles ur JOIN uslp.roles r "
                    "USING(role_id) WHERE ur.user_id=:uid"
                ),
                {"uid": uid},
            ).scalars()
        )
        perms = set(
            conn.execute(
                text("SELECT permission_code FROM uslp.v_user_permissions WHERE user_id=:uid"), {"uid": uid}
            ).scalars()
        )
        if not roles & (STAFF | {"Student", "Lecturer"}):
            raise PortalError("This account has no active portal role.", 403)
        return cls(uid, user["username"], user["name"], roles, perms)

    def scope(self):
        return {
            "uid": self.user_id,
            "staff": self.staff,
            "lecturer": "Lecturer" in self.roles,
            "student": "Student" in self.roles,
        }

    def read_scope(self, resource):
        general = resource + ".view" in self.permissions
        personal = resource + ".view_own" in self.permissions
        return {
            "uid": self.user_id,
            "staff": general and self.staff,
            "lecturer": general and "Lecturer" in self.roles,
            "student": (personal or general) and "Student" in self.roles,
        }

    def allows(self, operation):
        permission, _ = ACTIONS[operation]
        return permission in self.permissions and (
            self.staff or (operation == "complete_lesson" and "Lecturer" in self.roles)
        )


# Only these fixed predicates are interpolated into queries. User input is never SQL.
ASSIGNED = """EXISTS (SELECT 1 FROM uslp.teaching_assignments ta JOIN uslp.lecturers l
    USING(lecturer_id) WHERE ta.offering_id=o.offering_id AND l.user_id=:uid AND l.is_active)"""
OWN_STUDENT = """EXISTS (SELECT 1 FROM uslp.student_accounts a
    WHERE a.student_id=s.student_id AND a.user_id=:uid)"""
STUDENT_SCOPE = f"""(:staff OR (:student AND {OWN_STUDENT}) OR (:lecturer AND EXISTS (
    SELECT 1 FROM uslp.enrollments e JOIN uslp.course_offerings o USING(offering_id)
    WHERE e.student_id=s.student_id AND {ASSIGNED})))"""
COURSE_SCOPE = f"""(:staff OR EXISTS (SELECT 1 FROM uslp.course_offerings o
    WHERE o.course_id=c.course_id AND ((:lecturer AND {ASSIGNED}) OR (:student AND EXISTS (
       SELECT 1 FROM uslp.enrollments e JOIN uslp.student_accounts a USING(student_id)
       WHERE e.offering_id=o.offering_id AND a.user_id=:uid)))))"""
ENROLLMENT_SCOPE = f"""(:staff OR (:student AND {OWN_STUDENT}) OR (:lecturer AND {ASSIGNED}))"""


def snapshot(conn, who):
    students, courses, enrollments = [], [], []
    if who.permissions & {"students.view", "students.view_own"}:
        students = rows(
            conn,
            f"""
            SELECT s.student_id AS id,s.student_number AS number,d.full_name AS name,d.gender,
                   s.programme_id,d.programme_name AS programme,s.status,s.updated_at::text AS version
            FROM uslp_portal.students s JOIN uslp.v_student_directory d USING(student_id)
            WHERE {STUDENT_SCOPE} ORDER BY s.student_number
        """,
            **who.read_scope("students"),
        )
    if who.permissions & {"courses.view", "courses.view_own"}:
        courses = rows(
            conn,
            f"""
            SELECT c.course_id AS id,c.course_code AS code,c.course_title AS title,c.credits,
                   c.total_lessons,c.department_id,d.department_name AS department,c.updated_at::text AS version
            FROM uslp.courses c JOIN uslp.departments d USING(department_id)
            WHERE {COURSE_SCOPE} ORDER BY c.course_code
        """,
            **who.read_scope("courses"),
        )
    if who.permissions & {"enrollments.view", "enrollments.view_own"}:
        enrollments = rows(
            conn,
            f"""
            SELECT e.enrollment_id AS id,s.student_number,d.full_name AS student,c.course_title AS course,
                   c.course_code, concat(t.semester_name,' / ',y.session_name) AS term,
                   e.lessons_completed,c.total_lessons,e.status,e.offering_id
            FROM uslp.enrollments e JOIN uslp_portal.students s USING(student_id)
            JOIN uslp.v_student_directory d USING(student_id) JOIN uslp.course_offerings o USING(offering_id)
            JOIN uslp.courses c USING(course_id) JOIN uslp.semesters t USING(semester_id)
            JOIN uslp.academic_sessions y USING(academic_session_id)
            WHERE {ENROLLMENT_SCOPE} ORDER BY e.enrollment_id
        """,
            **who.read_scope("enrollments"),
        )
    lookups = {}
    if who.staff:
        if who.permissions & {"students.create", "students.update"}:
            lookups["programmes"] = rows(
                conn,
                "SELECT programme_id AS id,programme_name AS name "
                "FROM uslp.programmes WHERE is_active ORDER BY name",
            )
        if "courses.manage" in who.permissions:
            lookups["departments"] = rows(
                conn,
                "SELECT department_id AS id,department_name AS name "
                "FROM uslp.departments WHERE is_active ORDER BY name",
            )
            lookups["semesters"] = rows(
                conn,
                "SELECT semester_id AS id,concat(semester_name,' / ',"
                "session_name) AS name FROM uslp.semesters JOIN uslp.academic_sessions "
                "USING(academic_session_id) ORDER BY semesters.starts_on DESC",
            )
            lookups["lecturers"] = rows(
                conn,
                "SELECT lecturer_id AS id,concat(first_name,' ',last_name,"
                "' (',staff_number,')') AS name FROM uslp.lecturers WHERE is_active ORDER BY name",
            )
        if "academics.manage" in who.permissions:
            lookups["years"] = rows(
                conn,
                "SELECT academic_session_id AS id,session_name AS name "
                "FROM uslp.academic_sessions ORDER BY starts_on DESC",
            )
        if who.permissions & {"enrollments.create", "courses.manage"}:
            lookups["offerings"] = rows(
                conn,
                """
                SELECT o.offering_id AS id,o.enrollment_open AS open,concat(c.course_code,' · ',c.course_title,
                       ' · ',s.semester_name,' / ',a.session_name) AS name FROM uslp.course_offerings o
                JOIN uslp.courses c USING(course_id) JOIN uslp.semesters s USING(semester_id)
                JOIN uslp.academic_sessions a USING(academic_session_id) ORDER BY a.starts_on DESC,s.starts_on DESC,c.course_code
            """,
            )
    actions = [name for name in ACTIONS if who.allows(name)]
    return {
        "user": {
            "username": who.username,
            "name": who.name,
            "roles": sorted(who.roles),
            "staff": who.staff,
        },
        "actions": actions,
        "students": students,
        "courses": courses,
        "enrollments": enrollments,
        "lookups": lookups,
    }


def audit_log(conn, who, limit=50, offset=0):
    """Return a page of committed database audit events to staff accounts."""
    if not who.staff:
        raise PortalError("Your account does not have permission to view the audit log.", 403)
    if type(limit) is not int or not 1 <= limit <= 200:
        raise PortalError("Audit page size must be between 1 and 200.")
    if type(offset) is not int or offset < 0:
        raise PortalError("Audit page offset must be zero or greater.")

    total = conn.execute(text("SELECT count(*) FROM uslp.audit_logs")).scalar_one()
    entries = rows(
        conn,
        """
        SELECT a.audit_id AS id, a.occurred_at::text AS occurred_at,
               a.actor_user_id, coalesce(u.username, '') AS actor_username,
               coalesce(u.display_name, u.username, a.database_user) AS actor_name,
               a.database_user, a.table_name, a.record_key, a.operation,
               a.old_data, a.new_data
        FROM uslp.audit_logs a
        LEFT JOIN uslp.users u ON u.user_id=a.actor_user_id
        ORDER BY a.occurred_at DESC, a.audit_id DESC
        LIMIT :limit OFFSET :offset
        """,
        limit=limit,
        offset=offset,
    )
    return {"entries": entries, "total": total, "limit": limit, "offset": offset}


def add_student(conn, who, number, name, programme):
    return one(
        conn,
        """INSERT INTO uslp_portal.students(student_number,full_name,programme_id)
        VALUES (:number,:name,:programme) RETURNING student_id AS id""",
        number=label(number, 40),
        name=label(name, 240),
        programme=positive(programme),
    )


def edit_student(conn, who, id, name, programme, version):
    return one(
        conn,
        """UPDATE uslp_portal.students SET full_name=:name,programme_id=:programme
        WHERE student_id=:id AND updated_at::text=:version RETURNING student_id AS id""",
        id=positive(id),
        name=label(name, 240),
        programme=positive(programme),
        version=label(version, 80),
    )


def deactivate_student(conn, who, id):
    return one(
        conn,
        "UPDATE uslp_portal.students SET status='inactive' WHERE student_id=:id "
        "AND status='active' RETURNING student_id AS id",
        id=positive(id),
    )


def delete_student(conn, who, id):
    id = positive(id)
    # Lock the student first so a concurrent foreign-key insert cannot slip through.
    one(conn, "SELECT student_id FROM uslp_portal.students WHERE student_id=:id FOR UPDATE", id=id)
    linked = conn.scalar(text("""
        SELECT EXISTS (SELECT 1 FROM uslp.student_accounts WHERE student_id=:id)
            OR EXISTS (SELECT 1 FROM uslp.enrollments WHERE student_id=:id)
    """), {"id": id})
    if linked:
        raise PortalError("This student has a linked portal account or enrolment history. "
                          "Use Deactivate to keep those records.", 409)
    # Both operations and their audit entries commit or roll back together.
    conn.execute(text("DELETE FROM uslp.class_list_entries WHERE student_id=:id"), {"id": id})
    return one(conn, "DELETE FROM uslp_portal.students WHERE student_id=:id RETURNING student_id AS id", id=id)


def course_values(code, title, department, credits, lessons):
    return {
        "code": label(code, 20).upper(),
        "title": label(title, 180),
        "department": positive(department),
        "credits": positive(credits, 32767),
        "lessons": positive(lessons, 10000) if lessons is not None else None,
    }


def add_course(conn, who, code, title, department, credits, lessons):
    return one(
        conn,
        """INSERT INTO uslp.courses(course_code,course_title,department_id,credits,total_lessons)
        VALUES (:code,:title,:department,:credits,:lessons) RETURNING course_id AS id""",
        **course_values(code, title, department, credits, lessons),
    )


def edit_course(conn, who, id, code, title, department, credits, lessons, version):
    values = course_values(code, title, department, credits, lessons)
    id = positive(id)
    old = one(
        conn,
        "SELECT total_lessons FROM uslp.courses WHERE course_id=:id AND updated_at::text=:version "
        "FOR UPDATE",
        id=id,
        version=label(version, 80),
    )
    if old["total_lessons"] is not None and old["total_lessons"] != values["lessons"]:
        has_enrollments = conn.scalar(
            text(
                "SELECT EXISTS(SELECT 1 FROM uslp.enrollments JOIN "
                "uslp.course_offerings USING(offering_id) WHERE course_id=:id)"
            ),
            {"id": id},
        )
        if has_enrollments:
            raise PortalError(
                "This course already has enrolments. Its recorded lesson total is fixed.", 409
            )
    return one(
        conn,
        """UPDATE uslp.courses SET course_code=:code,course_title=:title,department_id=:department,
        credits=:credits,total_lessons=:lessons WHERE course_id=:id RETURNING course_id AS id""",
        id=id,
        **values,
    )


def delete_course(conn, who, id):
    return one(
        conn, "DELETE FROM uslp.courses WHERE course_id=:id RETURNING course_id AS id", id=positive(id)
    )


def add_enrollment(conn, who, student, offering):
    one(
        conn,
        "SELECT c.course_id FROM uslp.course_offerings o JOIN uslp.courses c USING(course_id) "
        "WHERE o.offering_id=:id AND c.is_active FOR SHARE OF c",
        id=positive(offering),
    )
    return one(
        conn,
        "SELECT uslp.enroll_student(:student,:offering) AS id",
        student=positive(student),
        offering=offering,
    )


def complete_lesson(conn, who, id, expected):
    if type(expected) is not int or expected < 0:
        raise PortalError("Refresh to get the current lesson count.")
    # An instructor can update only the specific offering they teach, even if another
    # instructor teaches a second offering of the same course.
    result = (
        conn.execute(
            text(f"""
        UPDATE uslp.enrollments e SET lessons_completed=e.lessons_completed+1,
               status=CASE WHEN e.lessons_completed+1=c.total_lessons THEN 'completed' ELSE 'enrolled' END
        FROM uslp.course_offerings o JOIN uslp.courses c USING(course_id)
        WHERE e.offering_id=o.offering_id AND e.enrollment_id=:id AND e.status='enrolled'
          AND e.lessons_completed=:expected AND e.lessons_completed<c.total_lessons AND (:staff OR (:lecturer AND {ASSIGNED}))
        RETURNING e.enrollment_id AS id,e.lessons_completed,c.total_lessons,e.status
    """),
            dict(id=positive(id), expected=expected, **who.scope()),
        )
        .mappings()
        .first()
    )
    if not result:
        raise PortalError(
            "No lesson was recorded. Refresh to check the latest progress, assignment, status and lesson total.",
            409,
        )
    return dict(result)


def withdraw_enrollment(conn, who, id):
    return one(
        conn,
        "UPDATE uslp.enrollments SET status='withdrawn' WHERE enrollment_id=:id "
        "AND status='enrolled' RETURNING enrollment_id AS id",
        id=positive(id),
    )


def delete_enrollment(conn, who, id):
    return one(
        conn,
        "DELETE FROM uslp.enrollments WHERE enrollment_id=:id RETURNING enrollment_id AS id",
        id=positive(id),
    )


def add_department(conn, who, code, name):
    return one(
        conn,
        "INSERT INTO uslp.departments(department_code,department_name) VALUES (:code,:name) "
        "RETURNING department_id AS id",
        code=label(code, 20).upper(),
        name=label(name, 150),
    )


def add_year(conn, who, name, start, end):
    first, last = dates(start, end)
    return one(
        conn,
        "INSERT INTO uslp.academic_sessions(session_name,starts_on,ends_on) VALUES (:name,:first,:last) "
        "RETURNING academic_session_id AS id",
        name=label(name, 60),
        first=first,
        last=last,
    )


def add_semester(conn, who, name, year, start, end):
    first, last = dates(start, end)
    return one(
        conn,
        "INSERT INTO uslp.semesters(academic_session_id,semester_name,starts_on,ends_on) "
        "VALUES (:year,:name,:first,:last) RETURNING semester_id AS id",
        year=positive(year),
        name=label(name, 60),
        first=first,
        last=last,
    )


def offer_course(conn, who, course, semester):
    return one(
        conn,
        "INSERT INTO uslp.course_offerings(course_id,semester_id) VALUES (:course,:semester) "
        "RETURNING offering_id AS id",
        course=positive(course),
        semester=positive(semester),
    )


def assign_lecturer(conn, who, lecturer, offering):
    return one(
        conn,
        "INSERT INTO uslp.teaching_assignments(lecturer_id,offering_id) VALUES (:lecturer,:offering) "
        "RETURNING offering_id AS id",
        lecturer=positive(lecturer),
        offering=positive(offering),
    )


ACTIONS = {
    "add_student": ("students.create", add_student),
    "edit_student": ("students.update", edit_student),
    "deactivate_student": ("students.deactivate", deactivate_student),
    "delete_student": ("students.delete", delete_student),
    "add_course": ("courses.manage", add_course),
    "edit_course": ("courses.manage", edit_course),
    "delete_course": ("courses.manage", delete_course),
    "offer_course": ("courses.manage", offer_course),
    "assign_lecturer": ("courses.manage", assign_lecturer),
    "add_department": ("academics.manage", add_department),
    "add_year": ("academics.manage", add_year),
    "add_semester": ("academics.manage", add_semester),
    "add_enrollment": ("enrollments.create", add_enrollment),
    "complete_lesson": ("lessons.record", complete_lesson),
    "withdraw_enrollment": ("enrollments.update", withdraw_enrollment),
    "delete_enrollment": ("enrollments.delete", delete_enrollment),
}
