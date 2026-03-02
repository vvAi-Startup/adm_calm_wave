from app import db
from datetime import datetime


class Audio(db.Model):
    __tablename__ = "audios"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(1000), nullable=True)
    duration_seconds = db.Column(db.Integer, default=0)
    size_bytes = db.Column(db.BigInteger, default=0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processed_path = db.Column(db.String(1000), nullable=True)
    processing_time_ms = db.Column(db.BigInteger, nullable=True)
    transcribed = db.Column(db.Boolean, default=False)
    transcription_text = db.Column(db.Text, nullable=True)
    favorite = db.Column(db.Boolean, default=False)
    playlist_id = db.Column(db.Integer, db.ForeignKey("playlists.id"), nullable=True)
    device_origin = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "duration_seconds": self.duration_seconds,
            "size_bytes": self.size_bytes,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "processed": self.processed,
            "processed_path": self.processed_path,
            "processing_time_ms": self.processing_time_ms,
            "transcribed": self.transcribed,
            "transcription_text": self.transcription_text,
            "favorite": self.favorite,
            "playlist_id": self.playlist_id,
            "device_origin": self.device_origin,
        }
