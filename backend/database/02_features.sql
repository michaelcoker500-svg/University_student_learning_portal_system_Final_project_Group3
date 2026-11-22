-- Run after 01_schema.sql and BEFORE sample data.
BEGIN;

-- PK and UNIQUE constraints already create indexes; these support FK lookups
-- and the filters used by the planned management screens.
CREATE INDEX idx_programmes_department ON uslp.programmes(department_id);
CREATE INDEX idx_students_programme ON uslp.students(programme_id);
CREATE INDEX idx_students_name ON uslp.students(last_name, first_name);
CREATE INDEX idx_lecturers_department ON uslp.lecturers(department_id);
CREATE INDEX idx_courses_department ON uslp.courses(department_id);
CREATE INDEX idx_offerings_semester ON uslp.course_offerings(semester_id);
CREATE INDEX idx_teaching_lecturer ON uslp.teaching_assignments(lecturer_id);
CREATE INDEX idx_enrollments_offering ON uslp.enrollments(offering_id);
CREATE INDEX idx_attendance_class ON uslp.attendance(class_session_id);
CREATE INDEX idx_attendance_recorder ON uslp.attendance(recorded_by);
CREATE INDEX idx_user_roles_role ON uslp.user_roles(role_id);
CREATE INDEX idx_role_permissions_permission ON uslp.role_permissions(permission_id);
CREATE INDEX idx_audit_actor ON uslp.audit_logs(actor_user_id);
CREATE INDEX idx_audit_table_time ON uslp.audit_logs(table_name, occurred_at DESC);

CREATE FUNCTION uslp.set_updated_at() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
BEGIN
    NEW.updated_at := clock_timestamp();
    RETURN NEW;
END;
$$;

CREATE TRIGGER users_updated BEFORE UPDATE ON uslp.users FOR EACH ROW EXECUTE FUNCTION uslp.set_updated_at();
CREATE TRIGGER students_updated BEFORE UPDATE ON uslp.students FOR EACH ROW EXECUTE FUNCTION uslp.set_updated_at();
CREATE TRIGGER lecturers_updated BEFORE UPDATE ON uslp.lecturers FOR EACH ROW EXECUTE FUNCTION uslp.set_updated_at();
CREATE TRIGGER courses_updated BEFORE UPDATE ON uslp.courses FOR EACH ROW EXECUTE FUNCTION uslp.set_updated_at();
CREATE TRIGGER attendance_updated BEFORE UPDATE ON uslp.attendance FOR EACH ROW EXECUTE FUNCTION uslp.set_updated_at();

CREATE FUNCTION uslp.validate_semester() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
DECLARE parent_start DATE; parent_end DATE;
BEGIN
    SELECT starts_on, ends_on INTO parent_start, parent_end
    FROM uslp.academic_sessions WHERE academic_session_id = NEW.academic_session_id FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Academic session does not exist' USING ERRCODE = '23503';
    END IF;
    IF NEW.starts_on < parent_start OR NEW.ends_on > parent_end THEN
        RAISE EXCEPTION 'Semester must lie within its academic session' USING ERRCODE = '23514';
    END IF;
    IF TG_OP = 'UPDATE' AND EXISTS (
        SELECT 1 FROM uslp.class_sessions c
        JOIN uslp.course_offerings o ON o.offering_id = c.offering_id
        WHERE o.semester_id = OLD.semester_id
          AND ((c.starts_at AT TIME ZONE 'UTC')::date < NEW.starts_on
            OR (c.ends_at AT TIME ZONE 'UTC')::date > NEW.ends_on)
    ) THEN
        RAISE EXCEPTION 'Semester dates would exclude an existing class' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER semester_dates BEFORE INSERT OR UPDATE ON uslp.semesters
FOR EACH ROW EXECUTE FUNCTION uslp.validate_semester();

CREATE FUNCTION uslp.protect_academic_session_dates() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM uslp.semesters WHERE academic_session_id = OLD.academic_session_id
               AND (starts_on < NEW.starts_on OR ends_on > NEW.ends_on)) THEN
        RAISE EXCEPTION 'Academic session dates would exclude an existing semester' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER academic_session_dates BEFORE UPDATE ON uslp.academic_sessions
FOR EACH ROW EXECUTE FUNCTION uslp.protect_academic_session_dates();

