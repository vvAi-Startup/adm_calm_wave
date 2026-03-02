import sys

c = open('c:/Users/fatec-dsm6/Desktop/adm_calm_wave/back-end/app/routes/auth.py', 'rb').read()
c = c.replace(
    b'data = request.get_json()\r\n    required = ["name", "email", "password"]\r\n    if not data or not all(k in data for k in required):\r\n        return jsonify({"error": "Nome, email e senha s\xc3\xa3o obrigat\xc3\xb3rios"}), 400',
    b'try:\r\n        data = RegisterSchema().load(request.get_json() or {})\r\n    except ValidationError as err:\r\n        return jsonify({"error": "Parametros invalidos", "messages": err.messages}), 400'
)
open('c:/Users/fatec-dsm6/Desktop/adm_calm_wave/back-end/app/routes/auth.py', 'wb').write(c)
print('OK')
