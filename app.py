from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # ASCII 대신 UTF-8 사용
CORS(app, resources={
    r"/*": {
        "origins": "http://localhost:3000",  # React 개발 서버 주소
        "supports_credentials": True
    }
})

# 설정
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'your_secret_key_here'
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


db = SQLAlchemy(app)

# User 모델 추가
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(255), nullable=True)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 공지사항 목록 조회
@app.route('/api/announcements', methods=['GET'])
def get_announcements():
    """
    GET /api/announcements
    모든 공지사항의 목록을 조회합니다.

    응답 예시:
    {
        "success": true,
        "announcements": [
            {
                "id": 1,
                "title": "공지사항 제목",
                "body": "공지사항 내용",
                "attachment": null,
                "is_public": true,
                "created_at": "2023-12-26T14:00:00",
                "updated_at": "2023-12-26T14:00:00"
            }
        ]
    }
    """
    try:
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
        return jsonify({
            'success': True,
            'announcements': [{
                'id': a.id,
                'title': a.title,
                'body': a.body,
                'attachment': a.attachment,
                'is_public': a.is_public,
                'created_at': a.created_at.isoformat(),
                'updated_at': a.updated_at.isoformat()
            } for a in announcements]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 공지사항 상세 조회
@app.route('/api/announcements/<int:id>', methods=['GET'])
def get_announcement(id):
    """
    GET /api/announcements/<id>
    특정 ID를 가진 공지사항의 상세 정보를 조회합니다.

    URL 파라미터:
    - id: 조회할 공지사항의 ID (integer)

    응답 예시:
    {
        "success": true,
        "announcement": {
            "id": 1,
            "title": "공지사항 제목",
            "body": "공지사항 내용",
            "attachment": null,
            "is_public": true,
            "created_at": "2023-12-26T14:00:00",
            "updated_at": "2023-12-26T14:00:00"
        }
    }
    """
    try:
        announcement = Announcement.query.get_or_404(id)
        return jsonify({
            'success': True,
            'announcement': {
                'id': announcement.id,
                'title': announcement.title,
                'body': announcement.body,
                'attachment': announcement.attachment,
                'is_public': announcement.is_public,
                'created_at': announcement.created_at.isoformat(),
                'updated_at': announcement.updated_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 공지사항 생성
@app.route('/api/announcements/create/<int:id>', methods=['POST'])
def create_announcement():
    """
    POST /api/announcements/create
    새로운 공지사항을 생성합니다.

    요청 본문 (form-data):
    - title: 공지사항 제목 (string, 필수)
    - body: 공지사항 내용 (string, 필수)
    - is_public: 공개 여부 (boolean, 선택, 기본값은 true)
    - attachment: 첨부 파일 (file, 선택)

    응답 예시:
    {
        "success": true,
        "message": "공지사항이 생성되었습니다.",
        "announcement_id": 1
    }

    상태 코드:
      - 201 Created: 성공적으로 공지사항이 생성됨
      - 401 Unauthorized: 로그인 필요
      - 500 Internal Server Error: 서버 오류 발생
    """

    if 'username' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401

    try:
        data = request.form
        title = data.get('title')
        body = data.get('body')
        is_public = data.get('is_public', 'true').lower() == 'true'

        # 파일 처리
        attachment = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                attachment = filename

        new_announcement = Announcement(
            title=title,
            body=body,
            attachment=attachment,
            is_public=is_public
        )

        db.session.add(new_announcement)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '공지사항이 생성되었습니다.',
            'announcement_id': new_announcement.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 공지사항 수정
@app.route('/api/announcements/correction/<int:id>', methods=['PUT'])
def update_announcement(id):
    """
    PUT /api/announcements/<id>
    특정 ID를 가진 공지사항을 수정합니다.

    요청 본문 (form-data):
    - title: 공지사항 제목 (string, 선택)
    - body: 공지사항 내용 (string, 선택)
    - is_public: 공개 여부 (boolean, 선택)
    - attachment: 첨부 파일 (file, 선택)

   응답 예시:
   {
       "success": true,
       "message": "공지사항이 수정되었습니다."
   }

   상태 코드:
     - 200 OK: 성공적으로 공지사항이 수정됨
     - 401 Unauthorized: 로그인 필요
     - 404 Not Found: 해당 ID의 공지사항이 존재하지 않음
     - 500 Internal Server Error: 서버 오류 발생
   """

    if 'username' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401

    try:
        announcement = Announcement.query.get_or_404(id)
        data = request.form

        # 데이터 업데이트
        announcement.title = data.get('title', announcement.title)
        announcement.body = data.get('body', announcement.body)
        announcement.is_public = data.get('is_public', 'true').lower() == 'true'

        # 파일 처리
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file.filename:
                # 기존 파일 삭제
                if announcement.attachment:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], announcement.attachment)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                # 새 파일 저장
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                announcement.attachment = filename

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '공지사항이 수정되었습니다.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500




# 공지사항 삭제
@app.route('/api/announcements/delete/<int:id>', methods=['DELETE'])
def delete_announcement(id):
    """
    DELETE /api/announcements/<id>
    특정 ID를 가진 공지사항을 삭제합니다.

    응답 예시:
    {
        "success": true,
        "message": "공지사항이 삭제되었습니다."
    }

    상태 코드:
      - 200 OK: 성공적으로 공지사항이 삭제됨
      - 401 Unauthorized: 로그인 필요
      - 404 Not Found: 해당 ID의 공지사항이 존재하지 않음
      - 500 Internal Server Error: 서버 오류 발생
    """

    if 'username' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401

    try:
        announcement = Announcement.query.get_or_404(id)

        # 첨부 파일 삭제
        if announcement.attachment:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], announcement.attachment)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(announcement)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '공지사항이 삭제되었습니다.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/uploads/<path:filename>')