CREATE FUNCTION uslp.protect_offering_identity() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
BEGIN
    IF NEW.course_id IS DISTINCT FROM OLD.course_id OR NEW.semester_id IS DISTINCT FROM OLD.semester_id THEN
        RAISE EXCEPTION 'Create a new offering instead of changing its course or semester' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER offering_identity BEFORE UPDATE ON uslp.course_offerings
FOR EACH ROW EXECUTE FUNCTION uslp.protect_offering_identity();

CREATE FUNCTION uslp.validate_enrollment() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
DECLARE student_status TEXT; accepts_enrollment BOOLEAN;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.student_id IS DISTINCT FROM OLD.student_id
           OR NEW.offering_id IS DISTINCT FROM OLD.offering_id
           OR NEW.enrolled_on IS DISTINCT FROM OLD.enrolled_on THEN
            RAISE EXCEPTION 'Enrollment identity and registration date cannot be rewritten' USING ERRCODE = '23514';
        END IF;
        IF NEW.status = OLD.status OR NEW.status <> 'enrolled' THEN
            RETURN NEW;
        END IF;
    END IF;
    IF NEW.status = 'enrolled' THEN
        SELECT status INTO student_status FROM uslp.students WHERE student_id = NEW.student_id FOR SHARE;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Student does not exist' USING ERRCODE = '23503';
        END IF;
        SELECT enrollment_open INTO accepts_enrollment FROM uslp.course_offerings
        WHERE offering_id = NEW.offering_id FOR SHARE;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Course offering does not exist' USING ERRCODE = '23503';
        END IF;
        IF student_status <> 'active' OR NOT accepts_enrollment THEN
            RAISE EXCEPTION 'Enrollment needs an active student and an open offering' USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER enrollment_rules BEFORE INSERT OR UPDATE ON uslp.enrollments
FOR EACH ROW EXECUTE FUNCTION uslp.validate_enrollment();

CREATE FUNCTION uslp.validate_class_session() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
DECLARE term_start DATE; term_end DATE;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.offering_id IS DISTINCT FROM OLD.offering_id THEN
            RAISE EXCEPTION 'A class cannot be moved to a different offering' USING ERRCODE = '23514';
        END IF;
        IF NEW.starts_at IS DISTINCT FROM OLD.starts_at AND EXISTS (
            SELECT 1 FROM uslp.attendance WHERE class_session_id = OLD.class_session_id
        ) THEN
            RAISE EXCEPTION 'A class with attendance cannot have its start time rewritten' USING ERRCODE = '23514';
        END IF;
    END IF;
    SELECT s.starts_on, s.ends_on INTO term_start, term_end
    FROM uslp.semesters s JOIN uslp.course_offerings o ON o.semester_id = s.semester_id
    WHERE o.offering_id = NEW.offering_id FOR SHARE OF s, o;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Course offering does not exist' USING ERRCODE = '23503';
    END IF;
    IF (NEW.starts_at AT TIME ZONE 'UTC')::date < term_start
       OR (NEW.ends_at AT TIME ZONE 'UTC')::date > term_end THEN
        RAISE EXCEPTION 'Class must lie within its semester dates' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER class_session_rules BEFORE INSERT OR UPDATE ON uslp.class_sessions
FOR EACH ROW EXECUTE FUNCTION uslp.validate_class_session();

CREATE FUNCTION uslp.validate_attendance() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
DECLARE enrolled_offering BIGINT; class_offering BIGINT; enrollment_status TEXT;
        registration_date DATE; class_start TIMESTAMPTZ;
BEGIN
    SELECT offering_id, status, enrolled_on INTO enrolled_offering, enrollment_status, registration_date
    FROM uslp.enrollments WHERE enrollment_id = NEW.enrollment_id FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Enrollment does not exist' USING ERRCODE = '23503';
    END IF;
    SELECT offering_id, starts_at INTO class_offering, class_start
    FROM uslp.class_sessions WHERE class_session_id = NEW.class_session_id FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Class session does not exist' USING ERRCODE = '23503';
    END IF;
    IF enrolled_offering <> class_offering THEN
        RAISE EXCEPTION 'Attendance class and enrollment belong to different offerings' USING ERRCODE = '23514';
    END IF;
    IF (class_start AT TIME ZONE 'UTC')::date < registration_date THEN
        RAISE EXCEPTION 'Attendance cannot predate enrollment' USING ERRCODE = '23514';
    END IF;
    IF TG_OP = 'INSERT' AND enrollment_status <> 'enrolled' THEN
        RAISE EXCEPTION 'New attendance needs a current enrollment' USING ERRCODE = '23514';
    END IF;
    IF TG_OP = 'UPDATE' THEN
        IF NEW.enrollment_id IS DISTINCT FROM OLD.enrollment_id
           OR NEW.class_session_id IS DISTINCT FROM OLD.class_session_id THEN
            RAISE EXCEPTION 'Attendance cannot be reassigned to a different student or class' USING ERRCODE = '23514';
        END IF;
        IF NEW.status IS DISTINCT FROM OLD.status AND coalesce(btrim(NEW.correction_reason), '') = '' THEN
            RAISE EXCEPTION 'An attendance correction requires a reason' USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER attendance_rules BEFORE INSERT OR UPDATE ON uslp.attendance
