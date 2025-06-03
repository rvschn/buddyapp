from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'buddyapp_secret'

def init_db():
    conn = sqlite3.connect('buddyapp.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT UNIQUE,
            password TEXT,
            gender TEXT,
            role TEXT,
            interest TEXT,
            need_help TEXT,
            offer_help TEXT,
            city TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'username' in session:
        return redirect('/match')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        gender = request.form['gender']
        role = request.form['role']
        interest = request.form['interest']
        need_help = request.form.get('need_help', '') if role == 'hilfe' else ''
        offer_help = request.form.get('offer_help', '') if role == 'buddy' else ''
        city = request.form['city']

        conn = sqlite3.connect('buddyapp.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (name, username, password, gender, role, interest, need_help, offer_help, city) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (name, username, password, gender, role, interest, need_help, offer_help, city))
            conn.commit()
        except:
            return "Fehler: Benutzername existiert bereits."
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('buddyapp.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect('/match')
        return "Login fehlgeschlagen."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/match')
def match():
    if 'username' not in session:
        return redirect('/login')
    
    city_filter = request.args.get('city', '').strip()
    role_filter = request.args.get('role', '').strip()
    interest_filter = request.args.get('interest', '').strip()

    conn = sqlite3.connect('buddyapp.db')
    c = conn.cursor()
    query = 'SELECT name, gender, role, interest, need_help, offer_help, city FROM users WHERE 1=1'
    params = []
    if city_filter:
        query += ' AND city LIKE ?'
        params.append(f"%{city_filter}%")
    if role_filter:
        query += ' AND role = ?'
        params.append(role_filter)
    if interest_filter:
        query += ' AND interest LIKE ?'
        params.append(f"%{interest_filter}%")
    c.execute(query, params)
    users = c.fetchall()
    conn.close()
    return render_template('match.html', users=users)

@app.route('/profil')
def profil():
    if 'username' not in session:
        return redirect('/login')
    conn = sqlite3.connect('buddyapp.db')
    c = conn.cursor()
    c.execute('SELECT name, username, gender, role, interest, need_help, offer_help, city FROM users WHERE username = ?', (session['username'],))
    user = c.fetchone()
    conn.close()
    return render_template('profil.html', user=user)

@app.route('/admin')
def admin():
    if 'username' not in session or session['username'] != 'admin':
        return redirect('/login')
    conn = sqlite3.connect('buddyapp.db')
    c = conn.cursor()
    c.execute('SELECT id, name, username, gender, role, interest, city FROM users')
    users = c.fetchall()
    conn.close()
    return render_template('admin.html', users=users)

@app.route('/admin/delete/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    if 'username' not in session or session['username'] != 'admin':
        return redirect('/login')
    
    conn = sqlite3.connect('buddyapp.db')
    c = conn.cursor()

    if request.method == 'POST':
        code = request.form.get('code')
        if code == '1234':
            c.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return redirect('/admin')
        else:
            conn.close()
            return "❌ Falscher Sicherheitscode."

    c.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return render_template('confirm_delete.html', username=result[0])
    else:
        return "Benutzer nicht gefunden."
init_db()

if __name__ == '__main__':
    app.run(debug=True)
