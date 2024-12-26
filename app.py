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

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)


class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    attachment = db.Column(db.String(255), nullable=True)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime)
    updated_at = db.Column(db.DateTime, default=datetime, onupdate=datetime)


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
@app.route('/api/announcements', methods=['POST'])
def create_announcement():
    """
    POST /api/announcements
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
@app.route('/api/announcements/<int:id>', methods=['PUT'])
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
@app.route('/api/announcements/<int:id>', methods=['DELETE'])
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


# 첨부파일 다운로드
@app.route('/api/uploads/<filename>')
def download_file(filename):
    """
    GET /api/uploads/<filename>
    첨부파일을 다운로드합니다.

    URL 파라미터:
    - filename: 다운로드할 파일의 이름

    응답 예시 (파일 다운로드):

    상태 코드:
      - 200 OK: 파일 다운로드 성공
      - 404 Not Found: 파일이 존재하지 않음
      - 500 Internal Server Error: 서버 오류 발생
    """

    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
