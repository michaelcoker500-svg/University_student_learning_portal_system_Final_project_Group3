# Group Three University Student Learning Portal

The PyQt6 desktop GUI uses one HTTPS service on the backend developer's Windows PC. PostgreSQL on that PC holds the supplied BSEM 1101 Semester 3 roster, originally 45 students. The frontend developer needs Python and PyQt6. For everyday development, open the folder containing this README in VS Code.

The downloadable **Group3 Developer Guide** gives the full Windows setup, a pgAdmin walkthrough, the GitHub workflow, two-PC test steps and troubleshooting. Run the commands below from the project root in the VS Code PowerShell terminal.

## Use your existing database

In pgAdmin, open Query Tool on the database where you already ran the project scripts. These read-only queries identify the database and the class list.

```sql
SELECT current_database(), count(*) AS directory_students
FROM uslp.v_student_directory;

SELECT class_label, semester_label, count(*) AS roster_entries
FROM uslp.v_class_list
GROUP BY class_label, semester_label
ORDER BY class_label, semester_label;
```

The original source shows BSEM 1101, Semester 3, 45 entries. Keep the exact database name from the first query. Back up that database before the first setup. An existing installation goes straight to setup. Setup verifies the source list by its fingerprint, applies the supplied 07, 08 and 09 updates when needed, and grants the service account access. Update 09 creates the writable `uslp_portal.students` view expected by the desktop service. Counts can change as the team manages students.

On the backend PC, using Python 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m backend.setup_portal
.\.venv\Scripts\python.exe -m backend.check_database
.\.venv\Scripts\python.exe -m backend.setup_portal --add-account
ipconfig
```

Use localhost and your existing PostgreSQL port and database name during setup. Supply the PostgreSQL owner password only on the host. The first portal account is `group3admin`. Create a named Administrator portal account for a teammate testing add, edit and delete. Use the Wi-Fi or Ethernet adapter IPv4 from `ipconfig` in place of the example below.

```powershell
.\.venv\Scripts\python.exe -m backend.portal_service --host 192.168.1.50
```

Keep the terminal open. It prints the path to **portal-team.json**. Give each developer this one public connection file and their own portal login. Keep the database settings, private key, original roster SQL and backups on the host. Live testing needs a route to the API on TCP 8765, usually on the same private Wi-Fi or hotspot. PostgreSQL can listen only on localhost.

## Open the GUI

On the frontend PC, install the frontend environment once.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r frontend\requirements.txt
.\.venv\Scripts\python.exe main.py
```

At sign-in, click **Choose team connection file**, open the backend developer's `portal-team.json` and use your portal account. The selection is saved for the next launch. To view both GUIs during a test, install the frontend requirements in the host's existing environment too, then start the GUI in a second terminal.

In VS Code use **Python: Select Interpreter** and choose `.venv\Scripts\python.exe`. In **Run and Debug**, select **Frontend - live GUI**, **Frontend - offline preview**, **Backend - database setup** or **Backend - start team API**. The backend launch asks for the host's IPv4. Enter its reachable network address for team tests.

For layout or interaction work while the host is offline:

```powershell
.\.venv\Scripts\python.exe main.py --demo
```

Preview opens with fictional records in memory and resets when you close it. To edit live records, close preview and open the live GUI. A network failure in live mode shows an error and preserves the last displayed snapshot. The application never queues offline writes.

## Check student changes

1. Two staff members sign in, open **Students** and find an existing student by official ID or part of their name.
2. On the frontend PC select **Add student**. Use an unused test ID such as `G3-TEST-001`, a fictional name and an active programme. The writer refreshes after commit. The other open GUI polls every four seconds. While a modal form is open, background display updates wait.
3. In pgAdmin run the query below. Re-run it after each change. A pgAdmin result grid shows the result from its last execution.
4. Select the test row and **Edit student**. Try a committed change to its name from pgAdmin as well. See the guide for the exact SQL.
5. Delete the fictional record. Search for its ID again and re-run the query. Both should be empty. The original 45 remain when the team has only changed the test row.

```sql
SELECT student_number, full_name, programme_name, status
FROM uslp.v_student_directory
WHERE student_number = 'G3-TEST-001';
```

The student directory includes new students. The imported class list records membership of the original source, so a new student gets a directory row without a fictional source row. Confirming **Delete** on an unlinked imported student also removes that student's source membership. The service audits both changes in one transaction. A portal account or enrolment history protects the student from deletion. **Deactivate** retains the record, its roster membership and its history.

