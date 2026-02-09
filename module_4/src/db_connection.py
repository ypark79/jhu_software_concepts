import psycopg

# Establish and return a connection to the PostgreSQL database "module_3"
def get_connection():

    database_name = "module_3"

    try:
        # Create a connection to the local PostgreSQL server
        # psycopg.connect() is the standard method for opening a session
        conn = psycopg.connect(
            dbname=database_name,
            host="localhost"
        )
        return conn
    except Exception as e:
        # If the database server is not running or credentials are wrong,
        # this will print a helpful error instead of crashing the program.
        print(f"Error: Unable to connect to the database "
              f"'{database_name}'.")
        print(f"Details: {e}")
        return None
