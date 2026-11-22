-- Local development data for Group Three. Use after 01 and 02 on a fresh database.
-- This script provides the class-list schema, role defaults and one fictional student.
BEGIN;
-- Accept facts that are unknown rather than manufacture dates or split names.
ALTER TABLE uslp.programmes ALTER COLUMN department_id DROP NOT NULL,
    ALTER COLUMN programme_code DROP NOT NULL,
    ALTER COLUMN duration_years DROP NOT NULL;
ALTER TABLE uslp.students ALTER COLUMN first_name DROP NOT NULL,
    ALTER COLUMN last_name DROP NOT NULL,
    ALTER COLUMN study_level DROP NOT NULL,
    ALTER COLUMN admitted_on DROP NOT NULL,
    ALTER COLUMN admitted_on DROP DEFAULT;
ALTER TABLE uslp.students ADD COLUMN IF NOT EXISTS full_name VARCHAR(240) CHECK (btrim(full_name) <> '');
ALTER TABLE uslp.students ADD COLUMN IF NOT EXISTS gender VARCHAR(30) CHECK (btrim(gender) <> '');
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conrelid = 'uslp.students'::regclass AND conname = 'students_name_available') THEN
        ALTER TABLE uslp.students ADD CONSTRAINT students_name_available CHECK (
            full_name IS NOT NULL OR (first_name IS NOT NULL AND last_name IS NOT NULL));
    END IF;
END;
$$;

-- A source class list is not a dated teaching meeting or an attendance mark.
CREATE TABLE IF NOT EXISTS uslp.class_lists (
    class_list_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    programme_id BIGINT NOT NULL REFERENCES uslp.programmes(programme_id) ON DELETE RESTRICT,
    class_label VARCHAR(80) NOT NULL CHECK (btrim(class_label) <> ''),
    semester_label VARCHAR(80) NOT NULL CHECK (btrim(semester_label) <> ''),
    source_filename TEXT NOT NULL CHECK (btrim(source_filename) <> ''),
    source_sha256 VARCHAR(64) NOT NULL UNIQUE CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    imported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS uslp.class_list_entries (
    class_list_id BIGINT NOT NULL REFERENCES uslp.class_lists(class_list_id) ON DELETE RESTRICT,
    student_id BIGINT NOT NULL REFERENCES uslp.students(student_id) ON DELETE RESTRICT,
    source_row SMALLINT NOT NULL CHECK (source_row > 0),
    source_code VARCHAR(40) NOT NULL CHECK (btrim(source_code) <> ''),
    PRIMARY KEY (class_list_id, student_id),
    UNIQUE (class_list_id, source_row),
    UNIQUE (class_list_id, source_code)
);

CREATE INDEX IF NOT EXISTS idx_students_full_name ON uslp.students(full_name);
CREATE INDEX IF NOT EXISTS idx_class_list_entries_student ON uslp.class_list_entries(student_id);
CREATE INDEX IF NOT EXISTS idx_class_lists_programme ON uslp.class_lists(programme_id);
CREATE OR REPLACE VIEW uslp.v_student_directory AS
SELECT s.student_id, s.student_number, s.first_name, s.last_name, s.email,
       s.study_level, s.status, p.programme_code, p.programme_name,
       d.department_code, d.department_name,
       coalesce(s.full_name::text, concat_ws(' ', s.first_name, s.last_name)) AS full_name, s.gender
FROM uslp.students s
JOIN uslp.programmes p ON p.programme_id = s.programme_id
LEFT JOIN uslp.departments d ON d.department_id = p.department_id;

CREATE OR REPLACE VIEW uslp.v_enrollment_details AS
SELECT e.enrollment_id, e.student_id, s.student_number,
       coalesce(s.full_name::text, concat_ws(' ', s.first_name, s.last_name)) AS student_name,
       o.offering_id, c.course_code, c.course_title,
       a.session_name, t.semester_name, e.enrolled_on, e.status
FROM uslp.enrollments e
JOIN uslp.students s ON s.student_id = e.student_id
JOIN uslp.course_offerings o ON o.offering_id = e.offering_id
JOIN uslp.courses c ON c.course_id = o.course_id
JOIN uslp.semesters t ON t.semester_id = o.semester_id
JOIN uslp.academic_sessions a ON a.academic_session_id = t.academic_session_id;

CREATE OR REPLACE VIEW uslp.v_class_list AS
SELECT l.class_list_id, e.source_row, s.student_number,
       coalesce(s.full_name::text, concat_ws(' ', s.first_name, s.last_name)) AS full_name,
       s.gender, e.source_code, l.class_label, l.semester_label,
       p.programme_name, l.source_filename, l.source_sha256
FROM uslp.class_list_entries e
JOIN uslp.class_lists l ON l.class_list_id = e.class_list_id
JOIN uslp.students s ON s.student_id = e.student_id
JOIN uslp.programmes p ON p.programme_id = l.programme_id;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'uslp.class_lists'::regclass AND tgname = 'audit_class_lists') THEN
        CREATE TRIGGER audit_class_lists AFTER INSERT OR UPDATE OR DELETE ON uslp.class_lists
        FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('class_list_id');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'uslp.class_list_entries'::regclass AND tgname = 'audit_class_list_entries') THEN
        CREATE TRIGGER audit_class_list_entries AFTER INSERT OR UPDATE OR DELETE ON uslp.class_list_entries
        FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('class_list_id', 'student_id');
    END IF;
