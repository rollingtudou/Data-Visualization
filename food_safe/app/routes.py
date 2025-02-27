from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@jwt_required()
def index():
    return render_template('chat.html')