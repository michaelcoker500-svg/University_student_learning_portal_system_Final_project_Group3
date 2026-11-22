-- Apply to the existing University Student Learning Portal database.
-- setup_portal.py applies this file inside a transaction. It is safe to run again.
ALTER TABLE uslp.users ADD COLUMN IF NOT EXISTS display_name VARCHAR(160)
    CHECK (btrim(display_name) <> '');
ALTER TABLE uslp.courses ADD COLUMN IF NOT EXISTS total_lessons INTEGER
    CHECK (total_lessons BETWEEN 1 AND 10000);
ALTER TABLE uslp.enrollments ADD COLUMN IF NOT EXISTS lessons_completed INTEGER
    NOT NULL DEFAULT 0 CHECK (lessons_completed >= 0);

-- Existing courses have an unknown lesson total until staff enter the actual value.
-- The service keeps the student's and lecturer's views scoped to their linked profiles.
INSERT INTO uslp.permissions (permission_code, description) VALUES
    ('students.view_own','View only the linked student profile'),
    ('courses.view_own','View courses in the linked student’s enrolments'),
    ('enrollments.view_own','View only the linked student’s enrolments'),
    ('lessons.record','Record completed lessons in an authorised offering'),
    ('students.delete','Delete an unreferenced student'),
    ('enrollments.delete','Delete an enrollment that has no attendance history')
ON CONFLICT (permission_code) DO NOTHING;

INSERT INTO uslp.role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id FROM uslp.roles r CROSS JOIN uslp.permissions p
WHERE (r.role_name = 'Student' AND p.permission_code IN
          ('students.view_own','courses.view_own','enrollments.view_own'))
   OR (r.role_name IN ('Administrator','Super Administrator','Registrar','Lecturer')
       AND p.permission_code = 'lessons.record')
   OR (r.role_name IN ('Administrator','Super Administrator')
       AND p.permission_code IN ('students.delete','enrollments.delete'))
ON CONFLICT DO NOTHING;
