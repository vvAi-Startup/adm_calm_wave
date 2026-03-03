import os
path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/web/app/layout.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'import "./globals.css";',
    'import { Toaster } from "react-hot-toast";\nimport "./globals.css";'
)
content = content.replace(
    '<AuthProvider>',
    '<AuthProvider>\n          <Toaster position="top-right" />'
)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Layout patched")