FOR EACH ROW EXECUTE FUNCTION uslp.validate_attendance();

-- The application will set actor_user_id locally within each transaction.
-- This is attribution metadata, NOT an authorization mechanism.
-- Do not distribute owner/superuser credentials to normal application users.
CREATE FUNCTION uslp.audit_change() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
DECLARE before_row JSONB; after_row JSONB; key_row JSONB; key_name TEXT;
        key_values JSONB := '{}'::jsonb; actor_text TEXT;
BEGIN
    IF TG_OP <> 'INSERT' THEN before_row := to_jsonb(OLD) - 'password_hash'; END IF;
    IF TG_OP <> 'DELETE' THEN after_row := to_jsonb(NEW) - 'password_hash'; END IF;
    key_row := coalesce(after_row, before_row);
    FOREACH key_name IN ARRAY TG_ARGV LOOP
        key_values := key_values || jsonb_build_object(key_name, key_row -> key_name);
    END LOOP;
    actor_text := nullif(current_setting('uslp.actor_user_id', TRUE), '');
    INSERT INTO uslp.audit_logs(actor_user_id, table_name, record_key, operation, old_data, new_data)
    VALUES (actor_text::bigint, TG_TABLE_NAME, key_values, TG_OP, before_row, after_row);
    RETURN NULL; -- Return value is ignored by AFTER triggers.
END;
$$;

CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON uslp.users FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('user_id');
CREATE TRIGGER audit_roles AFTER INSERT OR UPDATE OR DELETE ON uslp.roles FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('role_id');
CREATE TRIGGER audit_permissions AFTER INSERT OR UPDATE OR DELETE ON uslp.permissions FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('permission_id');
CREATE TRIGGER audit_user_roles AFTER INSERT OR UPDATE OR DELETE ON uslp.user_roles FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('user_id', 'role_id');
CREATE TRIGGER audit_role_permissions AFTER INSERT OR UPDATE OR DELETE ON uslp.role_permissions FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('role_id', 'permission_id');
CREATE TRIGGER audit_departments AFTER INSERT OR UPDATE OR DELETE ON uslp.departments FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('department_id');
CREATE TRIGGER audit_programmes AFTER INSERT OR UPDATE OR DELETE ON uslp.programmes FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('programme_id');
CREATE TRIGGER audit_students AFTER INSERT OR UPDATE OR DELETE ON uslp.students FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('student_id');
CREATE TRIGGER audit_lecturers AFTER INSERT OR UPDATE OR DELETE ON uslp.lecturers FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('lecturer_id');
CREATE TRIGGER audit_courses AFTER INSERT OR UPDATE OR DELETE ON uslp.courses FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('course_id');
CREATE TRIGGER audit_academic_sessions AFTER INSERT OR UPDATE OR DELETE ON uslp.academic_sessions FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('academic_session_id');
CREATE TRIGGER audit_semesters AFTER INSERT OR UPDATE OR DELETE ON uslp.semesters FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('semester_id');
CREATE TRIGGER audit_offerings AFTER INSERT OR UPDATE OR DELETE ON uslp.course_offerings FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('offering_id');
CREATE TRIGGER audit_teaching AFTER INSERT OR UPDATE OR DELETE ON uslp.teaching_assignments FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('offering_id', 'lecturer_id');
CREATE TRIGGER audit_enrollments AFTER INSERT OR UPDATE OR DELETE ON uslp.enrollments FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('enrollment_id');
CREATE TRIGGER audit_class_sessions AFTER INSERT OR UPDATE OR DELETE ON uslp.class_sessions FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('class_session_id');
CREATE TRIGGER audit_attendance AFTER INSERT OR UPDATE OR DELETE ON uslp.attendance FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('attendance_id');

