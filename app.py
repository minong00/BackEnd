from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "http://localhost:3000",  # React 개발 서버 주소
        "supports_credentials": True  # 세션 쿠키 허용
    }
})
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# 사용자 모델 정의
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


# 데이터베이스 초기화
with app.app_context():
    db.drop_all()
    db.create_all()


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 사용자 존재 여부 확인
    existing_user = Users.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"success": False, "message": "이미 존재하는 사용자입니다."}), 400

    # 비밀번호 해시화
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    # 새 사용자 생성
    new_user = Users(username=username, email=email, password_hash=hashed_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"success": True, "message": "회원가입 성공"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 사용자 조회
    user = Users.query.filter_by(username=username).first()

    # 인증 검사
    if user and check_password_hash(user.password_hash, password):
        session['username'] = username
        return jsonify({
            "success": True,
            "message": "로그인 성공",
            "username": username
        }), 200
    else:
        return jsonify({"success": False, "message": "잘못된 사용자 이름 또는 비밀번호입니다."}), 401


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('username', None)
    return jsonify({"success": True, "message": "로그아웃 되었습니다."}), 200


@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'username' in session:
        return jsonify({
            "isAuthenticated": True,
            "username": session['username']
        }), 200
    return jsonify({"isAuthenticated": False}), 401


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)