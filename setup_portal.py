"""Install stage 3/4 on the existing PostgreSQL database and provision a portal login."""

import argparse
import json
import os
import secrets
import sys
from getpass import getpass
from pathlib import Path

import psycopg
from argon2 import PasswordHasher
from psycopg import sql
from settings import CONFIG, DATABASE, DISPLAY_NAME, ROLE, USERNAME, read_connection

MIGRATION = Path(__file__).with_name("07_desktop_integration.sql")
ROLES = ("Administrator", "Registrar", "Lecturer", "Student", "Super Administrator")


def grant_runtime(conn, config, create):
    identity = sql.Identifier(config["user"])
    if create:
        verifier = conn.pgconn.encrypt_password(
            config["password"].encode(), config["user"].encode(), b"scram-sha-256"
        ).decode()
        conn.execute(
            sql.SQL(
                "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE "
                "NOREPLICATION NOBYPASSRLS PASSWORD {}"
            ).format(identity, sql.Literal(verifier))
        )
    statements = (
        "GRANT USAGE ON SCHEMA uslp TO {}",
        (
            "GRANT SELECT ON uslp.users, uslp.roles, uslp.permissions, uslp.user_roles, "
            "uslp.role_permissions, uslp.students, uslp.programmes, uslp.departments, "
            "uslp.courses, uslp.enrollments, uslp.semesters, uslp.academic_sessions, uslp.lecturers, "
            "uslp.course_offerings, uslp.teaching_assignments, uslp.class_sessions, uslp.attendance, "
            "uslp.v_user_permissions, uslp.v_student_directory TO {}"
        ),
        "GRANT UPDATE (failed_login_attempts, locked_until, last_login_at) ON uslp.users TO {}",
        "GRANT INSERT, UPDATE, DELETE ON uslp.students, uslp.courses, uslp.enrollments TO {}",
        (
            "GRANT INSERT ON uslp.departments, uslp.academic_sessions, uslp.semesters, "
            "uslp.course_offerings, uslp.teaching_assignments, uslp.audit_logs TO {}"
        ),
        # PostgreSQL's SELECT ... FOR SHARE in the starter's triggers needs an update privilege.
        "GRANT UPDATE (starts_on) ON uslp.academic_sessions TO {}",
        "GRANT UPDATE (starts_on) ON uslp.semesters TO {}",
        "GRANT UPDATE (enrollment_open) ON uslp.course_offerings TO {}",
        "GRANT USAGE ON ALL SEQUENCES IN SCHEMA uslp TO {}",
        "GRANT EXECUTE ON FUNCTION uslp.enroll_student(bigint,bigint) TO {}",
    )
    for statement in statements:
        conn.execute(sql.SQL(statement).format(identity))
    conn.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(config["dbname"]), identity)
    )


def add_account(conn, username, display_name, role, password, profile_number=None):
    username = username.strip().lower()
    display_name = display_name.strip()
    if not (1 <= len(username) <= 80 and 1 <= len(display_name) <= 160):
        raise ValueError("Enter a username up to 80 characters and a display name up to 160 characters.")
    if role not in ROLES:
        raise ValueError("Choose one of the listed roles.")
    if not password or not 12 <= len(password) <= 256:
        raise ValueError("Choose a portal password between 12 and 256 characters.")
    role_row = conn.execute("SELECT role_id FROM uslp.roles WHERE role_name = %s", (role,)).fetchone()
    if not role_row:
        raise ValueError("The role definitions from the existing backend must be installed first.")
    uid = conn.execute(
        "INSERT INTO uslp.users(username,display_name,password_hash,is_active) "
        "VALUES (%s,%s,%s,true) RETURNING user_id",
        (username, display_name, PasswordHasher().hash(password)),
    ).fetchone()[0]
    conn.execute("INSERT INTO uslp.user_roles(user_id,role_id) VALUES (%s,%s)", (uid, role_row[0]))
    if role in ("Student", "Lecturer"):
        table, key = ("students", "student_number") if role == "Student" else ("lecturers", "staff_number")
        link = sql.SQL("UPDATE uslp.{} SET user_id=%s WHERE {}=%s AND user_id IS NULL").format(
            sql.Identifier(table), sql.Identifier(key)
        )
        if conn.execute(link, (uid, profile_number)).rowcount != 1:
            raise ValueError(
                "That profile is missing or already linked. Check its official ID. "
                "The account creation was cancelled."
            )
    return uid


