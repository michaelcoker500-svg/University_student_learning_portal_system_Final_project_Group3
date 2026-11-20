"""Qt-facing models and client. Only the trusted service opens database connections."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPException


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
        return cls(**row)

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

    def cells(self):
        return [self.number, self.name, self.programme, self.status.title()]


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


class Portal:
    def __init__(self, port):
        self.port = port
        self.token = None
        self.clear()

    def clear(self):
        self.token = None
        self.user = {}
        self.actions = set()
        self.students, self.courses, self.enrollments, self.lookups = {}, {}, {}, {}

    def request(self, action, **fields):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=12)
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            conn.request("POST", "/" + action, body=json.dumps(fields).encode(), headers=headers)
            response = conn.getresponse()
            data = json.loads(response.read())
        except (OSError, HTTPException, ValueError):
            raise PortalError(
                "The portal service is unavailable. Check the connection and refresh.", 503
            ) from None
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

    def refresh(self):
        data = self.request("snapshot")
        self.user = data["user"]
        self.actions = set(data["actions"])
        for key, model in (("students", Student), ("courses", Course), ("enrollments", Enrollment)):
            setattr(self, key, {row["id"]: model.from_row(row) for row in data[key]})
        self.lookups = data["lookups"]

    def logout(self):
        try:
            if self.token:
                self.request("logout")
        except PortalError:
            pass
        finally:
            self.clear()
