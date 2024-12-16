from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # 보안을 위해 실제 운영 시 복잡한 키 사용
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)


# 사용자 모델 정의
class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


# 초기 데이터베이스 생성
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    # 로그인 상태 확인
    if 'username' in session:
        return f'로그인된 사용자: {session["username"]} <a href="/logout">로그아웃</a>'
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # 사용자 존재 여부 확인
        existing_user = users.query.filter_by(username=username).first()
        if existing_user:
            flash('이미 존재하는 사용자입니다.')
            return redirect('/signup')

        # 비밀번호 해시화
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # 새 사용자 생성
        new_user = users(username=username, email=email, password_hash=hashed_password)
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
        user = users.query.filter_by(username=username).first()

        # 인증 검사
        if user and check_password_hash(user.password_hash, password):
            session['username'] = username
            flash('로그인 성공!')
            return redirect('/')
        else:
            flash('잘못된 사용자 이름 또는 비밀번호입니다.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('로그아웃 되었습니다.')
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)