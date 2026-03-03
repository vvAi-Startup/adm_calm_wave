import os
path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/back-end/app/__init__.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = content.replace(
    'app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False',
    'from datetime import timedelta\n    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)\n    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)'
)
with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print("INIT patched")