CREATE VIEW uslp.v_student_directory AS
SELECT s.student_id, s.student_number, s.first_name, s.last_name, s.email,
       s.study_level, s.status, p.programme_code, p.programme_name,
       d.department_code, d.department_name
FROM uslp.students s
JOIN uslp.programmes p ON p.programme_id = s.programme_id
JOIN uslp.departments d ON d.department_id = p.department_id;

CREATE VIEW uslp.v_enrollment_details AS
SELECT e.enrollment_id, e.student_id, s.student_number,
       s.first_name || ' ' || s.last_name AS student_name,
       o.offering_id, c.course_code, c.course_title,
       a.session_name, t.semester_name, e.enrolled_on, e.status
FROM uslp.enrollments e
JOIN uslp.students s ON s.student_id = e.student_id
JOIN uslp.course_offerings o ON o.offering_id = e.offering_id
JOIN uslp.courses c ON c.course_id = o.course_id
JOIN uslp.semesters t ON t.semester_id = o.semester_id
JOIN uslp.academic_sessions a ON a.academic_session_id = t.academic_session_id;

-- Percentage is for marked, non-excused attendance only. An unmarked class
-- is not silently counted as an absence. NULL means no eligible marks yet.
CREATE VIEW uslp.v_attendance_summary AS
SELECT e.enrollment_id, e.student_id, e.offering_id,
       count(a.attendance_id) AS marked_classes,
       count(*) FILTER (WHERE a.status = 'present') AS present_count,
       count(*) FILTER (WHERE a.status = 'late') AS late_count,
       count(*) FILTER (WHERE a.status = 'absent') AS absent_count,
       count(*) FILTER (WHERE a.status = 'excused') AS excused_count,
       round(100.0 * count(*) FILTER (WHERE a.status IN ('present', 'late'))
             / nullif(count(*) FILTER (WHERE a.status IN ('present', 'late', 'absent')), 0), 2)
             AS attendance_percentage
FROM uslp.enrollments e LEFT JOIN uslp.attendance a ON a.enrollment_id = e.enrollment_id
GROUP BY e.enrollment_id, e.student_id, e.offering_id;

-- This view exposes grants; services must still enforce them on each action.
CREATE VIEW uslp.v_user_permissions AS
SELECT DISTINCT u.user_id, u.username, p.permission_code
FROM uslp.users u
JOIN uslp.user_roles ur ON ur.user_id = u.user_id
JOIN uslp.role_permissions rp ON rp.role_id = ur.role_id
JOIN uslp.permissions p ON p.permission_id = rp.permission_id
WHERE u.is_active AND (u.locked_until IS NULL OR u.locked_until <= CURRENT_TIMESTAMP);

CREATE FUNCTION uslp.enroll_student(p_student_id BIGINT, p_offering_id BIGINT)
RETURNS BIGINT LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
DECLARE new_id BIGINT;
BEGIN
    INSERT INTO uslp.enrollments(student_id, offering_id)
    VALUES (p_student_id, p_offering_id) RETURNING enrollment_id INTO new_id;
    RETURN new_id;
END;
$$;

CREATE PROCEDURE uslp.record_attendance(p_enrollment_id BIGINT, p_class_session_id BIGINT,
                                      p_status TEXT, p_recorded_by BIGINT)
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
BEGIN
    INSERT INTO uslp.attendance(enrollment_id, class_session_id, status, recorded_by)
    VALUES (p_enrollment_id, p_class_session_id, p_status, p_recorded_by);
END;
$$;

CREATE PROCEDURE uslp.correct_attendance(p_attendance_id BIGINT, p_status TEXT,
                                       p_recorded_by BIGINT, p_reason TEXT)
LANGUAGE plpgsql SET search_path = pg_catalog, uslp AS $$
BEGIN
    IF coalesce(btrim(p_reason), '') = '' THEN
        RAISE EXCEPTION 'A correction requires a reason' USING ERRCODE = '23514';
    END IF;
    UPDATE uslp.attendance SET status = p_status, recorded_by = p_recorded_by,
           correction_reason = p_reason WHERE attendance_id = p_attendance_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Attendance record does not exist' USING ERRCODE = 'P0002';
    END IF;
END;
$$;
COMMIT;
