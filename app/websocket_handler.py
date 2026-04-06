from flask_socketio import SocketIO, emit
from flask import request
from threading import Lock

socketio = SocketIO(async_mode='eventlet', cors_allowed_origins="*")
task_clients = {}
lock = Lock()


def init_socketio(app):
    """初始化WebSocket"""
    socketio.init_app(app)

    @socketio.on('connect')
    def handle_connect():
        print(f'✅ 客户端已连接: {request.sid}')
        emit('connection_status', {'status': 'connected', 'sid': request.sid})

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'❌ 客户端已断开: {request.sid}')
        with lock:
            for task_id in list(task_clients.keys()):
                task_clients[task_id].discard(request.sid)
                if not task_clients[task_id]:
                    del task_clients[task_id]

    @socketio.on('subscribe_task')
    def handle_subscribe(data):
        task_id = data.get('task_id')
        if not task_id:
            return

        with lock:
            if task_id not in task_clients:
                task_clients[task_id] = set()
            task_clients[task_id].add(request.sid)

        print(f'📡 客户端 {request.sid} 订阅任务 {task_id}')
        emit('subscribed', {'task_id': task_id})

    @socketio.on('unsubscribe_task')
    def handle_unsubscribe(data):
        task_id = data.get('task_id')
        if task_id:
            with lock:
                if task_id in task_clients:
                    task_clients[task_id].discard(request.sid)
                    if not task_clients[task_id]:
                        del task_clients[task_id]
            print(f'🔕 客户端 {request.sid} 取消订阅任务 {task_id}')


def emit_task_progress(task_id, progress, status, message=None):
    """向订阅者推送任务进度"""
    data = {
        'task_id': task_id,
        'progress': progress,
        'status': status,
        'message': message or f'进度: {progress}%'
    }

    with lock:
        if task_id in task_clients:
            disconnected_clients = set()
            for sid in task_clients[task_id]:
                try:
                    socketio.emit('task_update', data, room=sid)
                except Exception as e:
                    print(f'⚠️ 推送失败 {sid}: {e}')
                    disconnected_clients.add(sid)

            for sid in disconnected_clients:
                task_clients[task_id].discard(sid)

            if not task_clients[task_id]:
                del task_clients[task_id]


def emit_task_completed(task_id, result_url):
    """推送任务完成通知"""
    emit_task_progress(task_id, 100, 'completed', '分析完成！')

    with lock:
        if task_id in task_clients:
            for sid in task_clients[task_id]:
                socketio.emit('task_completed', {
                    'task_id': task_id,
                    'result_url': result_url
                }, room=sid)


def emit_task_failed(task_id, error_message):
    """推送任务失败通知"""
    emit_task_progress(task_id, 0, 'failed', f'失败: {error_message}')
