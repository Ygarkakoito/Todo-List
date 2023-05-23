from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Подключение к базе данных
db = sqlite3.connect('todo.db', check_same_thread=False)
cursor = db.cursor()

# Создание таблицы пользователей и задач
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status INTEGER DEFAULT 0,
        priority INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

db.commit()

# Регистрация аккаунта
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        user = cursor.fetchone()

        if user:
            flash('Имя пользователя уже занято', 'error')
            return redirect('/register')

        hashed_password = generate_password_hash(password)

        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        db.commit()

        flash('Регистрация прошла успешно. Вы можете войти в свой аккаунт', 'success')
        return redirect('/login')

    return render_template('register.html')

# Вход в аккаунт
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user[2], password):
            flash('Неверное имя пользователя или пароль', 'error')
            return redirect('/login')

        session['user_id'] = user[0]
        session['username'] = user[1]

        return redirect('/')

    return render_template('login.html')

# Выход из аккаунта
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect('/login')

# Главная страница со списком дел
@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute('SELECT * FROM tasks WHERE user_id=?', (user_id,))
        tasks = cursor.fetchall()
        return render_template('index.html', tasks=tasks)

    return redirect('/login')

# Добавление задачи
@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' in session:
        user_id = session['user_id']
        title = request.form['title']
        deadline = request.form['deadline']
        priority = request.form['priority']

        cursor.execute('INSERT INTO tasks (user_id, title, deadline, priority) VALUES (?, ?, ?, ?)',
                       (user_id, title, deadline, priority))
        db.commit()
    return redirect('/')

# Обновление задачи
@app.route('/update/<int:task_id>', methods=['GET', 'POST'])
def update_task(task_id):
    if 'user_id' in session:
        if request.method == 'POST':
            title = request.form['title']
            deadline = request.form['deadline']
            priority = request.form['priority']
            status = request.form['status']

            cursor.execute('UPDATE tasks SET title=?, deadline=?, priority=?, status=? WHERE id=?',
                           (title, deadline, priority, status, task_id))
            db.commit()
            return redirect('/')

        cursor.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
        task = cursor.fetchone()
        return render_template('update.html', task=task)

    return redirect('/login')



# Удаление задачи
@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' in session:
        cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        db.commit()
    return redirect('/')


# Поиск задач
@app.route('/search', methods=['POST'])
def search():
    if 'user_id' in session:
        user_id = session['user_id']
        search_query = request.form['search_query']
        search_query = '%' + search_query + '%'

        cursor.execute('SELECT * FROM tasks WHERE user_id=? AND title LIKE ?', (user_id, search_query))
        tasks = cursor.fetchall()
        return render_template('index.html', tasks=tasks)

    return redirect('/login')

# Отметка выполненной задачи
# Отметка выполненной задачи
@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    if 'user_id' in session:
        cursor.execute('UPDATE tasks SET status=1 WHERE id=?', (task_id,))
        db.commit()
    return redirect('/')



# Сортировка задач
@app.route('/sort/<string:sort_by>')
def sort_tasks(sort_by):
    if 'user_id' in session:
        user_id = session['user_id']

        if sort_by == 'priority':
            cursor.execute('SELECT * FROM tasks WHERE user_id=? ORDER BY priority', (user_id,))
        elif sort_by == 'deadline':
            cursor.execute('SELECT * FROM tasks WHERE user_id=? ORDER BY deadline', (user_id,))
        else:
            cursor.execute('SELECT * FROM tasks WHERE user_id=? ORDER BY created_at', (user_id,))

        tasks = cursor.fetchall()
        return render_template('index.html', tasks=tasks)

    return redirect('/login')

@app.route('/account')
def account():
    if 'user_id' in session:
        user_id = session['user_id']

        # Получение информации о пользователе
        cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
        user = cursor.fetchone()

        # Получение списка задач пользователя
        cursor.execute('SELECT * FROM tasks WHERE user_id=?', (user_id,))
        tasks = cursor.fetchall()

        return render_template('account.html', user=user, tasks=tasks)

    return redirect('/login')

# Добавление электронной почты
@app.route('/add_email', methods=['POST'])
def add_email():
    if 'user_id' in session:
        user_id = session['user_id']
        email = request.form['email']

        cursor.execute('UPDATE users SET email=? WHERE id=?', (email, user_id))
        db.commit()

        flash('Электронная почта успешно добавлена', 'success')

    return redirect('/account')

# Изменение электронной почты
# Изменение электронной почты
@app.route('/edit_email', methods=['POST'])
def edit_email():
    if 'user_id' in session:
        user_id = session['user_id']
        new_email = request.form['email']

        cursor.execute('UPDATE users SET email=? WHERE id=?', (new_email, user_id))
        db.commit()
        flash('Электронная почта успешно изменена', 'success')

    return redirect('/account')


@app.route('/update_email', methods=['POST'])
def update_email():
    if 'user_id' in session:
        user_id = session['user_id']
        email = request.form['email']

        cursor.execute('UPDATE users SET email=? WHERE id=?', (email, user_id))
        db.commit()

        flash('Электронная почта успешно обновлена', 'success')

    return redirect('/account')


if __name__ == '__main__':
    app.run(debug=True)
