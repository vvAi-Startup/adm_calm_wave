import os
from supabase import create_client, Client

supabase: Client = None

def init_supabase(app=None):
    global supabase
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    if url and key:
        try:
            supabase = create_client(url, key)
            print("[supabase] Cliente inicializado com sucesso.")
        except BaseException as e:
            print(f"[supabase] Aviso: nao foi possivel inicializar cliente - {type(e).__name__}: {e}")
