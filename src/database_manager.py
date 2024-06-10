import sqlite3


class DatabaseManager:
    DATABASE_PATH = 'emotions.db'

    def __init__(self):
        self.conn = self.initialize_database()
        self.cursor = self.conn.cursor()
        self.setup_database()

    def initialize_database(self):
        """Initializes the SQLite database connection."""
        try:
            conn = sqlite3.connect(self.DATABASE_PATH)
            return conn
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            exit()

    def setup_database(self):
        """Sets up the emotions table in the database."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotions (
                    id INTEGER PRIMARY KEY,
                    emotion TEXT,
                    age TEXT,
                    gender TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database setup error: {e}")
            exit()

    def add_emotion(self, emotion, age, gender):
        """Inserts emotion data into the database."""
        try:
            self.cursor.execute(
                'INSERT INTO emotions (emotion, age, gender) VALUES (?, ?, ?)',
                (emotion, age, gender)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error inserting data into database: {e}")

    def close(self):
        """Closes the database connection."""
        self.conn.close()
