import psycopg2
import csv
from datetime import datetime

# Database connection parameters
db_params = {
    'host': "localhost",
    'user': 'postgres',
    'password': 'anders2001'
}

# Connect to the default 'postgres' database to check for the existence of the 'netflix_fave' database
conn = psycopg2.connect(**db_params, database='postgres')
conn.autocommit = True  # Enable autocommit mode for database creation
cur = conn.cursor()

# Check if the 'netflix_fave' database exists
cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'netflix_fave'")
exists = cur.fetchone()

# If the database does not exist, create it
if not exists:
    cur.execute('CREATE DATABASE netflix_fave')

cur.close()
conn.close()

# Now connect to the newly created or existing 'netflix_fave' database
conn = psycopg2.connect(**db_params, database='netflix_fave')
cur = conn.cursor()

# Drop and create tables
cur.execute('DROP TABLE IF EXISTS favorite CASCADE;')
cur.execute('DROP TABLE IF EXISTS movies_and_shows CASCADE;')
cur.execute('DROP TABLE IF EXISTS "user" CASCADE;')

cur.execute('''
    CREATE TABLE movies_and_shows (
        show_id SERIAL PRIMARY KEY,
        type VARCHAR(50),
        title VARCHAR(150),
        director VARCHAR(150),
        "cast" VARCHAR(500),
        country VARCHAR(5000),
        date_added DATE,
        release_year INTEGER,
        rating VARCHAR(10),
        duration VARCHAR(50),
        listed_in VARCHAR(150),
        description TEXT
    );
''')

cur.execute('''
    CREATE TABLE "user" (
        user_id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(500) NOT NULL UNIQUE
    );
''')

cur.execute('''
    CREATE TABLE favorite (
        fave_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        show_id INTEGER NOT NULL,
        date DATE,
        FOREIGN KEY (user_id) REFERENCES "user" (user_id) ON DELETE CASCADE,
        FOREIGN KEY (show_id) REFERENCES movies_and_shows (show_id) ON DELETE CASCADE
    );
''')

# Function to parse date
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%B %d, %Y').date()
    except ValueError:
        return None

# Insert data into tables (assuming your CSV data matches the schema)
with open('netflix2.csv', 'r', encoding="UTF-8") as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header row.
    for row in reader:
        date_added = parse_date(row[5])  # Assuming the date_added column is the 6th column in the CSV
        release_year = int(row[6]) if row[6].isdigit() else None  # Ensure release_year is an integer
        rating = row[7] if row[7] else None  # Ensure rating is a string or None
        duration = row[8] if row[8] else None  # Ensure duration is a string or None

        cur.execute('''
            INSERT INTO movies_and_shows (type, title, director, "cast", country, date_added, release_year, rating, duration, listed_in, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (row[0], row[1], row[2], row[3], row[4], date_added, release_year, rating, duration, row[9], row[10]))

conn.commit()

cur.close()
conn.close()
