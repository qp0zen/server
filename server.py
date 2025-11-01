from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)  # Разрешаем запросы из приложения
app.config['SECRET_KEY'] = 'dargas12'

# "База данных" пользователей
users = {
    "user": {"password": "123456", "email": "user@test.com"},
    "admin": {"password": "admin", "email": "admin@test.com"},
    "test": {"password": "test", "email": "test@test.com"}
}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        try:
            # Убираем 'Bearer ' если есть
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return jsonify({"message": "Auth Server is running!", "status": "OK"})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        print(f"Login attempt: {username}")  # Для дебага
        
        if username in users and users[username]['password'] == password:
            # Генерируем токен
            token = jwt.encode({
                'user': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'username': username
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

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password or not email:
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400
        
        if username in users:
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 400
        
        # Добавляем нового пользователя
        users[username] = {
            "password": password, 
            "email": email
        }
        
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
        
        return jsonify({
            'success': True,
            'username': username,
            'email': users[username]['email']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Profile error: {str(e)}'
        }), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    # Для тестирования - возвращает список пользователей (без паролей)
    users_list = {username: {"email": data["email"]} for username, data in users.items()}
    return jsonify({
        'success': True,
        'users': users_list
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)