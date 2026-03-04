from flask import Blueprint, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, UserDevice, UserAchievement
from app.models.other import Event, Statistic, Setting, Notification, Playlist, SupportTicket
from app.models.audio import Audio
import os
import json
from datetime import datetime

privacy_bp = Blueprint('privacy', __name__)

@privacy_bp.route('/export', methods=['GET'])
@jwt_required()
def export_data():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    
    data = {
        "profile": user.to_dict(),
        "devices": [d.to_dict() for d in UserDevice.query.filter_by(user_id=user.id).all()],
        "settings": [s.to_dict() for s in Setting.query.filter_by(user_id=user.id).all()],
        "achievements": [a.to_dict() for a in UserAchievement.query.filter_by(user_id=user.id).all()],
        "playlists": [p.to_dict() for p in Playlist.query.filter_by(user_id=user.id).all()],
        "audios_metadata": [a.to_dict() for a in Audio.query.filter_by(user_id=user.id).all()],
        "events_log": [e.to_dict() for e in Event.query.filter_by(user_id=user.id).all()],
        "statistics": [s.to_dict() for s in Statistic.query.filter_by(user_id=user.id).all()],
        "support_tickets": [t.to_dict() for t in SupportTicket.query.filter_by(user_id=user.id).all()],
    }
    
    return jsonify({"message": "Dados exportados", "data": data})

@privacy_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    
    # Excluir fisicamente os audios da maquina
    audios = Audio.query.filter_by(user_id=user.id).all()
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    for audio in audios:
        try:
            if audio.file_path and os.path.exists(os.path.join(upload_folder, audio.file_path)):
                os.remove(os.path.join(upload_folder, audio.file_path))
            if audio.processed_path and os.path.exists(os.path.join(upload_folder, audio.processed_path)):
                os.remove(os.path.join(upload_folder, audio.processed_path))
        except Exception as e:
            # Continue deleting from DB even if file is missing
            pass
            
        db.session.delete(audio)

    # Clean cascading tables due to privacy constraints completely
    UserDevice.query.filter_by(user_id=user.id).delete()
    UserAchievement.query.filter_by(user_id=user.id).delete()
    Setting.query.filter_by(user_id=user.id).delete()
    Notification.query.filter_by(user_id=user.id).delete()
    Event.query.filter_by(user_id=user.id).delete()
    Statistic.query.filter_by(user_id=user.id).delete()
    Playlist.query.filter_by(user_id=user.id).delete()
    SupportTicket.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"message": "Sua conta e todos os dados vinculados foram excluidos permanentemente."})
