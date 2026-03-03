import os
path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/web/app/lib/api.ts'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'import toast from "react-hot-toast";' not in content:
    content = 'import toast from "react-hot-toast";\n' + content
    
content = content.replace(
    'const res = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers });',
    'let res; try { res = await fetch(`${BASE_URL}${endpoint}`, { ...options, headers }); } catch (error) { toast.error("Falha de conexão com o servidor. Verifique sua internet ou tente mais tarde."); throw error; }'
)
content = content.replace(
    'const res = await fetch(`${BASE_URL}/api/audios/upload`, {',
    'let res; try { res = await fetch(`${BASE_URL}/api/audios/upload`, {'
)
content = content.replace(
    'body: formData,\n    });',
    'body: formData,\n    }); } catch (error) { toast.error("Falha de conexão com o servidor."); throw error; }'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("API patched")
