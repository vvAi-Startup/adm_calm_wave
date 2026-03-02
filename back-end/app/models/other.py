from app import db
from datetime import datetime


class Playlist(db.Model):
    __tablename__ = "playlists"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    color = db.Column(db.String(20), default="#6FAF9E")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.Column(db.Integer, default=0)

    audios = db.relationship("Audio", backref="playlist", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_audios": len(self.audios),
            "order": self.order,
        }


class Statistic(db.Model):
    __tablename__ = "statistics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_recordings = db.Column(db.Integer, default=0)
    total_recorded_seconds = db.Column(db.Integer, default=0)
    total_processing_ms = db.Column(db.BigInteger, default=0)
    audios_transcribed = db.Column(db.Integer, default=0)
    total_app_usage_seconds = db.Column(db.Integer, default=0)
    playlists_created = db.Column(db.Integer, default=0)
    audios_deleted = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat() if self.date else None,
            "total_recordings": self.total_recordings,
            "total_recorded_seconds": self.total_recorded_seconds,
            "total_processing_ms": self.total_processing_ms,
            "audios_transcribed": self.audios_transcribed,
            "total_app_usage_seconds": self.total_app_usage_seconds,
            "playlists_created": self.playlists_created,
            "audios_deleted": self.audios_deleted,
        }


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    event_type = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    details_json = db.Column(db.Text, nullable=True)
    screen = db.Column(db.String(100), nullable=True)
    level = db.Column(db.String(20), default="info")  # info, warning, error

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "details_json": self.details_json,
            "screen": self.screen,
            "level": self.level,
        }


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True) # If null, system-wide for admin
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default="info") # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
