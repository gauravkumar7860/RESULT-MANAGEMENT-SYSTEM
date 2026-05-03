from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"


# ---------- DATABASE CONNECTION ----------
def get_db():
    return sqlite3.connect("database.db")


# ---------- HOME ----------
@app.route('/')
def home():
    return redirect('/admin/login')


# ---------- ADMIN LOGIN ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin":
            session['admin'] = True
            return redirect('/admin/dashboard')
        else:
            flash("Invalid Username or Password")

    return render_template('admin_login.html')


# ---------- ADMIN DASHBOARD ----------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin/login')
    return render_template('admin_dashboard.html')


# ---------- ADD CLASS ----------
@app.route('/admin/add_class', methods=['GET', 'POST'])
def add_class():
    if 'admin' not in session:
        return redirect('/admin/login')

    if request.method == 'POST':
        name = request.form['class_name']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO classes (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()

        return redirect('/admin/dashboard')

    return render_template('add_class.html')


# ---------- ADD STUDENT ----------
@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if 'admin' not in session:
        return redirect('/admin/login')

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll_no']
        class_id = request.form['class_id']

        cursor.execute("""
            INSERT INTO students (name, roll_no, class_id)
            VALUES (?, ?, ?)
        """, (name, roll, class_id))

        conn.commit()
        conn.close()
        return redirect('/admin/dashboard')

    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()
    conn.close()

    return render_template('add_student.html', classes=classes)


# ---------- ADD SUBJECT ----------
@app.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    if 'admin' not in session:
        return redirect('/admin/login')

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['subject_name']
        class_id = request.form['class_id']

        cursor.execute("""
            INSERT INTO subjects (name, class_id)
            VALUES (?, ?)
        """, (name, class_id))

        conn.commit()
        conn.close()
        return redirect('/admin/dashboard')

    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()
    conn.close()

    return render_template('add_subject.html', classes=classes)


# ---------- ADD MARKS ----------
@app.route('/admin/add_marks', methods=['GET', 'POST'])
def add_marks():
    if 'admin' not in session:
        return redirect('/admin/login')

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        student_id = request.form['student_id']
        subject_id = request.form['subject_id']
        marks = request.form['marks']

        # Prevent duplicate marks
        cursor.execute("""
            SELECT * FROM marks WHERE student_id=? AND subject_id=?
        """, (student_id, subject_id))

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE marks SET marks=? WHERE student_id=? AND subject_id=?
            """, (marks, student_id, subject_id))
        else:
            cursor.execute("""
                INSERT INTO marks (student_id, subject_id, marks)
                VALUES (?, ?, ?)
            """, (student_id, subject_id, marks))

        conn.commit()
        conn.close()
        return redirect('/admin/dashboard')

    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT id, name FROM subjects")
    subjects = cursor.fetchall()

    conn.close()

    return render_template('add_marks.html', students=students, subjects=subjects)


# ---------- STUDENT LOGIN ----------
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll = request.form['roll_no']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE roll_no=?", (roll,))
        student = cursor.fetchone()
        conn.close()

        if student:
            session['student_id'] = student[0]
            return redirect('/result')
        else:
            flash("Invalid Roll Number")

    return render_template('student_login.html')


# ---------- VIEW RESULT ----------
@app.route('/result')
def result():
    if 'student_id' not in session:
        return redirect('/student/login')

    conn = get_db()
    cursor = conn.cursor()

    # Student info
    cursor.execute("SELECT * FROM students WHERE id=?", (session['student_id'],))
    student = cursor.fetchone()

    # Marks + subjects
    cursor.execute("""
        SELECT subjects.name, marks.marks
        FROM marks
        JOIN subjects ON marks.subject_id = subjects.id
        WHERE marks.student_id=?
    """, (session['student_id'],))

    results = cursor.fetchall()

    # Calculate total & percentage
    total_marks = sum([r[1] for r in results]) if results else 0
    percentage = (total_marks / (len(results) * 100) * 100) if results else 0

    conn.close()

    return render_template(
        'result.html',
        student=student,
        results=results,
        total_marks=total_marks,
        percentage=percentage
    )


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)
