from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
from database import init_db

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

init_db()

app = Flask(__name__)
app.secret_key = "virinchi_2k26_secret_key"

DB_NAME = "campus.db"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    return render_template('index.html', username=session.get('username'))


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/events')
def events_page():
    return render_template('events.html')


@app.route('/event/<int:event_id>')
def event_details(event_id):
    conn = get_db_connection()
    event = conn.execute(
        'SELECT * FROM events WHERE event_id = ?',
        (event_id,)
    ).fetchone()
    conn.close()

    if event is None:
        return "Event not found", 404

    return render_template('event_details.html', event=event)


@app.route('/my-events')
def my_events_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('my_events.html')


@app.route('/recommendations')
def recommendations_page():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    user = conn.execute(
        'SELECT skills FROM users WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()

    skills = [s.strip() for s in user['skills'].split(',')] if user and user['skills'] else []
    return render_template('recommendations.html', student_skills=skills)


@app.route('/dashboard')
def dashboard_view():
    if session.get('role') not in ['admin', 'organizer']:
        return redirect('/login')

    return render_template(
        'dashboard.html',
        session_username=session.get('username'),
        session_role=session.get('role')
    )


@app.route('/api/auth/register', methods=['POST'])
def handle_register():
    username = request.form.get('username')
    password = request.form.get('password')
    department = request.form.get('department')
    skills = request.form.get('skills')

    if not username or not password or not skills:
        return "Please fill all required fields.", 400

    conn = get_db_connection()

    try:
        conn.execute('''
            INSERT INTO users (username, password, role, department, skills)
            VALUES (?, ?, 'student', ?, ?)
        ''', (username, password, department, skills))
        conn.commit()

    except sqlite3.IntegrityError:
        return "Username already exists.", 400

    finally:
        conn.close()

    return redirect('/login')


@app.route('/api/auth/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?',
        (username, password)
    ).fetchone()
    conn.close()

    if user:
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['role'] = user['role']

        if user['role'] in ['admin', 'organizer']:
            return redirect('/dashboard')
        return redirect('/')

    return "Invalid username or password.", 401


@app.route('/api/auth/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/api/events-data', methods=['GET'])
def get_all_events():
    conn = get_db_connection()
    events = conn.execute(
        'SELECT * FROM events ORDER BY event_id DESC'
    ).fetchall()
    conn.close()

    return jsonify([dict(row) for row in events])


@app.route('/api/student/recommendations', methods=['GET'])
def get_recommendations():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()

    user = conn.execute('''
        SELECT department, skills
        FROM users
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()

    events = conn.execute('SELECT * FROM events').fetchall()
    conn.close()

    if not user or not events:
        return jsonify([])

    student_profile = f"{user['department'] or ''} {user['skills'] or ''}"

    event_texts = []
    event_list = []

    for event in events:
        event_dict = dict(event)

        text = f"""
        {event_dict.get('title', '')}
        {event_dict.get('category', '')}
        {event_dict.get('sub_category', '')}
        {event_dict.get('description', '')}
        {event_dict.get('tags', '')}
        """

        event_texts.append(text)
        event_list.append(event_dict)

    documents = [student_profile] + event_texts

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity_scores = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:]
    ).flatten()

    recommendations = []

    for index, score in enumerate(similarity_scores):
        event = event_list[index]
        event['match_score'] = round(float(score) * 100, 2)
        recommendations.append(event)

    recommendations = sorted(
        recommendations,
        key=lambda x: x['match_score'],
        reverse=True
    )

    return jsonify(recommendations[:6])


@app.route('/api/admin/add-event', methods=['POST'])
def api_add_event():
    if session.get('role') not in ['admin', 'organizer']:
        return "Unauthorized", 403

    title = request.form.get('title')
    category = request.form.get('category')
    sub_category = request.form.get('sub_category')
    description = request.form.get('description')
    tags = request.form.get('tags')
    venue = request.form.get('venue')
    date = request.form.get('date') or '16-18 March 2026'

    image_file = request.files.get('image')
    image_url = ""

    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)
        image_url = "/" + image_path.replace("\\", "/")

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO events
        (title, category, sub_category, description, tags, date, venue, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, category, sub_category, description, tags, date, venue, image_url))

    conn.commit()
    conn.close()

    return redirect('/dashboard')


@app.route('/api/admin/edit-event/<int:event_id>', methods=['POST'])
def edit_event(event_id):
    if session.get('role') not in ['admin', 'organizer']:
        return "Unauthorized", 403

    title = request.form.get('title')
    category = request.form.get('category')
    sub_category = request.form.get('sub_category')
    description = request.form.get('description')
    tags = request.form.get('tags')
    venue = request.form.get('venue')
    date = request.form.get('date')

    conn = get_db_connection()

    old_event = conn.execute(
        'SELECT image_url FROM events WHERE event_id = ?',
        (event_id,)
    ).fetchone()

    image_url = old_event['image_url'] if old_event else ""

    image_file = request.files.get('image')

    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)
        image_url = "/" + image_path.replace("\\", "/")

    conn.execute('''
        UPDATE events
        SET title = ?,
            category = ?,
            sub_category = ?,
            description = ?,
            tags = ?,
            date = ?,
            venue = ?,
            image_url = ?
        WHERE event_id = ?
    ''', (
        title,
        category,
        sub_category,
        description,
        tags,
        date,
        venue,
        image_url,
        event_id
    ))

    conn.commit()
    conn.close()

    return "Event updated successfully.", 200


@app.route('/api/admin/delete-event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if session.get('role') not in ['admin', 'organizer']:
        return "Unauthorized", 403

    conn = get_db_connection()
    conn.execute('DELETE FROM registrations WHERE event_id = ?', (event_id,))
    conn.execute('DELETE FROM events WHERE event_id = ?', (event_id,))
    conn.commit()
    conn.close()

    return "Event deleted successfully.", 200


@app.route('/api/student/register-event', methods=['POST'])
def register_event():
    if session.get('role') != 'student':
        return "Only students can register for events.", 403

    event_id = request.form.get('event_id')

    if not event_id:
        return "Event ID missing.", 400

    conn = get_db_connection()

    try:
        conn.execute('''
            INSERT INTO registrations (user_id, event_id)
            VALUES (?, ?)
        ''', (session['user_id'], event_id))
        conn.commit()
        return "Registration successful!", 200

    except sqlite3.IntegrityError:
        return "You are already registered for this event.", 400

    finally:
        conn.close()


@app.route('/api/student/my-events', methods=['GET'])
def get_my_events():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    events = conn.execute('''
        SELECT e.event_id, e.title, e.category, e.sub_category,
               e.description, e.venue, e.date, e.image_url
        FROM events e
        JOIN registrations r ON e.event_id = r.event_id
        WHERE r.user_id = ?
        ORDER BY e.date
    ''', (user_id,)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in events])


@app.route('/api/student/cancel-registration/<int:event_id>', methods=['POST'])
def cancel_registration(event_id):
    if session.get('role') != 'student':
        return "Only students can cancel registration.", 403

    conn = get_db_connection()
    conn.execute('''
        DELETE FROM registrations
        WHERE user_id = ? AND event_id = ?
    ''', (session['user_id'], event_id))

    conn.commit()
    conn.close()

    return "Registration cancelled successfully.", 200


@app.route('/api/admin/analytics', methods=['GET'])
def get_analytics():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    conn = get_db_connection()

    event_stats = conn.execute('''
        SELECT e.title, COUNT(r.user_id) AS reg_count
        FROM events e
        LEFT JOIN registrations r ON e.event_id = r.event_id
        GROUP BY e.event_id
        ORDER BY reg_count DESC
    ''').fetchall()

    total_events = conn.execute('SELECT COUNT(*) AS count FROM events').fetchone()
    total_students = conn.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'student'").fetchone()
    total_registrations = conn.execute('SELECT COUNT(*) AS count FROM registrations').fetchone()

    conn.close()

    return jsonify({
        "event_stats": [dict(row) for row in event_stats],
        "total_events": total_events['count'],
        "total_students": total_students['count'],
        "total_registrations": total_registrations['count']
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)