END;
$$;

INSERT INTO uslp.roles(role_name, description) VALUES
('Super Administrator', 'Manage accounts, roles and academic records'),
('Administrator', 'Manage operational academic records'),
('Registrar', 'Manage students, academic structure and enrollment'),
('Lecturer', 'Work with assigned course offerings'),
('Student', 'View the linked student profile and enrolled courses') ON CONFLICT (role_name) DO NOTHING;

CREATE TEMP TABLE team_base_permissions (
    permission_code varchar(80) PRIMARY KEY,
    description text NOT NULL
) ON COMMIT DROP;

INSERT INTO team_base_permissions(permission_code, description) VALUES
('students.view', 'View student records'),
('students.create', 'Register students'),
('students.update', 'Update student details'),
('students.deactivate', 'Deactivate students'),
('lecturers.manage', 'Manage lecturer profiles'),
('academics.manage', 'Manage departments, programmes and academic periods'),
('courses.view', 'View courses and offerings'),
('courses.manage', 'Manage courses and teaching assignments'),
('enrollments.view', 'View enrollment records'),
('enrollments.create', 'Create enrollments'),
('enrollments.update', 'Withdraw or complete enrollments'),
('attendance.view', 'View attendance'),
('attendance.record', 'Record attendance'),
('attendance.correct', 'Correct attendance with a reason'),
('users.manage', 'Manage application accounts'),
('roles.manage', 'Manage role assignments and permissions'),
('audit.view', 'View administrative change history');

INSERT INTO uslp.permissions(permission_code, description)
SELECT permission_code, description FROM team_base_permissions
ON CONFLICT (permission_code) DO NOTHING;

INSERT INTO uslp.role_permissions(role_id, permission_id)
SELECT r.role_id, p.permission_id FROM uslp.roles r CROSS JOIN uslp.permissions p
JOIN team_base_permissions b ON b.permission_code = p.permission_code
WHERE r.role_name = 'Super Administrator'
   OR (r.role_name = 'Administrator' AND p.permission_code NOT IN ('roles.manage'))
   OR (r.role_name = 'Registrar' AND p.permission_code IN
       ('students.view', 'students.create', 'students.update', 'students.deactivate',
        'academics.manage', 'courses.view', 'courses.manage', 'enrollments.view',
        'enrollments.create', 'enrollments.update', 'attendance.view'))
   OR (r.role_name = 'Lecturer' AND p.permission_code IN
       ('students.view', 'courses.view', 'enrollments.view', 'attendance.view', 'attendance.record'))
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Development fixtures. A student record can exist without an account.
INSERT INTO uslp.departments(department_code, department_name)
VALUES ('G3-DEV', 'Practice Department')
ON CONFLICT (department_code) DO NOTHING;

INSERT INTO uslp.programmes(department_id, programme_code, programme_name)
SELECT department_id, 'G3-DEV', 'Practice Programme'
FROM uslp.departments WHERE department_code = 'G3-DEV'
ON CONFLICT (programme_code) DO NOTHING;

INSERT INTO uslp.students(student_number, full_name, programme_id)
SELECT 'G3-DEV-001', 'Practice Student', programme_id
FROM uslp.programmes WHERE programme_code = 'G3-DEV'
ON CONFLICT (student_number) DO NOTHING;

COMMIT;
