"""Trusted local service. A Qt client sends only its portal credentials and an opaque session token."""

import inspect
import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from portal_data import ACTIONS, Access, PortalError, snapshot
from settings import make_engine, read_connection
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

DENIED = "Sign-in failed. Check your username and password, or contact the account administrator."
TTL = 8 * 60 * 60


class PortalService:
    def __init__(self, engine):
        self.engine = engine
        self.hasher = PasswordHasher()
        self.dummy_hash = self.hasher.hash(secrets.token_urlsafe(32))
        self.sessions = {}
        self.lock = Lock()

    def login(self, username, password):
        if (
            not isinstance(username, str)
            or not isinstance(password, str)
            or not (0 < len(username) <= 80 and 0 < len(password) <= 256)
        ):
            raise PortalError(DENIED, 401)
        user_id = None
        with self.engine.begin() as conn:
            row = (
                conn.execute(
                    text("""
                SELECT user_id,password_hash,is_active,locked_until,failed_login_attempts,
                       coalesce(locked_until > now(), false) AS locked
                FROM uslp.users WHERE username=:username FOR UPDATE
            """),
                    {"username": username.strip().lower()},
                )
                .mappings()
                .first()
            )
            stored = row["password_hash"] if row and row["password_hash"] else self.dummy_hash
            try:
                verified = self.hasher.verify(stored, password)
            except (VerificationError, InvalidHashError):
                verified = False
            if row and row["is_active"] and not row["locked"]:
                if verified:
                    user_id = row["user_id"]
                    conn.execute(
                        text("SELECT set_config('uslp.actor_user_id',:actor,true)"), {"actor": str(user_id)}
                    )
                    conn.execute(
                        text(
                            "UPDATE uslp.users SET failed_login_attempts=0,locked_until=NULL,"
                            "last_login_at=now() WHERE user_id=:uid"
                        ),
                        {"uid": user_id},
                    )
                    Access.load(conn, user_id)
                else:
                    # After a timed lock expires the next failed attempt starts a new counter.
                    attempts = 1 if row["locked_until"] else row["failed_login_attempts"] + 1
                    conn.execute(
                        text(
                            "UPDATE uslp.users SET failed_login_attempts=:attempts,"
                            "locked_until=CASE WHEN :attempts >=5 THEN now()+interval '15 minutes' "
                            "ELSE NULL END WHERE user_id=:uid"
                        ),
                        {"attempts": attempts, "uid": row["user_id"]},
                    )
        if user_id is None:
            raise PortalError(DENIED, 401)
        token = secrets.token_urlsafe(32)
        with self.lock:
            now = time.monotonic()
            self.sessions = {k: v for k, v in self.sessions.items() if v[1] > now}
            self.sessions[token] = (user_id, now + TTL)
        return {"token": token}

    def request(self, operation, token, fields):
        if operation == "login":
            require_fields(self.login, (), fields)
            return self.login(**fields)
        with self.lock:
            session = self.sessions.get(token)
            if not session or session[1] <= time.monotonic():
                self.sessions.pop(token, None)
                raise PortalError("Your session has ended. Please sign in again.", 401)
            if operation == "logout":
                del self.sessions[token]
                return {}
        if operation != "snapshot" and operation not in ACTIONS:
            raise PortalError("Unknown portal action.", 404)
        with self.engine.begin() as conn:
            try:
                who = Access.load(conn, session[0])
            except PortalError:
                with self.lock:
                    self.sessions.pop(token, None)
                raise
            if operation == "snapshot":
                return snapshot(conn, who)
            _, function = ACTIONS[operation]
            if not who.allows(operation):
                raise PortalError("Your account does not have permission for that action.", 403)
            require_fields(function, (conn, who), fields)
            conn.execute(
                text("SELECT set_config('uslp.actor_user_id',:actor,true)"), {"actor": str(who.user_id)}
            )
            return function(conn, who, **fields)


def require_fields(function, positional, fields):
    try:
        inspect.signature(function).bind(*positional, **fields)
    except TypeError:
        raise PortalError("The request is missing a field or contains an unknown field.") from None


def database_error(error):
    code = getattr(error.orig, "sqlstate", None)
    messages = {
        "23505": "That identifier or relationship already exists.",
        "23503": "This record is linked to other data, or a selected record is missing. "
        "Keep the history and deactivate or withdraw the record where appropriate.",
        "23514": "The change conflicts with a database rule. Check the dates, status and values.",
        "23502": "A required value is missing.",
        "22001": "An entered value is too long.",
        "40001": "Another user changed the record. Refresh and try again.",
        "40P01": "Another update is in progress. Refresh and try again.",
        "42501": "The database service login needs its project grants. Run setup again.",
        "42P01": "The project tables are missing. Check the database you selected in setup.",
        "42703": "The desktop update is missing. Run setup_portal.py.",
    }
    if code in messages:
        return PortalError(messages[code], 409)
    return PortalError("The database request could not finish. Check PostgreSQL and your local setup.", 503)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        # All desktop traffic stays on loopback. Reject browser-originated requests.
        if self.headers.get("Origin") or self.headers.get_content_type() != "application/json":
            return self.reply(403, {"error": "Use the desktop client."})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 32768:
                raise PortalError("Invalid request size.", 413)
            fields = json.loads(self.rfile.read(size))
            if not isinstance(fields, dict):
                raise PortalError("Invalid request.")
            token = self.headers.get("Authorization", "").removeprefix("Bearer ")
            result = self.server.service.request(self.path.removeprefix("/"), token, fields)
        except PortalError as error:
            return self.reply(error.status, {"error": str(error)})
        except DBAPIError as error:
            translated = database_error(error)
            return self.reply(translated.status, {"error": str(translated)})
        except (ValueError, TypeError, UnicodeError):
            return self.reply(400, {"error": "The supplied fields are invalid."})
        except SQLAlchemyError:
            return self.reply(
                503, {"error": "PostgreSQL could not complete the request. Check the server and retry."}
            )
        return self.reply(200, result)

    def reply(self, status, payload):
        body = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def local_server(engine, port=0):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.service = PortalService(engine)
    return server


if __name__ == "__main__":
    db = make_engine(read_connection())
    with local_server(db, 8765) as server:
        print("USLP service ready on this computer. Launch portal.py --client in another window.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            db.dispose()
