import os
path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/back-end/app/routes/auth.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from flask_jwt_extended import create_access_token',
    'from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity'
)

content = content.replace(
    'token = create_access_token(identity=str(user.id))\n    return jsonify({"token": token, "user": user.to_dict()}), 200',
    'token = create_access_token(identity=str(user.id))\n    refresh_token = create_refresh_token(identity=str(user.id))\n    return jsonify({"token": token, "refresh_token": refresh_token, "user": user.to_dict()}), 200'
)

content = content.replace(
    'token = create_access_token(identity=str(user.id))\n    return jsonify({"token": token, "user": user.to_dict()}), 201',
    'token = create_access_token(identity=str(user.id))\n    refresh_token = create_refresh_token(identity=str(user.id))\n    return jsonify({"token": token, "refresh_token": refresh_token, "user": user.to_dict()}), 201'
)

refresh_endpoint = """
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({"token": new_access_token}), 200
"""
if "/refresh" not in content:
    content += refresh_endpoint

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("AUTH patched")
