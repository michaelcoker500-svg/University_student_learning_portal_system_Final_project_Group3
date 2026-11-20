-- Run once on the portal database after the class-list import, as the USLP table owner.
-- The single statement also works inside the transaction used by setup_portal.py.
DO $roster$
DECLARE
    old_columns integer;
    reader record;
BEGIN
    PERFORM pg_advisory_xact_lock(hashtext('uslp_desktop_setup'));
    SELECT count(*) INTO old_columns
    FROM pg_attribute
    WHERE attrelid = 'uslp.students'::regclass AND attnum > 0 AND NOT attisdropped
      AND attname IN ('user_id','first_name','last_name','email','study_level','admitted_on');

    IF old_columns = 0 AND to_regclass('uslp.student_accounts') IS NOT NULL
                       AND to_regclass('uslp.student_profile_details') IS NOT NULL THEN
        RETURN;
    END IF;
    IF old_columns <> 6 OR to_regclass('uslp.student_accounts') IS NOT NULL
                        OR to_regclass('uslp.student_profile_details') IS NOT NULL THEN
        RAISE EXCEPTION 'The student schema differs from the project backup. Review the existing columns and links before running this update.';
    END IF;

    LOCK TABLE uslp.students IN ACCESS EXCLUSIVE MODE;
    CREATE TABLE uslp.student_accounts (
        student_id bigint PRIMARY KEY REFERENCES uslp.students(student_id) ON DELETE RESTRICT,
        user_id bigint NOT NULL UNIQUE REFERENCES uslp.users(user_id) ON DELETE RESTRICT
    );
    CREATE TABLE uslp.student_profile_details (
        student_id bigint PRIMARY KEY REFERENCES uslp.students(student_id) ON DELETE CASCADE,
        first_name varchar(80) CHECK (btrim(first_name) <> ''),
        last_name varchar(80) CHECK (btrim(last_name) <> ''),
        email varchar(254),
        study_level smallint CHECK (study_level > 0),
        admitted_on date
    );
    INSERT INTO uslp.student_accounts (student_id, user_id)
    SELECT student_id, user_id FROM uslp.students WHERE user_id IS NOT NULL;
    INSERT INTO uslp.student_profile_details (student_id, first_name, last_name, email, study_level, admitted_on)
    SELECT student_id, first_name, last_name, email, study_level, admitted_on
    FROM uslp.students
    WHERE num_nonnulls(first_name, last_name, email, study_level, admitted_on) > 0;

    -- Keep the name already displayed for older students with split names only.
    UPDATE uslp.students SET full_name = concat_ws(' ', first_name, last_name)
    WHERE full_name IS NULL;

    CREATE OR REPLACE VIEW uslp.v_student_directory AS
    SELECT s.student_id, s.student_number, x.first_name, x.last_name, x.email,
           x.study_level, s.status, p.programme_code, p.programme_name,
           d.department_code, d.department_name, s.full_name::text AS full_name, s.gender
    FROM uslp.students s
    JOIN uslp.programmes p ON p.programme_id = s.programme_id
    LEFT JOIN uslp.departments d ON d.department_id = p.department_id
    LEFT JOIN uslp.student_profile_details x ON x.student_id = s.student_id;

    CREATE OR REPLACE VIEW uslp.v_enrollment_details AS
    SELECT e.enrollment_id, e.student_id, s.student_number, s.full_name::text AS student_name,
           o.offering_id, c.course_code, c.course_title,
           a.session_name, t.semester_name, e.enrolled_on, e.status
    FROM uslp.enrollments e
    JOIN uslp.students s ON s.student_id = e.student_id
    JOIN uslp.course_offerings o ON o.offering_id = e.offering_id
    JOIN uslp.courses c ON c.course_id = o.course_id
    JOIN uslp.semesters t ON t.semester_id = o.semester_id
    JOIN uslp.academic_sessions a ON a.academic_session_id = t.academic_session_id;

    CREATE OR REPLACE VIEW uslp.v_class_list AS
    SELECT l.class_list_id, e.source_row, s.student_number, s.full_name::text AS full_name,
           s.gender, e.source_code, l.class_label, l.semester_label,
           p.programme_name, l.source_filename, l.source_sha256
    FROM uslp.class_list_entries e
    JOIN uslp.class_lists l ON l.class_list_id = e.class_list_id
    JOIN uslp.students s ON s.student_id = e.student_id
    JOIN uslp.programmes p ON p.programme_id = l.programme_id;

    ALTER TABLE uslp.students
        DROP CONSTRAINT students_name_available,
        DROP COLUMN first_name, DROP COLUMN last_name, DROP COLUMN email,
        DROP COLUMN study_level, DROP COLUMN admitted_on, DROP COLUMN user_id,
        ADD CONSTRAINT students_name_available CHECK (full_name IS NOT NULL);

    -- Readers of the original roster could already read student_id and user_id.
    -- Carry across table-level read access to support already configured portal services.
    FOR reader IN
        SELECT DISTINCT a.grantee FROM pg_class t CROSS JOIN LATERAL aclexplode(t.relacl) a
        WHERE t.oid = 'uslp.students'::regclass AND a.privilege_type = 'SELECT'
          AND a.grantee <> t.relowner
    LOOP
        EXECUTE 'GRANT SELECT ON uslp.student_accounts TO ' ||
            CASE WHEN reader.grantee = 0 THEN 'PUBLIC'
                 ELSE quote_ident(pg_get_userbyid(reader.grantee)) END;
    END LOOP;

    CREATE TRIGGER audit_student_accounts AFTER INSERT OR UPDATE OR DELETE ON uslp.student_accounts
        FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('student_id');
    CREATE TRIGGER audit_student_profile_details AFTER INSERT OR UPDATE OR DELETE ON uslp.student_profile_details
        FOR EACH ROW EXECUTE FUNCTION uslp.audit_change('student_id');
END;
$roster$;
