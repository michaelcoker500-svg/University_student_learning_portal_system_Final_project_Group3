"""Run a round-trip test with one new fictional student on the backend PC."""
import argparse
import secrets
import sys
from getpass import getpass
from pathlib import Path

import psycopg

from backend.settings import read_connection
from frontend.portal_client import Portal, PortalError


def check(condition, message):
    if not condition:
        raise RuntimeError(message)
    print("PASS  " + message)


def verify(profile, username, password):
    writer, observer = Portal(profile), Portal(profile)
    number = "G3-SYNC-" + secrets.token_hex(8).upper()
    print(f"Fictional test row: {number}")
    with psycopg.connect(**read_connection(), autocommit=True, connect_timeout=5) as db:
        def stored():
            return db.execute("SELECT student_id, full_name FROM uslp.students WHERE student_number=%s",
                              (number,)).fetchone()

        def visible(client):
            client.refresh()
            return next((r for r in client.students.values() if r.number == number), None)

        def cleanup(record_id):
            # Use both identifiers. Only the row created by this test may be removed.
            row = stored()
            if row and row[0] == record_id:
                writer.request("delete_student", id=record_id)

        record_id = None
        try:
            writer.login(username, password)
            observer.login(username, password)
            required = {"add_student", "edit_student", "delete_student"}
            if not required <= writer.actions or not writer.lookups.get("programmes"):
                raise ValueError("Use a portal account with student CRUD access and one active programme.")
            programme = writer.lookups["programmes"][0]["id"]
            if stored():
                raise RuntimeError("Test identifier collision. Run the test again.")
            record_id = writer.request("add_student", number=number, name="Sync Test Student", programme=programme)["id"]
            check(stored() == (record_id, "Sync Test Student"), "GUI client create reached this PostgreSQL database")
            record = visible(observer)
            check(record is not None and record.name == "Sync Test Student", "Second client saw the same student")
            writer.request("edit_student", id=record_id, name="Sync Test Edited", programme=programme, version=record.version)
            check(stored() == (record_id, "Sync Test Edited"), "GUI client edit reached PostgreSQL")
            with db.transaction():
                db.execute("UPDATE uslp.students SET full_name=%s WHERE student_id=%s AND student_number=%s",
                           ("Sync Test From SQL", record_id, number))
            first, second = visible(writer), visible(observer)
            check(first is not None and second is not None and first.name == second.name == "Sync Test From SQL",
                  "Both clients saw the committed SQL edit")
            observer.request("delete_student", id=record_id)
            check(stored() is None and visible(writer) is None and visible(observer) is None,
                  "Delete removed the student from PostgreSQL and both clients")
        finally:
            try:
                if record_id is not None:
                    cleanup(record_id)
            finally:
                writer.logout()
                observer.logout()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="the connection file for this backend")
    args = parser.parse_args()
    try:
        verify(args.profile, input("Portal username: ").strip(), getpass("Portal password: "))
    except (OSError, ValueError, RuntimeError, PortalError, psycopg.Error) as error:
        print(f"Test did not finish: {error}\nAfter reconnecting, search for the printed test ID before retrying.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
