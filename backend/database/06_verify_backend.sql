-- OPTIONAL backend feature tests. All fictional data is rolled back.
-- Run in a quiet development copy after setup_portal has applied 07 and 08 (22 tables).
-- Identity sequence gaps may remain after rollback; no table rows remain changed.
BEGIN;
CREATE FUNCTION pg_temp.database_snapshot() RETURNS JSONB LANGUAGE plpgsql AS $$
DECLARE t RECORD; digest TEXT; result JSONB := '{}'::jsonb;
BEGIN
    FOR t IN SELECT table_name FROM information_schema.tables WHERE table_schema = 'uslp' AND table_type = 'BASE TABLE' ORDER BY table_name LOOP
        EXECUTE format('SELECT md5(coalesce(jsonb_agg(to_jsonb(x) ORDER BY to_jsonb(x)::text)::text, ''[]'')) FROM uslp.%I x', t.table_name) INTO digest;
        result := result || jsonb_build_object(t.table_name, digest);
    END LOOP;
    RETURN result;
END;
$$;
CREATE TEMP TABLE verify_baseline AS SELECT pg_temp.database_snapshot() AS snapshot;
COMMIT;
BEGIN;


CREATE FUNCTION pg_temp.assert_true(p_condition BOOLEAN, p_label TEXT) RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
    IF p_condition IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'FAIL: %', p_label;
    END IF;
    RAISE NOTICE 'PASS: %', p_label;
END;
$$;

CREATE FUNCTION pg_temp.expect_error(p_statement TEXT, p_sqlstate TEXT, p_label TEXT) RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE observed_state TEXT;
BEGIN
    BEGIN
        EXECUTE p_statement;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS observed_state = RETURNED_SQLSTATE;
        -- Older PostgreSQL releases report a RESTRICT action as a foreign-key violation.
        IF observed_state <> p_sqlstate AND NOT (p_sqlstate = '23001' AND observed_state = '23503') THEN
            RAISE EXCEPTION 'FAIL: %; expected SQLSTATE %, received %', p_label, p_sqlstate, observed_state;
        END IF;
        RAISE NOTICE 'PASS: %', p_label;
        RETURN;
    END;
    RAISE EXCEPTION 'FAIL: %; statement incorrectly succeeded', p_label;
END;
$$;


-- Fixture creation below uses fictional people and V-/VERIFY codes only.
INSERT INTO uslp.users(username) VALUES ('verify_admin'), ('verify_lecturer_ict'), ('verify_lecturer_business');
SELECT set_config('uslp.actor_user_id', user_id::text, TRUE) FROM uslp.users WHERE username = 'verify_admin';

INSERT INTO uslp.departments(department_code, department_name) VALUES
('VERIFY-ICT', 'Information and Communication Technology'),
('VERIFY-BUS', 'Business and Management');

INSERT INTO uslp.programmes(department_id, programme_code, programme_name, duration_years)
SELECT d.department_id, v.code, v.name, v.years
FROM (VALUES
    ('VERIFY-ICT', 'VERIFY-BSE', 'BSc Software Engineering', 4),
    ('VERIFY-ICT', 'VERIFY-BIT', 'BSc Information Technology', 4),
    ('VERIFY-BUS', 'VERIFY-BBA', 'Bachelor of Business Administration', 4)
) AS v(dept, code, name, years)
JOIN uslp.departments d ON d.department_code = v.dept;

INSERT INTO uslp.lecturers(staff_number, user_id, department_id, first_name, last_name, email)
SELECT v.staff, u.user_id, d.department_id, v.first_name, v.last_name, v.email
FROM (VALUES
    ('VERIFY-STF-001', 'verify_lecturer_ict', 'VERIFY-ICT', 'Mariama', 'Koroma', 'mariama.koroma@example.invalid'),
    ('VERIFY-STF-002', 'verify_lecturer_business', 'VERIFY-BUS', 'Samuel', 'Conteh', 'samuel.conteh@example.invalid')
) AS v(staff, username, dept, first_name, last_name, email)
JOIN uslp.users u ON u.username = v.username
JOIN uslp.departments d ON d.department_code = v.dept;

