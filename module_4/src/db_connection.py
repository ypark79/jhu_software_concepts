import os
import psycopg

# Establish and return a connection to PostgreSQL.
# Uses environment variables so tests can point to a test DB.
def get_connection():
    # Use environment variables so tests can point to a the test database.
    database_name = os.getenv("PGDATABASE", "module_3")
    host = os.getenv("PGHOST", "localhost")
    user = os.getenv("PGUSER", None)
    password = os.getenv("PGPASSWORD", None)
    port = int(os.getenv("PGPORT", "5432"))

    try:
        # Create a connection to the local PostgreSQL server
        conn = psycopg.connect(
            dbname=database_name,
            host=host,
            user=user,
            password=password,
            port=port
        )
        return conn
    except Exception as e:
        print(f"Error: Unable to connect to the database '{database_name}'.")
        print(f"Details: {e}")
        return None
