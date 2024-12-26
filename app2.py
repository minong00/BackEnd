from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask import abort
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os



app = Flask(__name__)
CORS(app)  # 모든 도메인 허용
# 또는 특정 도메인만 허용
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
app.config['SECRET_KEY'] = 'your_secret_key_here'  # 보안을 위해 실제 운영 시 복잡한 키 사용
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(255), nullable=True)  # 첨부파일 경로
    is_public = db.Column(db.Boolean, default=True)  # 공개 여부

# app 초기화 후에 추가
UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 사용자 모델 정의
class Users(db.Model):
    __tablename__ = 'users'  # 명시적으로 테이블 이름 지정
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

admin = Admin(app, name='My App', template_mode='bootstrap3')
admin.add_view(ModelView(Users, db.session))  # Users 모델을 어드민 페이지에 추가

with app.app_context():
    db.drop_all()  # 기존 테이블 전부 삭제
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



app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
@app.route('/')
def home():
    # 로그인 상태 확인
    if 'username' in session:
        return f'로그인된 사용자: {session["username"]} <a href="/logout">로그아웃</a>'
    return render_template('home.html')



def is_admin():
    return session.get('role') == 'admin'  # 세션에서 역할 확인

@app.route('/admin')
def admin_():
    if not is_admin():
        abort(403)  # 접근 금지
    return render_template('admin.html')  # 관리자 대시보드 템플릿

def CRUDadmin_():
    if not is_admin():
        abort(403)
    return render_template('admin.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # 사용자 존재 여부 확인
        existing_user = Users.query.filter_by(username=username).first()
        if existing_user:
            flash('이미 존재하는 사용자입니다.')
            return redirect('/signup')

        # 비밀번호 해시화
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # 새 사용자 생성
        new_user = Users(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('회원가입 성공!')
        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 사용자 조회
        user = Users.query.filter_by(username=username).first()

        # 인증 검사
        if user and check_password_hash(user.password_hash, password):
            session['username'] = username
            flash('로그인 성공!')
            return redirect('/')
        else:
            flash('잘못된 사용자 이름 또는 비밀번호입니다.')

    return render_template('login.html')


@app.route('/announcements')
def announcements():
    announcements = Announcement.query.all()  # 모든 공지사항 조회
    return render_template('announcements.html', announcements=announcements)

@app.route('/announcements/new', methods=['GET', 'POST'])
def new_announcement():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        attachment = request.files.get('attachment')  # 첨부파일 처리

        # 파일 저장 로직 (예: /uploads/ 폴더에 저장)
        attachment_path = None
        if attachment:
            attachment_path = os.path.join('uploads', attachment.filename)
            attachment.save(attachment_path)

        new_announcement = Announcement(title=title, body=body, attachment=attachment_path)
        db.session.add(new_announcement)
        db.session.commit()

        flash('공지사항이 추가되었습니다.')
        return redirect('/announcements')

    return render_template('new_announcement.html')


@app.route('/announcements/edit/<int:id>', methods=['GET', 'POST'])
def edit_announcement(id):
    announcement = Announcement.query.get_or_404(id)

    if request.method == 'POST':
        announcement.title = request.form['title']
        announcement.body = request.form['body']

        # 파일 업데이트 로직 (선택적)
        attachment = request.files.get('attachment')
        if attachment:
            attachment_path = os.path.join('uploads', attachment.filename)
            attachment.save(attachment_path)
            announcement.attachment = attachment_path

        announcement.is_public = 'is_public' in request.form  # 체크박스 처리
        db.session.commit()

        flash('공지사항이 수정되었습니다.')
        return redirect('/announcements')

    return render_template('edit_announcement.html', announcement=announcement)


@app.route('/announcements/delete/<int:id>', methods=['POST'])
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()

    flash('공지사항이 삭제되었습니다.')
    return redirect('/announcements')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('로그아웃 되었습니다.')

    return redirect('/')




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)