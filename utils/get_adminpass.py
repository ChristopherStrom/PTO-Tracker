import sqlite3
import sys

def get_admin_password(db_path):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query to find the admin user
        cursor.execute("SELECT username, password FROM user WHERE role = 'admin'")
        admin = cursor.fetchone()

        # Check if an admin user is found
        if admin:
            username, password = admin
            print(f"Admin username: {username}")
            print(f"Admin password: {password}")
        else:
            print("No admin user found.")

        # Close the database connection
        conn.close()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_adminpass.py <path_to_db>")
    else:
        db_path = sys.argv[1]
        get_admin_password(db_path)
