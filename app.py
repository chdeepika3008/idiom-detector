from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import pandas as pd
import csv
import os
import re
import random

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# ==========================
# LOAD IDIOMS DATASET
# ==========================
df = pd.read_csv("data/idioms_dataset.csv")  # Make sure file exists

# Digital Library (store history per user)
library = []

# ==========================
# LOGIN REQUIRED DECORATOR
# ==========================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================
# PUBLIC PAGES
# ==========================
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

# ==========================
# LOGIN
# ==========================
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users = {}
        if os.path.exists("users.csv"):
            with open("users.csv", newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    users[row['username']] = row['password']

        if username in users and password == users[username]:
            session['user'] = username
            session.pop('idiom_of_the_day', None)  # reset idiom of the day
            return redirect(url_for('translate'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# ==========================
# REGISTER
# ==========================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        users = {}
        if os.path.exists("users.csv"):
            with open("users.csv", newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    users[row['username']] = row['password']

        if username in users:
            return render_template('register.html', error="Username already exists")

        with open("users.csv", "a", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['username','password'])
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow({'username': username, 'password': password})

        return redirect(url_for('login'))

    return render_template('register.html')

# ==========================
# LOGOUT
# ==========================
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('idiom_of_the_day', None)
    return redirect(url_for('home'))

# ==========================
# CLEAN TEXT
# ==========================
def clean_text(text):
    if text and isinstance(text, str):
        return text.lower().strip()
    return ""

# ==========================
# DETECT IDIOM
# ==========================
def detect_idiom(sentence):
    sentence_clean = clean_text(sentence)
    if not sentence_clean:
        return {"idiom": "No idiom found", "meaning": "", "telugu": ""}

    for _, row in df.iterrows():
        idiom_text = row['idiom']
        if isinstance(idiom_text, str):
            pattern = r'\b' + re.escape(idiom_text.lower()) + r'\b'
            if re.search(pattern, sentence_clean):
                return {
                    "idiom": row['idiom'],
                    "meaning": row.get('meaning', ''),
                    "telugu": row.get('telugu_translation', '')
                }
    return {"idiom": "No idiom found", "meaning": "", "telugu": ""}

# ==========================
# TRANSLATE PAGE
# ==========================
@app.route('/translate', methods=['GET','POST'])
@login_required
def translate():
    idiom = ""
    meaning = ""
    telugu = ""
    sentence = ""

    # Idiom of the Day
    if 'idiom_of_the_day' not in session and not df.empty:
        random_row = df.sample(n=1).iloc[0]
        session['idiom_of_the_day'] = random_row['idiom']
    idiom_of_the_day = session.get('idiom_of_the_day')

    if request.method == 'POST':
        sentence = request.form.get('sentence', '')
        result = detect_idiom(sentence)

        idiom = result['idiom']
        meaning = result['meaning']
        telugu = result['telugu']

        # Save in Digital Library
        library.append({
            "user": session['user'],
            "sentence": sentence,
            "idiom": idiom,
            "meaning": meaning,
            "telugu": telugu
        })

    return render_template(
        'translate.html',
        idiom=idiom,
        meaning=meaning,
        telugu=telugu,
        sentence=sentence,
        idiom_of_the_day=idiom_of_the_day
    )

# ==========================
# EXAMPLES PAGE
# ==========================
@app.route('/examples')
@login_required
def examples():
    data = df.head(10).to_dict(orient='records')
    return render_template('examples.html', idioms=data)

# ==========================
# HISTORY PAGE
# ==========================
@app.route('/history')
@login_required
def history():
    user_history = [entry for entry in library if entry['user'] == session['user']]
    return render_template('history.html', entries=user_history)

# ==========================
# DIGITAL LIBRARY
# ==========================
@app.route('/library')
@login_required
def library_page():
    recent_library = library[-50:]
    return render_template('library.html', entries=recent_library)

# ==========================
# CLEAR HISTORY
# ==========================
@app.route('/clear_history')
@login_required
def clear_history():
    global library
    library = [entry for entry in library if entry['user'] != session['user']]
    return redirect(url_for('history'))

# ==========================
# RUN APP
# ==========================
if __name__ == '__main__':
    app.run(debug=True)