from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime


app = Flask(__name__)
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
    __tablename__: str = 'announcements'
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
    if 'username' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401

    try:
        announcement = Announcement.query.get_or_404(id)
        data = request.form

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
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)