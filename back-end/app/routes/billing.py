from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase

billing_bp = Blueprint('billing', __name__)


@billing_bp.route('/plan', methods=['GET'])
@jwt_required()
def get_plan_details():
    current_user_id = get_jwt_identity()
    resp = supabase.table('users').select('account_type').eq('id', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    account_type = resp.data[0]['account_type']

    if account_type == "premium":
        limits = {
            "max_audio_length_seconds": 3600,
            "max_storage_mb": 5000,
            "transcription_included": True,
        }
    else:
        limits = {
            "max_audio_length_seconds": 300,
            "max_storage_mb": 100,
            "transcription_included": False,
        }
    return jsonify({"account_type": account_type, "limits": limits})


@billing_bp.route('/upgrade', methods=['POST'])
@jwt_required()
def upgrade_plan():
    current_user_id = get_jwt_identity()
    resp = supabase.table('users').select('id').eq('id', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    data = request.get_json() or {}
    desired_plan = data.get("plan", "premium")
    if desired_plan not in ["free", "premium"]:
        return jsonify({"error": "Plano invalido."}), 400
    supabase.table('users').update({"account_type": desired_plan}).eq('id', current_user_id).execute()
    return jsonify({
        "message": f"Assinatura alterada para {desired_plan} com sucesso",
        "account_type": desired_plan,
    })
