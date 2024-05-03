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
            location TEXT
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


def add_event(event_id, event_text, event_image_path, event_time, event_location):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    event_id = str(event_id)
    event_text = str(event_text)
    event_image_path = str(event_image_path)
    event_time = str(event_time)
    event_location = str(event_location)

    c.execute('INSERT INTO Events (id, name, image, date, time, location) VALUES (?, ?, ?, ?, ?, ?)',
              (event_id, event_text, event_image_path, event_time, event_time, event_location))

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
    # Database logic to add user to the event
    # Assuming a function that takes user_id and event_id and adds to the event registration table
    print(f"Registering user {user_id} to event {event_id}")
