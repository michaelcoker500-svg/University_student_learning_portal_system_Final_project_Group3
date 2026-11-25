-- Provide the writable compatibility view used by the desktop service.
-- This exposes selected student columns without duplicating or moving data.
CREATE SCHEMA IF NOT EXISTS uslp_portal;

CREATE OR REPLACE VIEW uslp_portal.students AS
SELECT student_id, student_number, full_name, programme_id, status, updated_at
FROM uslp.students;
