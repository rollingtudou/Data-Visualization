from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
redis_client = FlaskRedis()
socketio = SocketIO()
jwt = JWTManager()

def create_app(config_object='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # 初始化扩展
    db.init_app(app)
    redis_client.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*')
    jwt.init_app(app)

    with app.app_context():
        # 注册蓝图
        from app.routes import main_bp
        app.register_blueprint(main_bp)

        # 创建数据库表
        db.create_all()

    return app