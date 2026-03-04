from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/plan', methods=['GET'])
@jwt_required()
def get_plan_details():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    
    # Simulação de limites baseados em account_type
    if user.account_type == "premium":
        limits = {
            "max_audio_length_seconds": 3600, # 1 hr
            "max_storage_mb": 5000,
            "transcription_included": True
        }
    else: # free
        limits = {
            "max_audio_length_seconds": 300, # 5 min
            "max_storage_mb": 100,
            "transcription_included": False
        }
    
    return jsonify({
        "account_type": user.account_type,
        "limits": limits
    })

@billing_bp.route('/upgrade', methods=['POST'])
@jwt_required()
def upgrade_plan():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    data = request.get_json() or {}
    
    desired_plan = data.get("plan", "premium")
    if desired_plan not in ["free", "premium"]:
        return jsonify({"error": "Plano invalido."}), 400
        
    user.account_type = desired_plan
    db.session.commit()
    
    return jsonify({"message": f"Assinatura alterada para {desired_plan} com sucesso", "account_type": user.account_type})
