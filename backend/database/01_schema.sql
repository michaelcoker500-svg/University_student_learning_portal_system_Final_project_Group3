-- University Student Learning Portal: initial PostgreSQL schema.
-- Run once in a NEW, empty uslp_db. Existing data is never dropped.
-- A second run deliberately fails instead of silently changing an existing schema.
BEGIN;
CREATE SCHEMA uslp;

CREATE TABLE uslp.users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(80) NOT NULL,
    password_hash TEXT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_username_format CHECK (username = lower(btrim(username)) AND username <> ''),
    CONSTRAINT users_username_unique UNIQUE (username),
    CONSTRAINT users_hash_format CHECK (password_hash IS NULL OR password_hash LIKE '$argon2id$%'),
    CONSTRAINT users_active_requires_hash CHECK (NOT is_active OR password_hash IS NOT NULL),
    CONSTRAINT users_failed_attempts_nonnegative CHECK (failed_login_attempts >= 0)
);

CREATE TABLE uslp.roles (
    role_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE CHECK (btrim(role_name) <> ''),
    description TEXT NOT NULL
);

CREATE TABLE uslp.permissions (
    permission_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    permission_code VARCHAR(80) NOT NULL UNIQUE CHECK (btrim(permission_code) <> ''),
    description TEXT NOT NULL
);

