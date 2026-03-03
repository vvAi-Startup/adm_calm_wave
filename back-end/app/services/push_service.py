import json
from app import db
from app.models.other import Notification

class PushService:
    @staticmethod
    def send_push_notification(user_id, title, message, data_payload=None):
        """
        Simula o envio de uma notificação Push (ex: via Firebase Cloud Messaging - FCM)
        para o dispositivo móvel do usuário e salva no banco de dados.
        """
        
        # 1. Salvar no banco de dados para histórico/painel web
        new_notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type="PUSH",
            is_read=False
        )
        db.session.add(new_notification)
        db.session.commit()
        
        # 2. Mock do envio real via SDK do FCM ou similar.
        print(f"[PUSH MOCK] Enviando para User {user_id}: {title} - {message}")
        if data_payload:
            print(f"[PUSH MOCK] Payload oculto: {json.dumps(data_payload)}")
            
        return True
