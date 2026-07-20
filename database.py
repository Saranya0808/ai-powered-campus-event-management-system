import sqlite3

DB_NAME = "campus.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            skills TEXT
        )
    ''')

    # 2. Events table 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            sub_category TEXT,
            description TEXT,
            tags TEXT,
            date TEXT,
            venue TEXT
        )
    ''')

    # 3. Registrations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
    ''')

    # 🌟 FIXED SEEDING BLOCK 1: Check and Seed Users independently
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        print("Seeding administrative and student user accounts...")
        cursor.executemany("INSERT OR IGNORE INTO users (username, password, role, department, skills) VALUES (?, ?, ?, ?, ?)", [
            # Standard Students
            ("student_cse", "pass123", "student", "CSE", "Coding, Bug Hunting, Web Design, Problem Solving"),
            ("student_ece", "pass123", "student", "ECE", "Circuits, Hardware, Project Exhibition, Innovation"),
            ("student_cultural", "pass123", "student", "ME", "Dancing, Photography, Arts, Riddles"),
            
            # Event Organizer
            ("organizer_virinchi", "org456", "organizer", "CSE", "Management, Planning, Coordination"),
            
            # Super Admin
            ("admin_main", "admin789", "admin", "SET", "Global Control, Infrastructure Security")
        ])

    # 🌟 FIXED SEEDING BLOCK 2: Check and Seed Events independently
    cursor.execute("SELECT COUNT(*) FROM events")
    if cursor.fetchone()[0] == 0:
        print("Seeding authentic VIRINCHI - 2K26 event dataset...")
        virinchi_events = [
            ("Bug Blasters", "Technical", "Celestra", "Test your debugging skills. Find and fix errors in broken code tracks quickly.", "Coding, Debugging, Problem Solving, Python, C++", "16-18 March 2026", "CSE Systems Lab"),
            ("Technical Charades", "Technical", "Celestra", "A team game where technical concepts must be acted out without speaking.", "Communication, Core Concepts, Teamwork, Technical", "16-18 March 2026", "Seminar Hall A"),
            ("Snake & Ladders (Tech Edition)", "Technical", "Celestra", "Classic board game mixed with instant engineering and tech trivia hurdles.", "Trivia, General Tech, Fun", "16-18 March 2026", "Open Plaza"),
            ("Brainwave Challenge", "Technical", "Sadarwa", "An intense technical quiz testing core engineering and analytical capabilities.", "Aptitude, Core Engineering, Logic", "16-18 March 2026", "Main Auditorium"),
            ("Treasure Hunt", "Technical", "Sadarwa", "Solve cryptic tech riddles hidden across campus to track down the final prize.", "Logic, Puzzles, Teamwork", "16-18 March 2026", "Campus Grounds"),
            ("Project Expo", "Technical", "Sadarwa", "Showcase your working engineering prototypes and full-stack web architectures.", "Project Exhibition, Innovation, Hardware, Software", "16-18 March 2026", "Main Corridor"),
            ("Quest of Secrets", "Technical", "Mecharena", "A mechanical and analytical tracking event involving structural challenges.", "Mechanics, Strategy, Logic", "16-18 March 2026", "Mechanical Lab"),
            ("Brain Battle", "Technical", "Mecharena", "Head-to-head quick fire engineering question match.", "Quiz, Quick Thinking, Core Tech", "16-18 March 2026", "Drawing Hall"),
            ("Drafting Marathon", "Technical", "Mecharena", "Precision structural modeling and digital design challenge.", "CAD, Design, Graphics, Precision", "16-18 March 2026", "CAD/CAM Lab"),
            ("Miss Virinchi-2K26", "Cultural", "Pageant", "The premier personality and talent hunt showcase of the national fest.", "Personality, Confidence, Presentation, Talent", "17 March 2026", "Open Air Theatre"),
            ("Natyakala", "Cultural", "Dance", "Classical and contemporary group and solo traditional dance exhibitions.", "Dance, Traditional, Arts, Performance", "18 March 2026", "Main Stage"),
            ("Freeze the Frame", "Cultural", "Photography", "Campus-wide theme photography competition capturing fest moments live.", "Photography, Editing, Creativity, Art", "16-18 March 2026", "Campus Wide"),
            ("Ethnic Aura", "Cultural", "Fashion", "Showcasing cultural legacy through innovative traditional couture designs.", "Fashion, Tradition, Styling, Presentation", "17 March 2026", "Main Stage"),
            ("Waste to Wonders", "Cultural", "Craft", "Creating beautiful structural models using recycled scraps and waste materials.", "Creativity, Crafts, Sustainability", "16 March 2026", "Basic Workshop")
        ]
        cursor.executemany(
            "INSERT INTO events (title, category, sub_category, description, tags, date, venue) VALUES (?, ?, ?, ?, ?, ?, ?)",
            virinchi_events
        )

    conn.commit()
    conn.close()
    print("Database configured and loaded successfully with Virinchi-2K26 layout data!")

if __name__ == "__main__":
    init_db()