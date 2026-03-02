import re
with open('c:/Users/fatec-dsm6/Desktop/adm_calm_wave/web/app/analytics/page.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

replacements = {
    'AvanÃ§ado': 'Avançado',
    'mÃªs': 'mês',
    'Total Ã\\x81udios': 'Total Áudios',
    'Total Ãudios': 'Total Áudios',
    'UsuÃ¡rios': 'Usuários',
    'usuÃ¡rios': 'usuários',
    'Ãšltimos': 'Últimos',
    'â†‘': '↑',
    'ðŸ‘¥': '👥',
    'â±ï¸': '⏱️',
    'ðŸ“‰': '📉',
    'ðŸŽ™ï¸': '🎙️',
    'RetenÃ§Ã£o': 'Retenção',
    'SaudÃ¡vel': 'Saudável',
    'DemogrÃ¡fica': 'Demográfica'
}

for k, v in replacements.items():
    c = c.replace(k, v)
    
# Deal with the title just in case it's missed due to the weird space char
c = re.sub(r'Total Ã.*udios', 'Total Áudios', c)

with open('c:/Users/fatec-dsm6/Desktop/adm_calm_wave/web/app/analytics/page.tsx', 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
