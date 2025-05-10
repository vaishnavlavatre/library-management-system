from flask import Flask, request, jsonify
import jwt
import datetime
from functools import wraps
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vuO1SiuDS7SkmkxM__24lgh4R-s9nJ52Y4vhV1xjVcU'

def init_db():
    conn = sqlite3.connect('auth_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 role TEXT NOT NULL)''')
    
    # Add admin user if not exists
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ('admin', 'admin123', 'admin'))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()

init_db()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        
        try:
            data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
            current_role = data['role']
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        
        return f(current_user, current_role, *args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401
    
    conn = sqlite3.connect('auth_db.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (auth.username,))
    user = c.fetchone()
    conn.close()
    
    if not user or user[2] != auth.password:
        return jsonify({'message': 'Invalid credentials!'}), 401
    
    token = jwt.encode({
        'id': user[0],
        'username': user[1],
        'role': user[3],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])
    
    return jsonify({'token': token})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required!'}), 400
    
    conn = sqlite3.connect('auth_db.sqlite')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, password, role))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Username already exists!'}), 400
    conn.close()
    
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/verify', methods=['GET'])
def verify_token():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 403
    
    try:
        data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=["HS256"])
        return jsonify({
            'id': data['id'],
            'username': data['username'],
            'role': data['role']
        })
    except:
        return jsonify({'message': 'Token is invalid!'}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)