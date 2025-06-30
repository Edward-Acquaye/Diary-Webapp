import sqlite3

def initialize_database():
    try:
        # Connect to the database file
        conn = sqlite3.connect('users.db')
        print("Connected to database successfully.")

        # Read and execute schema.sql
        with open('schema.sql', 'r') as f:
            schema = f.read()

        conn.executescript(schema)
        conn.commit()
        print("Database schema applied successfully.")

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == '__main__':
    initialize_database()
