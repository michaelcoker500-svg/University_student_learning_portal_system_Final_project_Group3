"""Identify the class-list source that came with the Group Three project."""
ROSTER_SHA256 = "8758ae783094e42e3f2e946aff31d1133337ba8781137ddc93f66f78a3ee858a"


def roster_size(conn):
    row = conn.execute(
        "SELECT count(e.student_id) FROM uslp.class_lists l "
        "LEFT JOIN uslp.class_list_entries e USING (class_list_id) "
        "WHERE l.source_sha256=%s GROUP BY l.class_list_id",
        (ROSTER_SHA256,),
    ).fetchone()
    if row is None:
        raise ValueError("This database does not contain the supplied BSEM 1101 / Semester 3 class list. "
                         "Select the database with your original 45 students, or restore the original "
                         "class-list import on a fresh database before setup.")
    return row[0]
