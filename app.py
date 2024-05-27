from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import nltk
from nltk import CFG
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey12345'

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        dbname='netflix_fave',  # Ensure this matches your database name
        user='postgres',        # Ensure this matches your username
        password='anders2001',  # Ensure this matches your password
        host='localhost'
    )
    return conn

# Define the CFG rules
cfg_rules = """
S -> Greeting Intro
Greeting -> 'Hi!' | 'Hello!' | 'Hey!'
Intro -> 'Welcome to FlixFinder!'
"""

# Parse the CFG
cfg = CFG.fromstring(cfg_rules)

def generate_sentence(grammar):
    productions = grammar.productions(lhs=grammar.start())
    sentence = []

    def expand(production):
        for symbol in production.rhs():
            if isinstance(symbol, nltk.grammar.Nonterminal):
                expand(random.choice(grammar.productions(lhs=symbol)))
            else:
                sentence.append(symbol)

    expand(random.choice(productions))
    return ' '.join(sentence)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM "user" WHERE username = %s;', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO "user" (username, password, email) VALUES (%s, %s, %s)',
                    (username, hashed_password, email))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/home')
def home():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT username FROM "user" WHERE user_id = %s;', (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            username = user[0]
            greeting_message = generate_sentence(cfg)  # Generate the greeting message
            return render_template('home.html', username=username, greeting_message=greeting_message)
    return redirect(url_for('login'))

@app.route('/favorites', methods=['GET', 'POST'])
def favorites():
    if 'user_id' not in session:
        flash('Please log in to view this page', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        show_id = request.form['show_id']
        date = request.form['date']
        cur.execute('INSERT INTO favorite (user_id, show_id, date) VALUES (%s, %s, %s)',
                    (user_id, show_id, date))
        conn.commit()

    cur.execute('''
        SELECT movies_and_shows.title, favorite.date, movies_and_shows.type, movies_and_shows.director
        FROM favorite 
        JOIN movies_and_shows ON favorite.show_id = movies_and_shows.show_id 
        WHERE favorite.user_id = %s;
    ''', (user_id,))
    favorite_shows = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('favorites.html', favorite_shows=favorite_shows)



@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return render_template('search.html')

    elif request.method == 'POST':
        title = request.form.get('title')
        director = request.form.get('director')
        cast = request.form.get('cast')
        country = request.form.get('country')
        release_year = request.form.get('release_year')
        rating = request.form.get('rating')
        duration = request.form.get('duration')
        listed_in = request.form.get('listed_in')

        conn = get_db_connection()
        cur = conn.cursor()

        query = 'SELECT * FROM movies_and_shows WHERE 1=1'
        params = []

        if title:
            query += ' AND title ILIKE %s'
            params.append(f'%{title}%')
        if director:
            query += ' AND director ILIKE %s'
            params.append(f'%{director}%')
        if cast:
            query += ' AND cast ILIKE %s'
            params.append(f'%{cast}%')
        if country:
            query += ' AND country ILIKE %s'
            params.append(f'%{country}%')
        if release_year:
            query += ' AND release_year = %s'
            params.append(release_year)
        if rating:
            query += ' AND rating ILIKE %s'
            params.append(f'%{rating}%')
        if duration:
            query += ' AND duration ILIKE %s'
            params.append(f'%{duration}%')
        if listed_in:
            query += ' AND listed_in ILIKE %s'
            params.append(f'%{listed_in}%')

        # Log the query and parameters
        logging.debug("Constructed Query: %s", query)
        logging.debug("Query Parameters: %s", params)
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        # Log the query results
        logging.debug("Query Results: %s", results)
        
        cur.close()
        conn.close()

        return render_template('search_results.html', results=results)

@app.route('/add_favorites', methods=['POST'])
def add_favorites():
    if 'user_id' not in session:
        flash('Please log in to add favorites', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    show_ids = request.form.getlist('favorites')

    conn = get_db_connection()
    cur = conn.cursor()

    for show_id in show_ids:
        cur.execute('INSERT INTO favorite (user_id, show_id, date) VALUES (%s, %s, current_date)', 
                    (user_id, show_id))

    conn.commit()
    cur.close()
    conn.close()

    flash('Favorites added successfully!', 'success')
    return redirect(url_for('favorites'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
