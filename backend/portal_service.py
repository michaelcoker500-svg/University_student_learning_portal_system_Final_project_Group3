"""Run the Group Three HTTPS API on the computer hosting PostgreSQL."""

import argparse
import inspect
import json
import secrets
import time
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from .portal_data import ACTIONS, Access, PortalError, audit_log, snapshot
from .settings import make_engine, read_connection
from .team_tls import server_identity
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
        if operation not in {"snapshot", "audit_log"} and operation not in ACTIONS:
            raise PortalError("Unknown portal action.", 404)
        with self.engine.begin() as conn:
            if operation in {"snapshot", "audit_log"}:
                # All lists in a response come from the same committed database snapshot.
                conn.exec_driver_sql("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            try:
                who = Access.load(conn, session[0])
            except PortalError:
                with self.lock:
                    self.sessions.pop(token, None)
                raise
            if operation == "snapshot":
                return snapshot(conn, who)
            if operation == "audit_log":
                require_fields(audit_log, (conn, who), fields)
                return audit_log(conn, who, **fields)
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
    if code == "23001":  # RESTRICT on newer PostgreSQL versions
        code = "23503"
    if code in messages:
        return PortalError(messages[code], 409)
    return PortalError("The database request could not finish. Check PostgreSQL and your local setup.", 503)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path != "/health":
            return self.reply(404, {"error": "Unknown portal action."})
        try:
            with self.server.service.engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1 FROM uslp.v_student_directory LIMIT 1")
        except SQLAlchemyError:
            return self.reply(503, {"error": "Database unavailable. Check the backend terminal and PostgreSQL."})
        return self.reply(200, {"status": "ok", "api_version": 1})

    def do_POST(self):
        # The API accepts JSON requests from the desktop application.
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
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


class TeamServer(ThreadingHTTPServer):
    def __init__(self, host, port, engine, context):
        self.context = context
        self.service = PortalService(engine)
        super().__init__((host, port), Handler)

    def get_request(self):
        client, peer = super().get_request()
        client.settimeout(15)
        # The first read performs the handshake in the request thread.
        return self.context.wrap_socket(client, server_side=True, do_handshake_on_connect=False), peer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="this computer's reachable IPv4 address")
    parser.add_argument("--port", type=int, default=8765, help="API port (default 8765)")
    args = parser.parse_args()
    db = None
    try:
        config = read_connection()
        db = make_engine(config)
        with db.connect() as conn:
            conn.exec_driver_sql("SELECT 1 FROM uslp.v_student_directory LIMIT 1")
        context, profile = server_identity(args.host, args.port)
        with TeamServer(args.host, args.port, db, context) as server:
            print(f"Portal API ready at https://{args.host}:{args.port}  |  Database: {config['dbname']}", flush=True)
            print(f"Team connection file: {profile}", flush=True)
            print("Leave this terminal open during live tests. Press Ctrl+C to stop.", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except SQLAlchemyError:
        print("Database connection failed. Check the PostgreSQL service and run python -m backend.check_database.",
              file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Portal service could not start: {error}", file=sys.stderr)
        return 1
    finally:
        if db is not None:
            db.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
