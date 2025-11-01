from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'dargas12'

# Инициализация базы данных
def init_db():
    try:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        c = conn.cursor()
        
        # Создаем таблицу пользователей
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      email TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Добавляем тестовых пользователей, если их нет
        test_users = [
            ('user', '123456', 'user@test.com'),
            ('admin', 'admin', 'admin@test.com'),
            ('test', 'test', 'test@test.com')
        ]
        
        for username, password, email in test_users:
            c.execute("INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)", 
                     (username, password, email))
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

# Инициализируем базу при старте
init_db()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return jsonify({"message": "Auth Server with Database is running!", "status": "OK"})

@app.route('/api/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return jsonify({"message": "Login endpoint - use POST method"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No JSON data received'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        print(f"🔐 Login attempt: {username}")
        
        conn = sqlite3.connect('users.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                 (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            # Генерируем токен
            token = jwt.encode({
                'user': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'username': username,
                'user_id': user[0]
            })
        
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/register', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return jsonify({"message": "Register endpoint - use POST method"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No JSON data received'}), 400
            
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password or not email:
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400
        
        conn = sqlite3.connect('users.db', check_same_thread=False)
        c = conn.cursor()
        
        # Проверяем, существует ли пользователь
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 400
        
        # Добавляем нового пользователя
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                 (username, password, email))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Registration error: {str(e)}'
        }), 500

@app.route('/api/profile', methods=['GET'])
@token_required
def profile():
    try:
        token = request.headers.get('Authorization')
        if token.startswith('Bearer '):
            token = token[7:]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        username = data['user']
        
        conn = sqlite3.connect('users.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id, username, email, created_at FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'success': True,
                'user_id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3]
            })
        else:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Profile error: {str(e)}'
        }), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id, username, email, created_at FROM users")
        users = c.fetchall()
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3]
            })
        
        return jsonify({
            'success': True,
            'users': users_list,
            'total': len(users_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching users: {str(e)}'
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        c = conn.cursor()
        
        # Общее количество пользователей
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        # Последние 5 пользователей
        c.execute("SELECT username, email, created_at FROM users ORDER BY created_at DESC LIMIT 5")
        recent_users = c.fetchall()
        
        conn.close()
        
        recent_users_list = []
        for user in recent_users:
            recent_users_list.append({
                'username': user[0],
                'email': user[1],
                'created_at': user[2]
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'recent_users': recent_users_list
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching stats: {str(e)}'
        }), 500

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'success': True,
        'message': 'API is working!',
        'endpoints': ['/api/login', '/api/register', '/api/profile', '/api/users', '/api/stats']
    })

if __name__ == '__main__':
    print("🚀 Starting Auth Server with Database...")
    print("📊 Database: users.db")
    print("🌐 Server running on http://0.0.0.0:5000")
    print("✅ Available endpoints:")
    print("   GET  /")
    print("   POST /api/login")
    print("   POST /api/register") 
    print("   GET  /api/profile")
    print("   GET  /api/users")
    print("   GET  /api/stats")
    print("   GET  /api/test")
    app.run(host='0.0.0.0', port=5000, debug=True)
