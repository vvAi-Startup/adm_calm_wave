from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    profile_photo_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_access = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    account_type = db.Column(db.String(50), default="free")  # free, premium
    role = db.Column(db.String(50), default="user") # user, admin, super_admin

    # Settings
    dark_mode = db.Column(db.Boolean, default=False)
    notifications_enabled = db.Column(db.Boolean, default=True)
    auto_process_audio = db.Column(db.Boolean, default=True)
    audio_quality = db.Column(db.String(20), default="high") # low, normal, high

    audios = db.relationship("Audio", backref="user", lazy=True)
    playlists = db.relationship("Playlist", backref="user", lazy=True)
    devices = db.relationship("UserDevice", backref="user", lazy=True)
    achievements = db.relationship("UserAchievement", backref="user", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "profile_photo_url": self.profile_photo_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_access": self.last_access.isoformat() if self.last_access else None,
            "active": self.active,
            "account_type": self.account_type,
            "role": self.role,
            "settings": {
                "dark_mode": self.dark_mode,
                "notifications_enabled": self.notifications_enabled,
                "auto_process_audio": self.auto_process_audio,
                "audio_quality": self.audio_quality,
            }
        }

class UserDevice(db.Model):
    __tablename__ = "user_devices"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    device_name = db.Column(db.String(255), nullable=False)
    device_type = db.Column(db.String(100), nullable=True) # Mobile, Browser, etc
    ip_address = db.Column(db.String(50), nullable=True)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_current = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "ip_address": self.ip_address,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "is_current": self.is_current
        }

class UserAchievement(db.Model):
    __tablename__ = "user_achievements"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    achievement_id = db.Column(db.Integer, nullable=False) # 1: First Audio, 2: 10 Audios, etc
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "achievement_id": self.achievement_id,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None
        }
