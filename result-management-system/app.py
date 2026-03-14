from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY, class_id INTEGER, name TEXT,
                 FOREIGN KEY(class_id) REFERENCES classes(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, roll_no TEXT UNIQUE, class_id INTEGER,
                 FOREIGN KEY(class_id) REFERENCES classes(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS marks (id INTEGER PRIMARY KEY, student_id INTEGER, subject_id INTEGER, marks INTEGER,
                 FOREIGN KEY(student_id) REFERENCES students(id), FOREIGN KEY(subject_id) REFERENCES subjects(id))''')
    
    c.execute("SELECT * FROM admin WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO admin (username, password) VALUES ('admin', 'admin123')")
    conn.commit()
    conn.close()

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        admin = c.fetchone()
        conn.close()
        if admin:
            session['admin_id'] = admin[0]
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials!')
    return render_template('admin_login.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,))
        student = c.fetchone()
        conn.close()
        if student:
            session['student_id'] = student[0]
            session['student_roll_no'] = roll_no
            return redirect(url_for('student_result'))
        flash('Student not found!')
    return render_template('student_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM classes")
    classes = c.fetchall()
    c.execute("SELECT COUNT(*) FROM students")
    total_students = c.fetchone()[0]
    conn.close()
    return render_template('admin_dashboard.html', classes=classes, total_students=total_students)

@app.route('/admin/add_class', methods=['GET', 'POST'])
def add_class():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        class_name = request.form['class_name']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO classes (name) VALUES (?)", (class_name,))
            conn.commit()
            flash('Class added successfully!')
        except:
            flash('Error adding class!')
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_class.html')

@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM classes")
    classes = c.fetchall()
    conn.close()
    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        class_id = request.form['class_id']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO students (name, roll_no, class_id) VALUES (?, ?, ?)", (name, roll_no, class_id))
            conn.commit()
            flash('Student added successfully!')
        except:
            flash('Roll number already exists!')
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_student.html', classes=classes)

@app.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM classes")
    classes = c.fetchall()
    conn.close()
    if request.method == 'POST':
        class_id = request.form['class_id']
        subject_name = request.form['subject_name']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO subjects (class_id, name) VALUES (?, ?)", (class_id, subject_name))
            conn.commit()
            flash('Subject added successfully!')
        except:
            flash('Subject already exists!')
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_subject.html', classes=classes)

@app.route('/admin/add_marks', methods=['GET', 'POST'])
def add_marks():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM classes")
    classes = c.fetchall()
    c.execute("SELECT s.id, s.name, s.roll_no, cl.name FROM students s JOIN classes cl ON s.class_id=cl.id")
    students = c.fetchall()
    c.execute("SELECT sub.id, sub.name, cl.name FROM subjects sub JOIN classes cl ON sub.class_id=cl.id")
    subjects_list = c.fetchall()
    conn.close()
    if request.method == 'POST':
        student_id = request.form['student_id']
        subject_id = request.form['subject_id']
        marks = request.form['marks']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO marks (student_id, subject_id, marks) VALUES (?, ?, ?)", (student_id, subject_id, marks))
        conn.commit()
        conn.close()
        flash('Marks added successfully!')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_marks.html', classes=classes, students=students, subjects=subjects_list)

@app.route('/student/result')
def student_result():
    if not session.get('student_id'):
        return redirect(url_for('student_login'))
    student_id = session['student_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT s.*, cl.name as class_name FROM students s JOIN classes cl ON s.class_id=cl.id WHERE s.id=?", (student_id,))
    student = c.fetchone()
    c.execute("SELECT sub.name, m.marks FROM marks m JOIN subjects sub ON m.subject_id=sub.id JOIN students s ON m.student_id=s.id WHERE s.id=?", (student_id,))
    results = c.fetchall()
    total_marks = sum([row[1] for row in results]) if results else 0
    total_subjects = len(results)
    percentage = (total_marks / (total_subjects * 100) * 100) if total_subjects > 0 else 0
    conn.close()
    return render_template('result.html', student=student, results=results, total_marks=total_marks, percentage=percentage)

@app.route('/download_pdf')
def download_pdf():
    if not session.get('student_id'):
        return redirect(url_for('student_login'))
    student_id = session['student_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT s.*, cl.name as class_name FROM students s JOIN classes cl ON s.class_id=cl.id WHERE s.id=?", (student_id,))
    student = c.fetchone()
    c.execute("SELECT sub.name, m.marks FROM marks m JOIN subjects sub ON m.subject_id=sub.id JOIN students s ON m.student_id=s.id WHERE s.id=?", (student_id,))
    results = c.fetchall()
    total_marks = sum([row[1] for row in results]) if results else 0
    total_subjects = len(results)
    percentage = (total_marks / (total_subjects * 100) * 100) if total_subjects > 0 else 0
    conn.close()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=24, spaceAfter=30, alignment=1)
    story.append(Paragraph("REPORT CARD", title_style))
    story.append(Spacer(1, 20))
    
    student_data = [['Student Name:', student[1]], ['Roll No:', student[2]], ['Class:', student[8]], ['Date:', datetime.now().strftime('%Y-%m-%d')]]
    student_table = Table(student_data)
    student_table.setStyle(TableStyle([('BACKGROUND', (0,0),(-1,0), colors.grey), ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),14),
    ('BOTTOMPADDING',(0,0),(-1,0),12),('BACKGROUND',(0,1),(-1,-1),colors.beige),('GRID',(0,0),(-1,-1),1,colors.black)]))
    story.append(student_table)
    
    if results:
        story.append(Spacer(1, 20))
        marks_data = [['Subject', 'Marks']] + [[sub[0], sub[1]] for sub in results]
        marks_table = Table(marks_data)
        marks_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),12),
        ('BOTTOMPADDING',(0,0),(-1,0),12),('BACKGROUND',(0,1),(-1,-1),colors.beige),('GRID',(0,0),(-1,-1),1,colors.black)]))
        story.append(marks_table)
        story.append(Spacer(1, 10))
        summary_data = [['Total Marks', f'{total_marks}/{total_subjects*100}'], ['Percentage', f'{percentage:.2f}%']]
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.lightblue),('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),12),('GRID',(0,0),(-1,-1),1,colors.black)]))
        story.append(summary_table)
    
    doc.build(story)
    buffer.seek(0)
    return send_file(io.BytesIO(buffer.getvalue()), as_attachment=True, download_name=f"report_card_{student[2]}.pdf", mimetype='application/pdf')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/')
def home():
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)