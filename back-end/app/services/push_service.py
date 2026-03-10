import json
from app.supabase_ext import supabase


class PushService:
    @staticmethod
    def send_push_notification(user_id, title, message, data_payload=None):
        """
        Simula envio de notificacao Push e salva no Supabase.
        """
        try:
            supabase.table('notifications').insert({
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": "PUSH",
                "is_read": False,
            }).execute()
        except Exception as e:
            print(f"[PUSH] Erro ao salvar notificacao: {e}")

        print(f"[PUSH MOCK] Enviando para User {user_id}: {title} - {message}")
        if data_payload:
            print(f"[PUSH MOCK] Payload: {json.dumps(data_payload)}")
        return True
