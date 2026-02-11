import pytest
import db_connection

@pytest.mark.db
# This test checks get_connection returns None on connection error.
def test_get_connection_failure(monkeypatch):
    
    def boom(**kwargs):
        raise Exception("fail")

    monkeypatch.setattr(db_connection.psycopg, "connect", boom)
    conn = db_connection.get_connection()
    assert conn is None