CREATE TABLE uslp.user_roles (
    user_id BIGINT NOT NULL REFERENCES uslp.users(user_id) ON DELETE RESTRICT,
    role_id BIGINT NOT NULL REFERENCES uslp.roles(role_id) ON DELETE RESTRICT,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE uslp.role_permissions (
    role_id BIGINT NOT NULL REFERENCES uslp.roles(role_id) ON DELETE RESTRICT,
    permission_id BIGINT NOT NULL REFERENCES uslp.permissions(permission_id) ON DELETE RESTRICT,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE uslp.departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_code VARCHAR(20) NOT NULL UNIQUE,
    department_name VARCHAR(150) NOT NULL CHECK (btrim(department_name) <> ''),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT departments_code_format CHECK (department_code = upper(btrim(department_code)) AND department_code <> '')
);

CREATE TABLE uslp.programmes (
    programme_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES uslp.departments(department_id) ON DELETE RESTRICT,
    programme_code VARCHAR(20) NOT NULL UNIQUE,
    programme_name VARCHAR(150) NOT NULL CHECK (btrim(programme_name) <> ''),
    duration_years SMALLINT NOT NULL CHECK (duration_years > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT programmes_code_format CHECK (programme_code = upper(btrim(programme_code)) AND programme_code <> '')
);

CREATE TABLE uslp.students (
    student_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_number VARCHAR(40) NOT NULL UNIQUE CHECK (btrim(student_number) <> ''),
    user_id BIGINT UNIQUE REFERENCES uslp.users(user_id) ON DELETE RESTRICT,
    programme_id BIGINT NOT NULL REFERENCES uslp.programmes(programme_id) ON DELETE RESTRICT,
    first_name VARCHAR(80) NOT NULL CHECK (btrim(first_name) <> ''),
    last_name VARCHAR(80) NOT NULL CHECK (btrim(last_name) <> ''),
    email VARCHAR(254),
    study_level SMALLINT NOT NULL CHECK (study_level > 0),
    status VARCHAR(15) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'graduated')),
    admitted_on DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE uslp.lecturers (
    lecturer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    staff_number VARCHAR(40) NOT NULL UNIQUE CHECK (staff_number = upper(btrim(staff_number)) AND staff_number <> ''),
    user_id BIGINT UNIQUE REFERENCES uslp.users(user_id) ON DELETE RESTRICT,
    department_id BIGINT NOT NULL REFERENCES uslp.departments(department_id) ON DELETE RESTRICT,
    first_name VARCHAR(80) NOT NULL CHECK (btrim(first_name) <> ''),
    last_name VARCHAR(80) NOT NULL CHECK (btrim(last_name) <> ''),
    email VARCHAR(254),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE uslp.courses (
    course_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES uslp.departments(department_id) ON DELETE RESTRICT,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_title VARCHAR(180) NOT NULL CHECK (btrim(course_title) <> ''),
    credits SMALLINT NOT NULL CHECK (credits > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT courses_code_format CHECK (course_code = upper(btrim(course_code)) AND course_code <> '')
);

CREATE TABLE uslp.academic_sessions (
    academic_session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_name VARCHAR(60) NOT NULL UNIQUE CHECK (btrim(session_name) <> ''),
    starts_on DATE NOT NULL,
    ends_on DATE NOT NULL,
    CONSTRAINT academic_sessions_date_order CHECK (ends_on >= starts_on)
);

CREATE TABLE uslp.semesters (
    semester_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    academic_session_id BIGINT NOT NULL REFERENCES uslp.academic_sessions(academic_session_id) ON DELETE RESTRICT,
    semester_name VARCHAR(60) NOT NULL CHECK (btrim(semester_name) <> ''),
    starts_on DATE NOT NULL,
    ends_on DATE NOT NULL,
    CONSTRAINT semesters_name_per_session UNIQUE (academic_session_id, semester_name),
    CONSTRAINT semesters_date_order CHECK (ends_on >= starts_on)
);

-- One offering of a course per semester in this first version.
CREATE TABLE uslp.course_offerings (
    offering_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    course_id BIGINT NOT NULL REFERENCES uslp.courses(course_id) ON DELETE RESTRICT,
    semester_id BIGINT NOT NULL REFERENCES uslp.semesters(semester_id) ON DELETE RESTRICT,
    enrollment_open BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT course_offerings_course_semester_unique UNIQUE (course_id, semester_id)
);

-- Allows co-teaching without storing a comma-separated list of lecturers.
CREATE TABLE uslp.teaching_assignments (
    offering_id BIGINT NOT NULL REFERENCES uslp.course_offerings(offering_id) ON DELETE RESTRICT,
    lecturer_id BIGINT NOT NULL REFERENCES uslp.lecturers(lecturer_id) ON DELETE RESTRICT,
    PRIMARY KEY (offering_id, lecturer_id)
);

CREATE TABLE uslp.enrollments (
    enrollment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES uslp.students(student_id) ON DELETE RESTRICT,
    offering_id BIGINT NOT NULL REFERENCES uslp.course_offerings(offering_id) ON DELETE RESTRICT,
    enrolled_on DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(12) NOT NULL DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'withdrawn', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT enrollments_student_offering_unique UNIQUE (student_id, offering_id)
);

CREATE TABLE uslp.class_sessions (
    class_session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    offering_id BIGINT NOT NULL REFERENCES uslp.course_offerings(offering_id) ON DELETE RESTRICT,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    topic VARCHAR(180) NOT NULL CHECK (btrim(topic) <> ''),
    CONSTRAINT class_sessions_time_order CHECK (ends_at > starts_at),
    CONSTRAINT class_sessions_start_unique UNIQUE (offering_id, starts_at)
);

CREATE TABLE uslp.attendance (
    attendance_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    enrollment_id BIGINT NOT NULL REFERENCES uslp.enrollments(enrollment_id) ON DELETE RESTRICT,
    class_session_id BIGINT NOT NULL REFERENCES uslp.class_sessions(class_session_id) ON DELETE RESTRICT,
    status VARCHAR(10) NOT NULL CHECK (status IN ('present', 'late', 'absent', 'excused')),
    recorded_by BIGINT NOT NULL REFERENCES uslp.users(user_id) ON DELETE RESTRICT,
    correction_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT attendance_enrollment_class_unique UNIQUE (enrollment_id, class_session_id)
);

CREATE TABLE uslp.audit_logs (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_user_id BIGINT REFERENCES uslp.users(user_id) ON DELETE RESTRICT,
    database_user TEXT NOT NULL DEFAULT CURRENT_USER,
    table_name TEXT NOT NULL,
    record_key JSONB NOT NULL,
    operation VARCHAR(6) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
COMMIT;