def configure(owner, username, display, role, password, profile=None, path=None):
    path = path or CONFIG
    new_settings = not path.exists()
    if new_settings:
        runtime = dict(
            owner, user="uslp_desktop_" + secrets.token_hex(8), password=secrets.token_urlsafe(36)
        )
    else:
        runtime = read_connection(path)
        if any(str(runtime[key]) != str(owner[key]) for key in ("host", "port", "dbname")):
            raise ValueError(
                "This workstation is configured for another database. Use its original connection settings."
            )
        with psycopg.connect(**runtime, connect_timeout=5) as existing:
            existing.execute("SELECT 1")
    saved = False
    try:
        with psycopg.connect(**owner, connect_timeout=5) as conn:
            conn.execute("SELECT pg_advisory_xact_lock(hashtext('uslp_desktop_setup'))")
            current = conn.execute(
                "SELECT current_database(), to_regclass('uslp.v_class_list'), "
                "to_regprocedure('uslp.enroll_student(bigint,bigint)')"
            ).fetchone()
            if any(value is None for value in current[1:]):
                raise ValueError("Choose the database containing the 20-table USLP backend and its views.")
            installed = conn.execute("""
                SELECT count(*) = 3 FROM information_schema.columns
                WHERE table_schema='uslp' AND (table_name,column_name) IN
                  (('users','display_name'),('courses','total_lessons'),('enrollments','lessons_completed'))
            """).fetchone()[0]
            if not installed:
                conn.execute(MIGRATION.read_text(encoding="utf-8"))
            grant_runtime(conn, runtime, new_settings)
            match = conn.execute(
                "SELECT display_name, is_active, ARRAY(SELECT r.role_name "
                "FROM uslp.user_roles ur JOIN uslp.roles r USING(role_id) "
                "WHERE ur.user_id=u.user_id ORDER BY r.role_name) "
                "FROM uslp.users u WHERE username=%s",
                (username.strip().lower(),),
            ).fetchone()
            if match:
                if not (
                    username == USERNAME
                    and display == DISPLAY_NAME
                    and role == ROLE
                    and match[0] == display
                    and match[1]
                    and list(match[2]) == [role]
                ):
                    raise ValueError(
                        "That username is already in use. Choose another. Existing credentials were preserved."
                    )
                created = False
            else:
                add_account(conn, username, display, role, password, profile)
                created = True
            if new_settings:
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                # Exclusive creation prevents taking over another setup running on this workstation.
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                saved = True
                with os.fdopen(fd, "w", encoding="utf-8") as out:
                    json.dump(runtime, out)
    except Exception:
        if saved:
            path.unlink(missing_ok=True)
        raise
    with psycopg.connect(**runtime, connect_timeout=5) as check:
        db, count = check.execute(
            "SELECT current_database(), (SELECT count(*) FROM uslp.students)"
        ).fetchone()
    return created, db, count


def prompt(label, default=None):
    answer = input(f"{label} [{default}]: " if default is not None else f"{label}: ").strip()
    return answer or default or ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--add-account",
        action="store_true",
        help="create a second staff or linked student/lecturer account",
    )
    opts = parser.parse_args()
    previous = read_connection() if CONFIG.exists() else {}
    print("Connect to the existing USLP database with its owner (usually postgres).")
    owner = {
        "host": prompt("PostgreSQL host", previous.get("host", "localhost")),
        "port": int(prompt("Port", previous.get("port", 5432))),
        "dbname": prompt("Database name", previous.get("dbname", DATABASE)),
        "user": prompt("Database owner", "postgres"),
        "password": getpass("Database owner password: "),
    }
    username, display, role, profile = USERNAME, DISPLAY_NAME, ROLE, None
    if opts.add_account:
        username = prompt("Portal username").lower()
        display = prompt("Display name")
        for index, value in enumerate(ROLES, 1):
            print(f"{index}. {value}")
        choice = int(prompt("Role number"))
        if not 1 <= choice <= len(ROLES):
            raise ValueError("Choose a listed role number.")
        role = ROLES[choice - 1]
        if role in ("Student", "Lecturer"):
            profile = prompt(
                "Existing student number" if role == "Student" else "Existing lecturer staff number"
            )
    print(f"Portal account: {username} | {display} | {role}")
    secret = getpass("New portal password (12–256 characters; Enter to reuse an existing group account): ")
    if secret and secret != getpass("Confirm portal password: "):
        raise ValueError("The two portal passwords differ. Run setup again.")
    created, database, count = configure(owner, username, display, role, secret, profile)
    print(f"Connected to {database}. Students stored: {count}.")
    print(
        "Portal account created."
        if created
        else "Group account already exists; its existing password still applies."
    )
    print(f"Start portal.py and sign in as {username}.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, psycopg.Error, KeyboardInterrupt) as exc:
        if isinstance(exc, psycopg.Error):
            msg = (
                str(exc.diag.message_primary)
                if exc.diag.message_primary
                else "Check the PostgreSQL service, host, owner login and privileges."
            )
        else:
            msg = str(exc) or "Setup cancelled."
        sys.exit(f"Setup did not finish. {msg}")
