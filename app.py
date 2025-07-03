from flask import Flask, render_template, request, redirect, session, url_for
import pymysql
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

connection = pymysql.connect(
    host="localhost",
    user="root",
    password='',
    database="todo_app"
)
cur = connection.cursor()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def dashboard():
    cur.execute("SELECT sort_order FROM settings WHERE id = 1")
    result = cur.fetchone()
    sort_order = result[0] if result else 'date'

    sort_field = {
        'title': 'title',
        'date': 'date',
        'status': 'status'
    }.get(sort_order, 'date')

    cur.execute(f"SELECT * FROM tasks ORDER BY {sort_field} ASC")
    tasks = cur.fetchall()
    return render_template('board.html', tasks=tasks)

@app.route('/todotasks', methods=["POST", "GET"])
def todotasks():
    if request.method == "POST":
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        if title == "" or description == "" or date == "":
            return render_template('todotasks.html', error="All fields are required.")
        cur.execute("INSERT INTO tasks(title, description, date, status) VALUES(%s, %s, %s, 'pending')", (title, description, date))
        connection.commit()
        return render_template('todotasks.html', success="Task has been added successfully")
    return render_template('todotasks.html')

@app.route('/deletetasks/<int:task_id>', methods=["GET"])
def deletetasks(task_id):
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    connection.commit()
    return redirect('/')

@app.route('/toggle_status/<int:task_id>', methods=["POST"])
def toggle_status(task_id):
    cur.execute("SELECT status FROM tasks WHERE id = %s", (task_id,))
    current_status = cur.fetchone()[0]
    new_status = 'done' if current_status == 'pending' else 'pending'
    cur.execute("UPDATE tasks SET status = %s WHERE id = %s", (new_status, task_id))
    connection.commit()
    return '', 204

@app.route('/profile', methods=["GET", "POST"])
def profile():
    if request.method == 'POST':
        file = request.files.get('profile_pic')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            session['profile_pic'] = filename

    cur.execute("SELECT COUNT(*) FROM tasks")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'done'")
    done = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
    pending = cur.fetchone()[0]

    return render_template('profile.html',
                           profile_pic=session.get('profile_pic'),
                           total=total, done=done, pending=pending)




@app.route('/analytics')
def analytics():
    cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
    status_data = cur.fetchall()

    cur.execute("""
        SELECT DATE(date) as task_date, COUNT(*) FROM tasks
        GROUP BY task_date ORDER BY task_date
    """)
    daily_data = cur.fetchall()

    return render_template("analytics.html", status_data=status_data, daily_data=daily_data)













@app.route('/settings', methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        sort_order = request.form.get("sort_order")
        notifications = 1 if request.form.get("notifications") == "on" else 0
        cur.execute("UPDATE settings SET sort_order=%s, notifications=%s WHERE id=1", (sort_order, notifications))
        connection.commit()
        return redirect(url_for('settings'))

    cur.execute("SELECT sort_order, notifications FROM settings WHERE id=1")
    current_settings = cur.fetchone()
    return render_template("settings.html", settings=current_settings)

if __name__ == '__main__':
    app.run(debug=True)
