import pytest
import psycopg

import db_connection

@pytest.mark.db
# This test checks get_connection returns None on connection error.
def test_get_connection_failure(monkeypatch):

    def boom(**kwargs):
        raise psycopg.OperationalError("fail")

    monkeypatch.setattr(db_connection.psycopg, "connect", boom)
    conn = db_connection.get_connection()
    assert conn is None


@pytest.mark.db
# This test covers get_connection success path (return conn).
def test_get_connection_success(monkeypatch):
    fake_conn = object()
    monkeypatch.setattr(db_connection.psycopg, "connect",
                        lambda **kwargs: fake_conn)
    conn = db_connection.get_connection()
    assert conn is fake_conn