def download_file(filename):
    """
    GET /api/uploads/<filename>
    첨부파일을 다운로드합니다.
    """
    try:
        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            return jsonify({'success': False, 'message': '파일을 찾을 수 없습니다.'}), 404
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 회원가입
@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    새로운 사용자를 등록합니다.
    """
    try:
        data = request.get_json()

        # 필수 필드 검증
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'{field}가 필요합니다.'}), 400

        # 이메일, 사용자명 중복 체크
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': '이미 존재하는 사용자명입니다.'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': '이미 존재하는 이메일입니다.'}), 400

        # 새 사용자 생성
        user = User(
            username=data['username'],
            email=data['email'],
            is_admin=data.get('is_admin', False)
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '회원가입이 완료되었습니다.',
            'user_id': user.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# 로그인
@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    사용자 로그인을 처리합니다.
    """
    try:
        data = request.get_json()

        # 필수 필드 검증
        if not all(k in data for k in ('username', 'password')):
            return jsonify({'success': False, 'message': '사용자명과 비밀번호가 필요합니다.'}), 400

        # 사용자 검증
        user = User.query.filter_by(username=data['username']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'success': False, 'message': '잘못된 사용자명 또는 비밀번호입니다.'}), 401

        # 세션에 사용자 정보 저장
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin

        return jsonify({
            'success': True,
            'message': '로그인되었습니다.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# 로그아웃
@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """
    POST /api/auth/logout
    사용자 로그아웃을 처리합니다.
    """
    session.clear()
    return jsonify({'success': True, 'message': '로그아웃되었습니다.'})


# 현재 사용자 정보 조회
@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """
    GET /api/auth/me
    현재 로그인된 사용자의 정보를 반환합니다.
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'success': False, 'message': '사용자를 찾을 수 없습니다.'}), 404

    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin
        }
    })


# 관리자 권한 확인 데코레이터
from functools import wraps


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
        if not session.get('is_admin', False):
            return jsonify({'success': False, 'message': '관리자 권한이 필요합니다.'}), 403
        return f(*args, **kwargs)

    return decorated_function


# 기존의 공지사항 관련 라우트들에 admin_required 데코레이터 적용
@app.route('/api/announcements/create', methods=['POST'])
@admin_required
def create_announcement():
    try:
        data = request.form
        title = data.get('title')
        body = data.get('body')
        is_public = data.get('is_public', 'true').lower() == 'true'

        attachment = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                attachment = filename

        new_announcement = Announcement(
            title=title,
            body=body,
            attachment=attachment,
            is_public=is_public,
            author_id=session['user_id']
        )

        db.session.add(new_announcement)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '공지사항이 생성되었습니다.',
            'announcement_id': new_announcement.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)