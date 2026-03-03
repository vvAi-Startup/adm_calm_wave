import os
path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/back-end/app/routes/audios.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add socketio import
text = text.replace(
    'from app import db',
    'from app import db, socketio'
)

# Emit event when audio finishes processing
old_log = 'print(f"Audio processed successfully in {audio.processing_time_ms}ms")'
new_log = 'print(f"Audio processed successfully in {audio.processing_time_ms}ms")\n            # Emit websocket event\n            socketio.emit("audio_completed", {"audio_id": audio.id, "filename": audio.filename, "message": "Processamento concluído!"}, namespace="/")'

text = text.replace(old_log, new_log)

# Protect upload size limit
text = text.replace(
    'if file.filename == \'\':\n        return jsonify({"error": "Nome de arquivo vazio"}), 400',
    'if file.filename == \'\':\n        return jsonify({"error": "Nome de arquivo vazio"}), 400\n\n    # Security check: limit upload size and content if needed. (Already limited by app config generally, but we can enforce audio extension)\n    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".aac")):\n        return jsonify({"error": "Formato não suportado."}), 400\n'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Websocket event patched")
