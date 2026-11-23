"""Qt-facing models and client. Only the trusted service opens database connections."""

import argparse
import ipaddress
import json
import os
import ssl
import sys
import tempfile
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields as dataclass_fields
from http.client import HTTPSConnection, HTTPException


class PortalError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class Record(ABC):
    @abstractmethod
    def cells(self):
        """Return the text values for this record's table row."""

    @classmethod
    def from_row(cls, row):
        return cls(**{field.name: row[field.name] for field in dataclass_fields(cls)})

    @staticmethod
    def cell(value):
        return "—" if value is None else str(value)


@dataclass
class Student(Record):
    id: int
    number: str
    name: str
    programme_id: int
    programme: str
    status: str
    version: str

    gender: str | None = None

    @classmethod
    def from_row(cls, row):
        return super().from_row({"gender": None, **row})

    def cells(self):
        return [self.number, self.name, self.cell(self.gender), self.programme, self.status.title()]


@dataclass
class Course(Record):
    id: int
    code: str
    title: str
    credits: int
    total_lessons: int | None
    department_id: int
    department: str
    version: str

    def cells(self):
        return [self.code, self.title, self.department, str(self.credits), self.cell(self.total_lessons)]


@dataclass
class Enrollment(Record):
    id: int
    student_number: str
    student: str
    course: str
    course_code: str
    term: str
    lessons_completed: int
    total_lessons: int | None
    status: str
    offering_id: int

    @property
    def progress(self):
        return None if not self.total_lessons else round(100 * self.lessons_completed / self.total_lessons)

    def cells(self):
        return [
            str(self.id),
            self.student,
            f"{self.course_code} · {self.course}",
            self.term,
            f"{self.lessons_completed}/{self.cell(self.total_lessons)}",
            "—" if self.progress is None else f"{self.progress}%",
            self.status.title(),
        ]


DEFAULT_PROFILE = Path(__file__).resolve().parent.parent / "portal-team.json"
SAVED_PROFILE = Path(os.getenv("LOCALAPPDATA") or Path.home() / ".config") / "USLP-Client" / "portal-team.json"


@dataclass(frozen=True)
class Endpoint:
    host: str
    port: int
    context: ssl.SSLContext


def read_profile(path):
    try:
        content = Path(path).read_text(encoding="utf-8-sig")
        data = json.loads(content)
        if data["format"] != 1 or type(data["port"]) is not int or not 1 <= data["port"] <= 65535:
            raise ValueError
        host = str(ipaddress.IPv4Address(data["host"]))
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_verify_locations(cadata=data["ca_pem"])
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise PortalError(f"Cannot read the team connection file at {path}. Choose the file from your backend developer.") from error
    return Endpoint(host, data["port"], context), content


class Portal:
    preview = False

    def __init__(self, profile=None):
        self.endpoint = None
        self.clear()
        if profile is not None:
            self.configure(profile)

    def configure(self, path, remember=False):
        endpoint, content = read_profile(path)
        if remember:
            try:
                SAVED_PROFILE.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=SAVED_PROFILE.parent,
                                                 delete=False) as f:
                    temp = Path(f.name)
                    f.write(content)
                try:
                    os.replace(temp, SAVED_PROFILE)
                finally:
                    temp.unlink(missing_ok=True)
            except OSError as error:
                raise PortalError("Cannot save the selected team connection under your user profile.") from error
        self.clear()
        self.endpoint = endpoint

    def clear(self):
        self.token = None
        self.user = {}
        self.actions = set()
        self.students, self.courses, self.enrollments, self.lookups = {}, {}, {}, {}

    def request(self, action, **fields):
        endpoint = self.endpoint
        if endpoint is None:
            raise PortalError("Choose the portal-team.json file supplied by your backend developer.")
        conn = HTTPSConnection(endpoint.host, endpoint.port, context=endpoint.context, timeout=7)
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            if action == "health":
                conn.request("GET", "/health")
            else:
                conn.request("POST", "/" + action, body=json.dumps(fields).encode(), headers=headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if not isinstance(data, dict):
                raise ValueError
        except ssl.SSLCertVerificationError:
            raise PortalError("The server identity could not be verified. Check the team profile and both computers' clocks.", 503) from None
        except (OSError, HTTPException, ValueError):
            message = f"Cannot confirm a reply from {endpoint.host}:{endpoint.port}. Check the host and team network."
            if action not in {"health", "login", "logout", "snapshot"}:
                message += " Refresh and check the record before repeating the change."
            raise PortalError(message, 503) from None
        finally:
            conn.close()
        if response.status != 200:
            raise PortalError(data.get("error", "The request failed."), response.status)
        return data

    def login(self, username, password):
        self.clear()
        self.token = self.request("login", username=username, password=password)["token"]
        try:
            self.refresh()
        except PortalError:
            self.logout()
            raise

    def apply_snapshot(self, data):
        try:
            user, actions, lookups = data["user"], set(data["actions"]), data["lookups"]
            collections = {}
            for key, model in (("students", Student), ("courses", Course), ("enrollments", Enrollment)):
                collections[key] = {row["id"]: model.from_row(row) for row in data[key]}
        except (TypeError, KeyError) as error:
            raise PortalError("This GUI and backend use different record formats. Check out compatible versions.", 502) from error
        changed = self.user != user or self.actions != actions or self.lookups != lookups
        for key, records in collections.items():
            changed = changed or records != getattr(self, key)
            setattr(self, key, records)
        self.user, self.actions, self.lookups = user, actions, lookups
        return changed

    def refresh(self):
        return self.apply_snapshot(self.request("snapshot"))

    def logout(self):
        try:
            if self.token:
                self.request("logout")
        except PortalError:
            pass
        finally:
            self.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check the API and PostgreSQL using a team connection file.")
    parser.add_argument("profile", type=Path, nargs="?", default=None)
    args = parser.parse_args()
    try:
        path = args.profile or (SAVED_PROFILE if SAVED_PROFILE.is_file() else DEFAULT_PROFILE)
        client = Portal(path)
        result = client.request("health")
        print(f"API {client.endpoint.host}:{client.endpoint.port}  |  Status: {result['status']}  |  API version: {result['api_version']}")
    except (PortalError, KeyError) as error:
        sys.exit(str(error))
