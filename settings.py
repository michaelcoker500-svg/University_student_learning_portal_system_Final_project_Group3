"""Per-workstation connection settings. The portal account is separate from the database login."""

import json
import os
from pathlib import Path

from sqlalchemy import URL, create_engine

DATABASE = "University Student Learning Portal"
DISPLAY_NAME = "group three admininistator"
USERNAME = "group3admin"
ROLE = "Administrator"
CONFIG = Path(os.getenv("LOCALAPPDATA") or Path.home() / ".config") / "USLP-Desktop" / "connection.json"


def read_connection(path=None):
    target = path or CONFIG
    if not target.is_file():
        raise ValueError("Run setup_portal.py on the database workstation first.")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        return {key: data[key] for key in ("host", "port", "dbname", "user", "password")}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ValueError(
            "The local connection settings could not be read. Check the setup guide."
        ) from error


def make_engine(config):
    url = URL.create(
        "postgresql+psycopg",
        username=config["user"],
        password=config["password"],
        host=config["host"],
        port=int(config["port"]),
        database=config["dbname"],
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 5, "application_name": "USLP Desktop"},
    )
