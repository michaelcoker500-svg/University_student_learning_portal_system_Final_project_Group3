"""Fictional, process-local records for working on the GUI without a server."""
from datetime import date
from itertools import count

from .portal_client import Portal, PortalError


class PreviewPortal(Portal):
    preview = True

    def __init__(self):
        super().__init__()
        self.ids = count(10)
        self.versions = count(1)
        self.people = {1: {"id": 1, "number": "PREVIEW-001", "name": "Sample Student", "programme_id": 1,
                           "status": "active", "version": "0"}}
        self.catalogue = {1: {"id": 1, "code": "DEMO101", "title": "Introduction to Computing",
                              "department_id": 1, "credits": 3, "total_lessons": 5, "version": "0"}}
        self.periods = {1: {"id": 1, "name": "Practice term", "year": 1}}
        self.offerings = {1: {"id": 1, "course": 1, "semester": 1}}
        self.registrations = {1: {"id": 1, "student": 1, "offering": 1, "lessons_completed": 1, "status": "enrolled"}}
        self.references = {
            "departments": {1: {"id": 1, "code": "DEMO", "name": "Practice Department"}},
            "programmes": {1: {"id": 1, "name": "Practice Programme"}},
            "years": {1: {"id": 1, "name": "Practice year", "start": "2026-01-01", "end": "2026-12-31"}},
            "lecturers": {1: {"id": 1, "name": "Sample Lecturer"}},
        }
        self.assignments = set()

    def request(self, action, **fields):
        if action == "login":
            return {"token": "preview"}
        if action == "logout":
            return {}
        if action == "snapshot":
            return self.snapshot()
        if not self.token or action not in self.actions:
            raise PortalError("This action is unavailable in the preview.")
        try:
            return self.change(action, fields)
        except (KeyError, ValueError, TypeError):
            raise PortalError("Select an available record and complete all required fields.") from None

    def snapshot(self):
        def term_name(term):
            return f"{term['name']} / {self.references['years'][term['year']]['name']}"

        lookups = {key: [{"id": r["id"], "name": r["name"]} for r in rows.values()]
                   for key, rows in self.references.items()}
        lookups["semesters"] = [{"id": t["id"], "name": term_name(t)} for t in self.periods.values()]
        lookups["offerings"] = []
        for o in self.offerings.values():
            c = self.catalogue[o["course"]]
            term = term_name(self.periods[o["semester"]])
            lookups["offerings"].append({"id": o["id"], "open": True, "name": f"{c['code']} · {c['title']} · {term}"})
        enrollments = []
        for e in self.registrations.values():
            student = self.people[e["student"]]
            offering = self.offerings[e["offering"]]
            course = self.catalogue[offering["course"]]
            enrollments.append({"id": e["id"], "student_number": student["number"], "student": student["name"],
                                "course": course["title"], "course_code": course["code"],
                                "term": term_name(self.periods[offering["semester"]]), "offering_id": offering["id"],
                                "lessons_completed": e["lessons_completed"], "total_lessons": course["total_lessons"],
                                "status": e["status"]})
        return {
            "user": {"name": "Preview user", "username": "preview", "roles": ["Administrator"], "staff": True},
            "actions": ["add_student", "edit_student", "deactivate_student", "delete_student",
                        "add_course", "edit_course", "delete_course", "offer_course", "add_enrollment",
                        "complete_lesson", "withdraw_enrollment", "delete_enrollment", "add_department",
                        "add_year", "add_semester", "assign_lecturer"], "lookups": lookups, "enrollments": enrollments,
            "students": [dict(p, programme=self.references["programmes"][p["programme_id"]]["name"])
                         for p in self.people.values()],
            "courses": [dict(c, department=self.references["departments"][c["department_id"]]["name"])
                        for c in self.catalogue.values()],
        }

    @staticmethod
    def unique(rows, key, value, ignore=None):
        if any(r[key] == value and r["id"] != ignore for r in rows.values()):
            raise PortalError("That identifier already exists.", 409)

    def change(self, action, f):
        if any(value == "" for value in f.values()):
            raise PortalError("Please complete all required fields.")
        record_id = f["id"] if "id" in f else next(self.ids)
        if action in {"add_student", "edit_student"}:
            self.references["programmes"][f["programme"]]
            if action == "add_student":
                self.unique(self.people, "number", f["number"])
                self.people[record_id] = {"id": record_id, "number": f["number"], "status": "active"}
            self.people[record_id].update(name=f["name"], programme_id=f["programme"], version=str(next(self.versions)))
        elif action == "deactivate_student":
            self.people[record_id]["status"] = "inactive"
        elif action == "delete_student":
            if any(e["student"] == record_id for e in self.registrations.values()):
                raise PortalError("This student has enrolments.", 409)
            del self.people[record_id]
        elif action in {"add_course", "edit_course"}:
            code = f["code"].upper()
            self.unique(self.catalogue, "code", code, ignore=record_id)
            self.references["departments"][f["department"]]
            self.catalogue[record_id] = {"id": record_id, "code": code, "title": f["title"], "credits": f["credits"],
                                         "department_id": f["department"], "total_lessons": f["lessons"],
                                         "version": str(next(self.versions))}
        elif action == "delete_course":
            if any(o["course"] == record_id for o in self.offerings.values()):
                raise PortalError("This course already has an offering.", 409)
            del self.catalogue[record_id]
        elif action == "add_enrollment":
            self.offerings[f["offering"]]
            if self.people[f["student"]]["status"] != "active":
                raise PortalError("Select an active student.")
            if any(e["student"] == f["student"] and e["offering"] == f["offering"] for e in self.registrations.values()):
                raise PortalError("This student is already enrolled in that offering.", 409)
            self.registrations[record_id] = dict(f, id=record_id, lessons_completed=0, status="enrolled")
        elif action == "complete_lesson":
            e = self.registrations[record_id]
            maximum = self.catalogue[self.offerings[e["offering"]]["course"]]["total_lessons"]
            if e["status"] != "enrolled" or not maximum or e["lessons_completed"] >= maximum:
                raise PortalError("This enrolment cannot record another lesson.", 409)
            e["lessons_completed"] += 1
            if e["lessons_completed"] == maximum:
                e["status"] = "completed"
            return {"id": record_id, "lessons_completed": e["lessons_completed"], "total_lessons": maximum}
        elif action == "withdraw_enrollment":
            self.registrations[record_id]["status"] = "withdrawn"
        elif action == "delete_enrollment":
            del self.registrations[record_id]
        elif action == "add_department":
            self.unique(self.references["departments"], "code", f["code"].upper())
            self.references["departments"][record_id] = dict(f, code=f["code"].upper(), id=record_id)
        elif action in {"add_year", "add_semester"}:
            if date.fromisoformat(f["end"]) < date.fromisoformat(f["start"]):
                raise PortalError("The end date must be on or after the start date.")
            rows = self.references["years"]
            if action == "add_semester":
                rows[f["year"]]
                rows = self.periods
            rows[record_id] = dict(f, id=record_id)
        elif action == "offer_course":
            self.catalogue[f["course"]]
            self.periods[f["semester"]]
            if any(o["course"] == f["course"] and o["semester"] == f["semester"] for o in self.offerings.values()):
                raise PortalError("This course already has an offering in that term.", 409)
            self.offerings[record_id] = dict(f, id=record_id)
        elif action == "assign_lecturer":
            self.references["lecturers"][f["lecturer"]]
            self.offerings[f["offering"]]
            pair = (f["lecturer"], f["offering"])
            if pair in self.assignments:
                raise PortalError("This lecturer is already assigned.", 409)
            self.assignments.add(pair)
            record_id = f["offering"]
        else:
            raise PortalError("This preview action is unavailable.")
        return {"id": record_id}
