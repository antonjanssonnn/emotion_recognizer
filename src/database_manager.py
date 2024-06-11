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

    def get_most_common_emotion(self, start_time, end_time):
        """Retrieves the most common emotion within a specified time range."""
        query = '''
            SELECT emotion, COUNT(emotion) as count
            FROM emotions
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY emotion
            ORDER BY count DESC
            LIMIT 1
        '''
        self.cursor.execute(query, (start_time, end_time))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_emotion_trends(self):
        """Retrieves the dominant emotions from morning to evening."""
        time_ranges = [
            ("Morning", "06:00:00", "12:00:00"),
            ("Afternoon", "12:00:01", "18:00:00"),
            ("Evening", "18:00:01", "23:59:59")
        ]
        trends = {}
        for period, start, end in time_ranges:
            query = f'''
                SELECT emotion, COUNT(emotion) as count
                FROM emotions
                WHERE time(timestamp) BETWEEN ? AND ?
                GROUP BY emotion
                ORDER BY count DESC
                LIMIT 1
            '''
            self.cursor.execute(query, (start, end))
            result = self.cursor.fetchone()
            trends[period] = result[0] if result else None
        return trends

    def get_happy_emotion_counts(self, start_time, end_time):
        """Retrieves counts of happy emotions within a specified time range."""
        query = '''
            SELECT datetime(timestamp), COUNT(emotion) as count
            FROM emotions
            WHERE emotion = 'happy' AND timestamp BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m-%d %H', timestamp)
        '''
        self.cursor.execute(query, (start_time, end_time))
        return self.cursor.fetchall()

    def get_happy_emotion_counts_for_week(self, start_date, end_date):
        """Retrieves counts of happy emotions within the workweek."""
        query = '''
            SELECT date(timestamp), strftime('%H', timestamp) as hour, COUNT(emotion) as count
            FROM emotions
            WHERE emotion = 'happy' AND date(timestamp) BETWEEN ? AND ?
            GROUP BY date(timestamp), hour
        '''
        self.cursor.execute(query, (start_date, end_date))
        return self.cursor.fetchall()

    def close(self):
        """Closes the database connection."""
        self.conn.close()
