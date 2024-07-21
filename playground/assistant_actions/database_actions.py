import sqlite3
import os

from playground.actions_manager import agent_action


@agent_action
def create_database(db_filename):
    """
    Create a SQLite database if it doesn't exist.

    Args:
    db_filename (str): The name of the database file

    Returns:
    The status message indicating whether the database was created or already exists.
    """
    # Check if the database file already exists
    db_exists = os.path.exists(db_filename)

    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect(db_filename)

    if not db_exists:
        return f"Database '{db_filename}' created successfully."
    else:
        return f"Connected to existing database '{db_filename}'."


@agent_action
def create_table(db_filename, table_name, columns):
    """
    Create a table in the SQLite database if it doesn't exist.

    Args:
    db_filename (str): The name of the database file
    table_name (str): The name of the table to create
    columns (dict): A dictionary where keys are column names and values are column types

    Returns:
    The status message indicating whether the table was created or already exists.
    """
    db_exists = os.path.exists(db_filename)

    if not db_exists:
        create_database(db_filename)

    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    # Check if the table already exists
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    if cursor.fetchone():
        return f"Table '{table_name}' already exists."

    # Construct the CREATE TABLE SQL statement
    columns_def = ", ".join([f"{name} {type}" for name, type in columns.items()])
    create_table_sql = f"CREATE TABLE {table_name} ({columns_def})"

    # Execute the CREATE TABLE SQL statement
    cursor.execute(create_table_sql)
    conn.commit()

    return f"Table '{table_name}' created successfully."


@agent_action
def insert_or_update_database_entry(db_filename, table_name, columns):
    """
    Insert or update an entry in the specified databasetable.

    Args:
    db_filename (str): The name of the database file
    table_name (str): The name of the table
    columns (dict): A dictionary where keys are column names and values are the data to insert/update

    Returns:
    The status message indicating whether the entry was inserted/updated successfully.
    """
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    # Check if the table exists
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    if not cursor.fetchone():
        print(f"Table '{table_name}' does not exist.")
        conn.close()
        return False

    # Prepare column names and placeholders for the SQL statement
    column_names = ", ".join(columns.keys())
    placeholders = ", ".join(["?" for _ in columns])
    values = tuple(columns.values())

    # Construct the INSERT OR REPLACE statement
    sql = (
        f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
    )

    try:
        cursor.execute(sql, values)
        conn.commit()
        return f"Entry inserted/updated successfully in table '{table_name}'."
    except sqlite3.Error as e:
        conn.rollback()
        return f"An error occurred: {e}"
    finally:
        conn.close()


@agent_action
def query_database(db_filename, sql_query, limit=None):
    """
    Execute a custom SQL query on the database and return the results.

    Args:
    db_filename (str): The name of the database file
    sql_query (str): The SQL query to execute
    limit (int, optional): The maximum number of results to return

    Returns:
    list: A list of tuples containing the query results
    """
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    try:
        if limit:
            sql_query = f"{sql_query} LIMIT {limit}"

        cursor.execute(sql_query)
        results = cursor.fetchall()

        print(f"Query executed successfully. {len(results)} results returned.")
        return results
    except sqlite3.Error as e:
        print(f"An error occurred while executing the query: {e}")
        return []
    finally:
        conn.close()
