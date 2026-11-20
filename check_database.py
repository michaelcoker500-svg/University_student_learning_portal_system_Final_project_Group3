import json
import os
from getpass import getpass
from pathlib import Path

import psycopg


def main():
    settings_file = (
        Path(os.environ["LOCALAPPDATA"])
        / "USLP-Desktop"
        / "connection.json"
    )

    if settings_file.is_file():
        with settings_file.open(encoding="utf-8-sig") as file:
            settings = json.load(file)
    else:
        default_db = "University Student Learning Portal"
        database = input(f"Database name [{default_db}]: ").strip()
        username = input("PostgreSQL username [postgres]: ").strip()

        settings = {
            "host": "localhost",
            "port": 5432,
            "dbname": database or default_db,
            "user": username or "postgres",
            "password": getpass("PostgreSQL password: "),
        }

    with psycopg.connect(**settings, connect_timeout=5) as connection:
        print("Connected to database:", connection.info.dbname)

        result = connection.execute(
            "SELECT COUNT(*) FROM uslp.v_student_directory"
        ).fetchone()

        print("Students in the directory:", result[0])


if __name__ == "__main__":
    main()