The host can also run an automated check with two API sessions and an independent SQL connection. It tests one uniquely named fictional row and cleans it up. Audit entries remain. Supply the exact connection-file path printed by your service.

```powershell
.\.venv\Scripts\python.exe verify_sync.py "C:\path\to\portal-team.json"
```

## Divide the work in GitHub

| Files | Owner | Purpose |
|---|---|---|
| `frontend/portal.py` | Frontend | PyQt6 windows, tables, search, dialogs, polling and status |
| `frontend/portal_client.py` | Frontend, coordinate contract edits | HTTPS, certificate verification, portal session and visible record models |
| `frontend/preview.py` | Frontend | Offline example data and interactions |
| `backend/portal_service.py`, `backend/portal_data.py` | Backend | JSON actions, sessions, role checks, queries and transactions |
| `backend/database/`, `backend/setup_portal.py` | Backend | Schema, migrations, grants and account setup |
| `backend/roster.py`, `backend/team_tls.py` | Backend | Identify the original class list and issue the team HTTPS profile |
| `.vscode/launch.json`, `verify_sync.py` | Both | Shared launches and two-client acceptance test |

The initial split patch supplied in the outer ZIP was generated against **d5c25cd**, the commit inside the uploaded project. Apply it once on a new branch in your existing clone to preserve its history. The complete runnable source is also supplied under `Group3_Portal/`. The patch and this source are two ways to get the same code. Detailed steps are in the guide.

For each feature, agree on the action and its JSON fields. Work on separate branches, open pull requests and test compatible revisions together. Each developer pulls merged code and restarts the changed process. The backend developer applies database migrations on the host. Record changes flow through the live API immediately after commit and are visible to authorised GUI sessions on refresh.

## Student API contract

The service accepts JSON with Content-Type application/json. After login, send the returned token as Authorization: Bearer TOKEN. The client never submits SQL or a role. The service checks permissions on each action.

| Request | JSON fields | Successful result |
|---|---|---|
| GET /health | None | status and api_version after a database read |
| POST /login | username, password | token |
| POST /snapshot | {} | user, actions, students, courses, enrollments and lookups |
| POST /audit_log | limit, offset | Staff-only page of persistent audit entries and total count |
| POST /add_student | number, name, programme | id |
| POST /edit_student | id, name, programme, version | id |
| POST /deactivate_student | id | id |
| POST /delete_student | id | id |
| POST /logout | {} | {} |

`number` is the official student ID, a string. `id` is the database's internal integer. `programme` in write requests is an integer from `lookups.programmes`. Each student in a snapshot supplies `id, number, name, programme_id, programme, status, version`. Pass the last-read version back unchanged on edit. Search filters the current role-scoped snapshot in the GUI. Existing code also supports courses, offerings, academic periods, enrolments and lesson progress.

The audit endpoint returns at most 200 records per request, newest first, with `id`, `occurred_at`, `actor_user_id`, `actor_username`, `actor_name`, `database_user`, `table_name`, `record_key`, `operation`, `old_data` and `new_data`. Staff accounts can page with `limit` (default 50) and `offset` (default 0). Other roles receive HTTP 403. The dashboard audit view reads this endpoint, so committed records remain available after sign-out and across sessions.

On an already configured backend host, rerun `python -m backend.setup_portal` once after updating the project. Setup grants the runtime service account read access to the existing audit table; no table or migration change is needed.

A failed action returns an error string and HTTP status. Handle 400 for invalid input, 401 for a missing or expired session, 403 for permissions, 409 for conflicting data, and 503 for service or database availability. After an interrupted write, refresh and search before retrying.

## Restoring after a lost database

The supplied private class-list import is in your **original** ZIP under `database/03_sample_data (1).sql`. Keep that ZIP on the backend PC. Prefer restoring your latest private database backup, which includes changes made since import. To rebuild the initial 45 on an empty database, run `backend/database/01_schema.sql`, then `02_features.sql`, then the original private `03_sample_data (1).sql` in pgAdmin. Run backend setup afterwards. The optional `06_verify_backend.sql` in this package expects the post-setup schema in a quiet development copy. Its fixture transaction rolls back. `03_team_dev.sql` from the original repository is a historical fictional seed and is excluded from the 45-student installation sequence.
