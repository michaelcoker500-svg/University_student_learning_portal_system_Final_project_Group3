"""Check the backend runtime login against the configured portal database."""
import sys

import psycopg
from .settings import read_connection
from .roster import roster_size


def main():
    try:
        with psycopg.connect(**read_connection(), connect_timeout=5) as conn:
            imported = roster_size(conn)
            db, count = conn.execute(
                "SELECT current_database(), (SELECT count(*) FROM uslp.v_student_directory)"
            ).fetchone()
    except (ValueError, psycopg.Error) as error:
        print(f"Database check failed: {error}", file=sys.stderr)
        return 1
    print(f"Connected to {db}. Students in the directory: {count}.")
    print(f"BSEM 1101 / Semester 3: {imported} current roster entries (45 at original import).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
