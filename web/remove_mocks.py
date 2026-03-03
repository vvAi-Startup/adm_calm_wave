import re

files_with_mock = [
    r"c:\Users\fatec-dsm6\Desktop\adm_calm_wave\web\app\users\page.tsx",
    r"c:\Users\fatec-dsm6\Desktop\adm_calm_wave\web\app\audios\page.tsx",
    r"c:\Users\fatec-dsm6\Desktop\adm_calm_wave\web\app\logs\page.tsx",
]

for filepath in files_with_mock:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove the mock fallback block
    # For example: 
    # if (res.users.length === 0) { ... } else { setUsers(res.users); ... }
    # Will be replaced with direct setting
    
    if "users" in filepath:
        content = re.sub(
            r"if\s*\(res.users\.length\s*===\s*0\)\s*\{[^\}]+\}\s*else\s*\{([^\}]+)\}",
            r"\1", 
            content,
            flags=re.DOTALL
        )
    elif "audios" in filepath:
        content = re.sub(
            r"if\s*\(res.audios\.length\s*===\s*0\)\s*\{[^\}]+\}\s*else\s*\{([^\}]+)\}",
            r"\1", 
            content,
            flags=re.DOTALL
        )
    elif "logs" in filepath:
        content = re.sub(
            r"if\s*\(res.events\.length\s*===\s*0\)\s*\{[^\}]+\}\s*else\s*\{([^\}]+)\}",
            r"\1", 
            content,
            flags=re.DOTALL
        )
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Mock usages removed successfully")