INSERT INTO uslp.courses(department_id, course_code, course_title, credits)
SELECT d.department_id, v.code, v.title, v.credits
FROM (VALUES
    ('VERIFY-ICT', 'V-DCOMP114', 'Database Systems', 3),
    ('VERIFY-ICT', 'V-PROG211', 'Object-Oriented Programming 1', 3),
    ('VERIFY-ICT', 'V-WEB201', 'Web Development', 3),
    ('VERIFY-ICT', 'V-MATH201', 'Discrete Mathematics', 3),
    ('VERIFY-BUS', 'V-BUS201', 'Principles of Business', 3),
    ('VERIFY-BUS', 'V-MGT201', 'Introduction to Management', 3)
) AS v(dept, code, title, credits)
JOIN uslp.departments d ON d.department_code = v.dept;

INSERT INTO uslp.academic_sessions(session_name, starts_on, ends_on)
VALUES ('VERIFY-2026/2027', '2026-09-01', '2027-08-31');

INSERT INTO uslp.semesters(academic_session_id, semester_name, starts_on, ends_on)
SELECT a.academic_session_id, v.name, v.starts_on::date, v.ends_on::date
FROM (VALUES
    ('Verify Semester 3', '2026-09-01', '2027-02-28'),
    ('Verify Semester 4', '2027-03-01', '2027-08-31')
) AS v(name, starts_on, ends_on)
CROSS JOIN uslp.academic_sessions a WHERE a.session_name = 'VERIFY-2026/2027';

INSERT INTO uslp.course_offerings(course_id, semester_id)
SELECT c.course_id, s.semester_id FROM uslp.courses c CROSS JOIN uslp.semesters s
WHERE c.course_code LIKE 'V-%' AND (s.semester_name = 'Verify Semester 3' OR (s.semester_name = 'Verify Semester 4' AND c.course_code = 'V-DCOMP114'));

INSERT INTO uslp.teaching_assignments(offering_id, lecturer_id)
SELECT o.offering_id, l.lecturer_id FROM uslp.course_offerings o
JOIN uslp.courses c ON c.course_id = o.course_id
JOIN uslp.lecturers l ON l.department_id = c.department_id WHERE c.course_code LIKE 'V-%';

INSERT INTO uslp.students(student_number, programme_id, full_name)
SELECT 'VERIFY2026' || lpad(v.n::text, 3, '0'), p.programme_id, concat_ws(' ', v.first_name, v.last_name)
FROM (VALUES
    (1, 'Aisha', 'Kamara', 'VERIFY-BSE'), (2, 'Ibrahim', 'Sesay', 'VERIFY-BSE'),
    (3, 'Hawa', 'Conteh', 'VERIFY-BSE'), (4, 'Musa', 'Bangura', 'VERIFY-BSE'),
    (5, 'Fatmata', 'Koroma', 'VERIFY-BSE'), (6, 'Abdul', 'Turay', 'VERIFY-BSE'),
    (7, 'Isata', 'Kargbo', 'VERIFY-BSE'), (8, 'Joseph', 'Sannoh', 'VERIFY-BSE'),
    (9, 'Zainab', 'Jalloh', 'VERIFY-BSE'), (10, 'Daniel', 'Mansaray', 'VERIFY-BSE'),
    (11, 'Adama', 'Fofanah', 'VERIFY-BSE'), (12, 'Mohamed', 'Kallon', 'VERIFY-BSE'),
    (13, 'Aminata', 'Sorie', 'VERIFY-BIT'), (14, 'David', 'Kanu', 'VERIFY-BIT'),
    (15, 'Kadiatu', 'Suma', 'VERIFY-BIT'), (16, 'Peter', 'Gbessay', 'VERIFY-BIT'),
    (17, 'Sia', 'Fofana', 'VERIFY-BBA'), (18, 'Osman', 'Sankoh', 'VERIFY-BBA'),
    (19, 'Esther', 'Dumbuya', 'VERIFY-BBA'), (20, 'Alie', 'Saidu', 'VERIFY-BBA')
) AS v(n, first_name, last_name, programme)
JOIN uslp.programmes p ON p.programme_code = v.programme;

