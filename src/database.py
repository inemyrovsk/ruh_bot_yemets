import sqlite3


def initialize_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create table for Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            phone_number TEXT NOT NULL,
            name TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # Create table for Events
    c.execute('''
        CREATE TABLE IF NOT EXISTS Events (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            image TEXT,
            date TEXT,
            time TEXT,
            location TEXT,
            price FLOAT
        )
    ''')

    # Create table for Publications
    c.execute('''
        CREATE TABLE IF NOT EXISTS Publications (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            image BLOB,
            scheduled_time TEXT,
            is_for_everyone INTEGER DEFAULT 1,
            group_id INTEGER,
            FOREIGN KEY(group_id) REFERENCES Groups(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS EventParticipants (
            user_name TEXT,
            user_id INTEGER,
            event_id TEXT,
            PRIMARY KEY(user_id, event_id),
            FOREIGN KEY(user_id) REFERENCES Users(id),
            FOREIGN KEY(event_id) REFERENCES Events(id)
        )
    ''')

    # Create table for Groups
    c.execute('''
        CREATE TABLE IF NOT EXISTS Groups (
            id INTEGER PRIMARY KEY,
            event_id INTEGER,
            FOREIGN KEY(event_id) REFERENCES Events(id)
        )
    ''')

    # Create table for GroupMembers (to handle many-to-many relationship between Users and Groups)
    c.execute('''
        CREATE TABLE IF NOT EXISTS GroupMembers (
            user_id INTEGER,
            group_id INTEGER,
            PRIMARY KEY(user_id, group_id),
            FOREIGN KEY(user_id) REFERENCES Users(id),
            FOREIGN KEY(group_id) REFERENCES Groups(id)
        )
    ''')

    # Create table for SupportMessages
    c.execute('''
        CREATE TABLE IF NOT EXISTS SupportMessages (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            message TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
    ''')

    conn.commit()
    conn.close()


def check_user_registered(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('SELECT * FROM Users WHERE id=?', (user_id,))
    user = c.fetchone()

    conn.close()

    return user is not None


def add_user(user_id, phone_number, name):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('INSERT INTO Users (id, phone_number, name) VALUES (?, ?, ?)', (user_id, phone_number, name))

    conn.commit()
    conn.close()


def add_user_to_event(user_id, event_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('INSERT INTO GroupMembers (user_id, group_id) VALUES (?, ?)', (user_id, event_id))

    conn.commit()
    conn.close()


def add_event(event_id, event_text, event_image_path, event_time, event_location, event_price):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    event_id = str(event_id)
    event_text = str(event_text)
    event_image_path = str(event_image_path)
    event_time = str(event_time)
    event_location = str(event_location)
    event_price = float(event_price)

    c.execute('INSERT INTO Events (id, name, image, date, time, location, price) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (event_id, event_text, event_image_path, event_time, event_time, event_location, event_price))

    conn.commit()
    conn.close()


def change_event(event_id, new_event_text, new_event_image):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('UPDATE Events SET name = ?, image = ? WHERE id = ?', (new_event_text, new_event_image, event_id))

    conn.commit()
    conn.close()


def delete_event(event_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('DELETE FROM Events WHERE id = ?', (event_id,))

    conn.commit()
    conn.close()


def register_user_to_event(user_id, event_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Check if the user is already registered for the event
    c.execute("SELECT * FROM EventParticipants WHERE user_id = ? AND event_id = ?", (user_id, event_id))
    if c.fetchone() is not None:
        conn.close()
        return False  # User is already registered

    # Register the user for the event
    c.execute("INSERT INTO EventParticipants (user_id, event_id) VALUES (?, ?)", (user_id, event_id))
    conn.commit()
    conn.close()
    print(f"Registering user {user_id} to event {event_id}")
    return True  # User was successfully registered

def fetch_users_by_event_id(event_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Execute the SELECT query with a JOIN to get the name and phone_number from the users table
    c.execute("""
        SELECT EventParticipants.user_id, Users.name, Users.phone_number 
        FROM EventParticipants 
        JOIN Users ON EventParticipants.user_id = Users.id 
        WHERE EventParticipants.event_id=?
    """, (event_id,))

    # Fetch all rows as a list of tuples
    rows = c.fetchall()

    # Close the database connection
    conn.close()

    # Convert the list of tuples to a list of dictionaries
    users = [{"user_id": row[0], "name": row[1], "phone_number": row[2]} for row in rows]

    return users