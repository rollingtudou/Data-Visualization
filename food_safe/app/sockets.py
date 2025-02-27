from flask import current_app
from flask_socketio import emit
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio, db, redis_client
from app.models import ChatMessage, User
import requests
import json

@socketio.on('connect')
@jwt_required()
def handle_connect():
    user_id = get_jwt_identity()
    redis_client.sadd(f'online_users', user_id)
    emit('user_connected', {'user_id': user_id}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    user_id = get_jwt_identity()
    redis_client.srem(f'online_users', user_id)
    emit('user_disconnected', {'user_id': user_id}, broadcast=True)

@socketio.on('user_message')
@jwt_required()
def handle_message(data):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        emit('error', {'message': '用户未找到'})
        return

    message_content = data.get('message')
    model_name = data.get('model_name', 'default')
    session_id = data.get('session_id')

    # 保存用户消息
    user_message = ChatMessage(
        content=message_content,
        user_id=user_id,
        is_bot=False,
        model_name=model_name,
        session_id=session_id
    )
    db.session.add(user_message)
    db.session.commit()

    # 调用模型API
    try:
        response = requests.post(
            current_app.config['MODEL_API_URL'],
            json={
                "prompt": message_content,
                "model": model_name,
                "session_id": session_id
            },
            headers={"Authorization": f"Bearer {current_app.config['MODEL_API_KEY']}"}
        )
        bot_response = response.json()['result']

        # 保存机器人回复
        bot_message = ChatMessage(
            content=bot_response,
            user_id=user_id,
            is_bot=True,
            model_name=model_name,
            session_id=session_id
        )
        db.session.add(bot_message)
        db.session.commit()

        # 广播消息给所有用户
        emit('bot_response', {
            'content': bot_response,
            'user_id': user_id,
            'session_id': session_id,
            'timestamp': bot_message.timestamp.isoformat()
        }, room=session_id)

    except Exception as e:
        emit('error', {'message': f'API调用失败: {str(e)}'})

@socketio.on('join_session')
@jwt_required()
def handle_join_session(data):
    session_id = data.get('session_id')
    if session_id:
        socketio.join_room(session_id)
        emit('session_joined', {'session_id': session_id})

@socketio.on('leave_session')
@jwt_required()
def handle_leave_session(data):
    session_id = data.get('session_id')
    if session_id:
        socketio.leave_room(session_id)
        emit('session_left', {'session_id': session_id})