INSERT INTO uslp.enrollments(student_id, offering_id, enrolled_on)
SELECT s.student_id, o.offering_id, '2026-09-15'
FROM uslp.students s JOIN uslp.programmes p ON p.programme_id = s.programme_id
JOIN uslp.courses c ON
    (p.programme_code = 'VERIFY-BSE' AND c.course_code IN ('V-DCOMP114', 'V-PROG211')) OR
    (p.programme_code = 'VERIFY-BIT' AND c.course_code IN ('V-DCOMP114', 'V-WEB201')) OR
    (p.programme_code = 'VERIFY-BBA' AND c.course_code IN ('V-BUS201', 'V-MGT201'))
JOIN uslp.course_offerings o ON o.course_id = c.course_id
JOIN uslp.semesters t ON t.semester_id = o.semester_id
WHERE t.semester_name = 'Verify Semester 3';

INSERT INTO uslp.class_sessions(offering_id, starts_at, ends_at, topic)
SELECT o.offering_id, v.starts_at::timestamptz, v.ends_at::timestamptz, v.topic
FROM uslp.course_offerings o JOIN uslp.semesters s ON s.semester_id = o.semester_id
CROSS JOIN (VALUES
    ('2026-11-02 09:00:00+00', '2026-11-02 11:00:00+00', 'Introduction and review'),
    ('2026-11-09 09:00:00+00', '2026-11-09 11:00:00+00', 'Practical class')
) AS v(starts_at, ends_at, topic)
WHERE s.semester_name = 'Verify Semester 3';

-- First class marked; the second class is deliberately still unmarked.
-- These dates are sample teaching events, not a completed timetable.
INSERT INTO uslp.attendance(enrollment_id, class_session_id, status, recorded_by)
SELECT e.enrollment_id, cs.class_session_id,
       CASE right(s.student_number, 1)
         WHEN '0' THEN 'absent' WHEN '5' THEN 'late' WHEN '9' THEN 'excused'
         ELSE 'present' END,
       u.user_id
FROM uslp.enrollments e JOIN uslp.students s ON s.student_id = e.student_id
JOIN uslp.class_sessions cs ON cs.offering_id = e.offering_id
JOIN uslp.users u ON u.username = 'verify_admin'
WHERE cs.starts_at = '2026-11-02 09:00:00+00' AND s.student_number LIKE 'VERIFY2026%';

DO $$
DECLARE sid BIGINT; sid2 BIGINT; db_offering BIGINT; web_offering BIGINT; later_offering BIGINT;
        eid BIGINT; eid2 BIGINT; class1 BIGINT; class2 BIGINT; other_class BIGINT;
        actor BIGINT; att_id BIGINT; programme BIGINT; new_enrollment BIGINT;
