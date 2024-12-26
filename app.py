from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})  # React 개발 서버 주소

app.config['SECRET_KEY'] = 'your_secret_key_here'  # 보안을 위해 실제 운영 시 복잡한 키 사용
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


# 공지사항 모델 정의
class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(255), nullable=True)  # 첨부파일 경로
    is_public = db.Column(db.Boolean, default=True)  # 공개 여부


# 관리자 페이지 설정
admin = Admin(app, name='My App', template_mode='bootstrap3')
admin.add_view(ModelView(Users, db.session))  # Users 모델을 어드민 페이지에 추가
admin.add_view(ModelView(Announcement, db.session))  # Announcement 모델을 어드민 페이지에 추가

# 초기 데이터베이스 생성
with app.app_context():
    db.drop_all()  # 기존 테이블 전부 삭제 (운영 환경에서는 주의!)
    db.create_all()  # 새로 테이블 생성

    # 기본 관리자 계정 추가
    if not Users.query.filter_by(username='admin').first():
        admin_user = Users(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('adminpassword'),  # 기본 비밀번호 해시화
        )
        db.session.add(admin_user)
        db.session.commit()


# 홈 페이지 라우트
@app.route('/')
def home():
    if 'username' in session:
        return f'로그인된 사용자: {session["username"]} <a href="/logout">로그아웃</a>'
    return render_template('home.html')


# 사용자 등록 API
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
    hashed_password = generate_password_hash(password)

    # 새 사용자 생성
    new_user = Users(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True, "message": "회원가입 성공!"}), 201


# 로그인 API
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 사용자 조회
    user = Users.query.filter_by(username=username).first()

    # 인증 검사
    if user and check_password_hash(user.password_hash, password):
        session['username'] = username  # 세션에 사용자 이름 저장
        return jsonify({"success": True, "message": "로그인 성공!", "username": username}), 200

    return jsonify({"success": False, "message": "잘못된 사용자 이름 또는 비밀번호입니다."}), 401


# 로그아웃 라우트
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('로그아웃 되었습니다.')
    return redirect('/')


# 공지사항 목록 조회 API
@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    announcements = Announcement.query.all()
    return jsonify([{
        'id': announcement.id,
        'title': announcement.title,
        'body': announcement.body,
        'attachment': announcement.attachment,
        'is_public': announcement.is_public,
    } for announcement in announcements]), 200


# 공지사항 추가 API
@app.route('/api/announcements', methods=['POST'])
def create_announcement():
    data = request.json
    title = data.get('title')
    body = data.get('body')

    new_announcement = Announcement(title=title, body=body)

    db.session.add(new_announcement)
    db.session.commit()

    return jsonify({"success": True, "message": "공지사항이 추가되었습니다."}), 201


# 공지사항 수정 API (PUT 요청)
@app.route('/api/announcements/<int:id>', methods=['PUT'])
def update_announcement(id):
    announcement = Announcement.query.get_or_404(id)

    data = request.json
    announcement.title = data.get('title', announcement.title)
    announcement.body = data.get('body', announcement.body)

    db.session.commit()

    return jsonify({"success": True, "message": "공지사항이 수정되었습니다."}), 200


# 공지사항 삭제 API (DELETE 요청)
@app.route('/api/announcements/<int:id>', methods=['DELETE'])
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)

    db.session.delete(announcement)
    db.session.commit()

    return jsonify({"success": True, "message": "공지사항이 삭제되었습니다."}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