BEGIN
    PERFORM pg_temp.assert_true((SELECT count(*) = 22 FROM information_schema.tables
                                WHERE table_schema = 'uslp' AND table_type = 'BASE TABLE'), '22 application tables');
    PERFORM pg_temp.assert_true((SELECT count(*) = 5 FROM information_schema.views WHERE table_schema = 'uslp'), '5 reporting views');
    PERFORM pg_temp.assert_true((SELECT count(*) = 20 FROM uslp.students WHERE student_number LIKE 'VERIFY2026%'), '20 sample students');
    PERFORM pg_temp.assert_true((SELECT count(*) = 40 FROM uslp.enrollments e JOIN uslp.students s USING (student_id) WHERE s.student_number LIKE 'VERIFY2026%'), '40 sample enrollments');
    PERFORM pg_temp.assert_true((SELECT count(*) = 12 FROM uslp.class_sessions cs JOIN uslp.course_offerings o USING(offering_id) JOIN uslp.courses c USING(course_id) WHERE c.course_code LIKE 'V-%'), '12 sample classes');
    PERFORM pg_temp.assert_true((SELECT count(*) = 40 FROM uslp.attendance a JOIN uslp.enrollments e USING(enrollment_id) JOIN uslp.students s USING(student_id) WHERE s.student_number LIKE 'VERIFY2026%'), '40 sample attendance marks');
    PERFORM pg_temp.assert_true((SELECT bool_and(NOT is_active AND password_hash IS NULL) FROM uslp.users WHERE username LIKE 'verify_%'), 'sample accounts disabled');

    SELECT student_id, programme_id INTO sid, programme FROM uslp.students WHERE student_number = 'VERIFY2026001';
    SELECT student_id INTO sid2 FROM uslp.students WHERE student_number = 'VERIFY2026002';
    SELECT offering_id INTO db_offering FROM uslp.course_offerings o
        JOIN uslp.courses c USING (course_id) JOIN uslp.semesters s USING (semester_id)
        WHERE c.course_code = 'V-DCOMP114' AND s.semester_name = 'Verify Semester 3';
    SELECT offering_id INTO web_offering FROM uslp.course_offerings o
        JOIN uslp.courses c USING (course_id) JOIN uslp.semesters s USING (semester_id)
        WHERE c.course_code = 'V-WEB201' AND s.semester_name = 'Verify Semester 3';
    SELECT offering_id INTO later_offering FROM uslp.course_offerings o
        JOIN uslp.courses c USING (course_id) JOIN uslp.semesters s USING (semester_id)
        WHERE c.course_code = 'V-DCOMP114' AND s.semester_name = 'Verify Semester 4';
    SELECT enrollment_id INTO eid FROM uslp.enrollments WHERE student_id = sid AND offering_id = db_offering;
    SELECT enrollment_id INTO eid2 FROM uslp.enrollments WHERE student_id = sid2 AND offering_id = db_offering;
    SELECT class_session_id INTO class1 FROM uslp.class_sessions
        WHERE offering_id = db_offering AND starts_at = '2026-11-02 09:00+00';
    SELECT class_session_id INTO class2 FROM uslp.class_sessions
        WHERE offering_id = db_offering AND starts_at = '2026-11-09 09:00+00';
    SELECT min(class_session_id) INTO other_class FROM uslp.class_sessions WHERE offering_id = web_offering;
    SELECT user_id INTO actor FROM uslp.users WHERE username = 'verify_admin';
    SELECT attendance_id INTO att_id FROM uslp.attendance WHERE enrollment_id = eid AND class_session_id = class1;
    PERFORM set_config('uslp.actor_user_id', actor::text, TRUE);

    PERFORM pg_temp.expect_error(format('INSERT INTO uslp.students(student_number, programme_id, full_name) VALUES (''VERIFY2026001'', %s, ''Test Student'')', programme), '23505', 'duplicate student number rejected');
    PERFORM pg_temp.expect_error('INSERT INTO uslp.students(student_number, programme_id, full_name) VALUES (''BAD-FK'', -999, ''Test Student'')', '23503', 'missing programme rejected');
    PERFORM pg_temp.expect_error(format('UPDATE uslp.students SET full_name = '''' WHERE student_id = %s', sid), '23514', 'blank full name rejected');
    PERFORM pg_temp.expect_error(format('UPDATE uslp.students SET status = ''invalid'' WHERE student_id = %s', sid), '23514', 'unknown student status rejected');
    PERFORM pg_temp.expect_error('UPDATE uslp.courses SET credits = 0 WHERE course_code = ''V-DCOMP114''', '23514', 'nonpositive course credits rejected');
    PERFORM pg_temp.expect_error('UPDATE uslp.users SET is_active = TRUE WHERE username = ''verify_admin''', '23514', 'active account requires password hash');
    PERFORM pg_temp.expect_error('UPDATE uslp.users SET password_hash = ''plaintext'' WHERE username = ''verify_admin''', '23514', 'plain-text password storage rejected');
    PERFORM pg_temp.expect_error(format('SELECT uslp.enroll_student(%s, %s)', sid, db_offering), '23505', 'duplicate enrollment rejected');
    PERFORM pg_temp.expect_error(format('SELECT uslp.enroll_student(-999, %s)', db_offering), '23503', 'missing student rejected');
    PERFORM pg_temp.expect_error(format('SELECT uslp.enroll_student(%s, -999)', sid), '23503', 'missing course offering rejected');

    UPDATE uslp.students SET status = 'inactive' WHERE student_id = sid;
    PERFORM pg_temp.expect_error(format('SELECT uslp.enroll_student(%s, %s)', sid, web_offering), '23514', 'inactive student enrollment rejected');
    UPDATE uslp.students SET status = 'active' WHERE student_id = sid;
    UPDATE uslp.course_offerings SET enrollment_open = FALSE WHERE offering_id = web_offering;
    PERFORM pg_temp.expect_error(format('SELECT uslp.enroll_student(%s, %s)', sid, web_offering), '23514', 'closed offering enrollment rejected');
    UPDATE uslp.course_offerings SET enrollment_open = TRUE WHERE offering_id = web_offering;

    new_enrollment := uslp.enroll_student(sid, later_offering);
    PERFORM pg_temp.assert_true(new_enrollment IS NOT NULL, 'same course in another semester allowed');
    PERFORM pg_temp.assert_true((SELECT attendance_percentage IS NULL FROM uslp.v_attendance_summary WHERE enrollment_id = new_enrollment), 'no attendance returns NULL percentage');
    PERFORM pg_temp.assert_true((SELECT marked_classes = 1 AND attendance_percentage = 100.00 FROM uslp.v_attendance_summary WHERE enrollment_id = eid), 'unmarked classes are not counted as absence');

    CALL uslp.record_attendance(eid, class2, 'present', actor);
    PERFORM pg_temp.assert_true((SELECT count(*) = 2 FROM uslp.attendance WHERE enrollment_id = eid), 'attendance procedure records valid mark');
    PERFORM pg_temp.expect_error(format('CALL uslp.record_attendance(%s, %s, ''present'', %s)', eid, class2, actor), '23505', 'duplicate attendance rejected');
    PERFORM pg_temp.expect_error(format('CALL uslp.record_attendance(%s, %s, ''present'', %s)', eid, other_class, actor), '23514', 'attendance for a different course rejected');
    PERFORM pg_temp.expect_error(format('CALL uslp.record_attendance(-999, %s, ''present'', %s)', class2, actor), '23503', 'attendance without enrollment rejected');
    PERFORM pg_temp.expect_error(format('CALL uslp.record_attendance(%s, %s, ''holiday'', %s)', eid2, class2, actor), '23514', 'invalid attendance status rejected');
    UPDATE uslp.enrollments SET status = 'withdrawn' WHERE enrollment_id = eid2;
    PERFORM pg_temp.expect_error(format('CALL uslp.record_attendance(%s, %s, ''present'', %s)', eid2, class2, actor), '23514', 'new attendance for withdrawn enrollment rejected');
    UPDATE uslp.enrollments SET status = 'enrolled' WHERE enrollment_id = eid2;

    PERFORM pg_temp.expect_error(format('UPDATE uslp.attendance SET status = ''absent'' WHERE attendance_id = %s', att_id), '23514', 'attendance correction needs a reason');
    PERFORM pg_temp.expect_error(format('CALL uslp.correct_attendance(-999, ''late'', %s, ''test'')', actor), 'P0002', 'correction of missing record rejected');
    CALL uslp.correct_attendance(att_id, 'late', actor, 'Lecturer confirmed the arrival time');
    PERFORM pg_temp.assert_true((SELECT status = 'late' AND correction_reason <> '' FROM uslp.attendance WHERE attendance_id = att_id), 'valid attendance correction saved');
    PERFORM pg_temp.assert_true((SELECT actor_user_id = actor AND old_data ->> 'status' = 'present' AND new_data ->> 'status' = 'late'
        FROM uslp.audit_logs WHERE table_name = 'attendance' ORDER BY audit_id DESC LIMIT 1), 'audit captures actor and before/after values');

    PERFORM pg_temp.expect_error(format('DELETE FROM uslp.students WHERE student_id = %s', sid), '23001', 'student with enrollments cannot be deleted');
    PERFORM pg_temp.expect_error('DELETE FROM uslp.departments WHERE department_code = ''VERIFY-ICT''', '23001', 'referenced department cannot be deleted');
    PERFORM pg_temp.expect_error(format('UPDATE uslp.enrollments SET offering_id = %s WHERE enrollment_id = %s', web_offering, eid), '23514', 'enrollment history cannot be reassigned');
    PERFORM pg_temp.expect_error(format('UPDATE uslp.course_offerings SET semester_id = (SELECT semester_id FROM uslp.semesters WHERE semester_name = ''Verify Semester 4'') WHERE offering_id = %s', db_offering), '23514', 'offering history cannot be reassigned');
    PERFORM pg_temp.expect_error('UPDATE uslp.semesters SET starts_on = ''2026-08-01'' WHERE semester_name = ''Verify Semester 3''', '23514', 'semester outside academic session rejected');
    PERFORM pg_temp.expect_error('UPDATE uslp.academic_sessions SET starts_on = ''2026-10-01'' WHERE session_name = ''VERIFY-2026/2027''', '23514', 'parent date change cannot invalidate semesters');
    PERFORM pg_temp.expect_error(format('INSERT INTO uslp.class_sessions(offering_id, starts_at, ends_at, topic) VALUES (%s, ''2027-04-01 09:00+00'', ''2027-04-01 10:00+00'', ''Invalid date'')', db_offering), '23514', 'class outside semester rejected');
    PERFORM pg_temp.expect_error(format('UPDATE uslp.class_sessions SET starts_at = starts_at + interval ''1 hour'' WHERE class_session_id = %s', class1), '23514', 'class start protected after attendance exists');

    UPDATE uslp.users SET failed_login_attempts = 1 WHERE user_id = actor;
    PERFORM pg_temp.assert_true(NOT EXISTS (SELECT 1 FROM uslp.audit_logs
        WHERE table_name = 'users' AND (old_data ? 'password_hash' OR new_data ? 'password_hash')), 'password hashes excluded from audit payloads');

    BEGIN
        INSERT INTO uslp.departments(department_code, department_name) VALUES ('TX-FAIL', 'Transaction test');
        INSERT INTO uslp.programmes(department_id, programme_code, programme_name, duration_years)
        VALUES (-999, 'TX-PROGRAMME', 'Invalid parent', 4);
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
    PERFORM pg_temp.assert_true(NOT EXISTS (SELECT 1 FROM uslp.departments WHERE department_code = 'TX-FAIL'), 'failed multi-step operation rolls back the first insert');
    PERFORM pg_temp.assert_true(NOT EXISTS (SELECT 1 FROM uslp.audit_logs WHERE new_data ->> 'department_code' = 'TX-FAIL'), 'failed transaction rolls back its audit entry');
END;
$$;
ROLLBACK;
DO $$
BEGIN
    IF (SELECT snapshot FROM verify_baseline) IS DISTINCT FROM pg_temp.database_snapshot() THEN
        RAISE EXCEPTION 'FAIL: rollback changed stored table contents';
    END IF;
    RAISE NOTICE 'PASS: rollback restores all table contents, including real students and audit logs';
END;
$$;
DROP TABLE verify_baseline;
DROP FUNCTION pg_temp.database_snapshot();
