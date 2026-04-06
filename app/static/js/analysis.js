/**
 * ASD 预测系统 - 分析任务管理（WebSocket版本）
 */

// WebSocket连接实例
let socket = null;
const taskSubscriptions = new Map();

// 初始化WebSocket连接
function initWebSocket() {
    if (socket && socket.connected) {
        return socket;
    }

    // 加载Socket.IO客户端库
    if (typeof io === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
        script.onload = () => {
            connectWebSocket();
        };
        document.head.appendChild(script);
    } else {
        connectWebSocket();
    }
}

function connectWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('✅ WebSocket已连接:', socket.id);

        // 重新订阅所有任务
        taskSubscriptions.forEach((callback, taskId) => {
            socket.emit('subscribe_task', {task_id: taskId});
        });
    });

    socket.on('disconnect', () => {
        console.log('❌ WebSocket已断开');
    });

    socket.on('connection_status', (data) => {
        console.log('连接状态:', data);
    });

    socket.on('task_update', (data) => {
        console.log('📊 任务更新:', data);
        handleTaskUpdate(data);
    });

    socket.on('task_completed', (data) => {
        console.log('✅ 任务完成:', data);
        handleTaskCompleted(data);
    });

    return socket;
}

// 处理任务进度更新
function handleTaskUpdate(data) {
    const {task_id, progress, status, message} = data;

    // 更新进度条
    updateProgressBar(task_id, progress, status, message);

    // 调用注册的回调
    if (taskSubscriptions.has(task_id)) {
        taskSubscriptions.get(task_id)(data);
    }
}

// 处理任务完成
function handleTaskCompleted(data) {
    const {task_id, result_url} = data;

    showNotification(
        '分析完成',
        '点击查看详细报告',
        'success',
        () => window.location.href = result_url
    );

    // 取消订阅
    unsubscribeTask(task_id);

    // 刷新任务列表
    setTimeout(() => location.reload(), 3000);
}

// 启动单个分析任务（WebSocket版本）
function startAnalysis(mriId, callback) {
    fetch(`/analysis/start/${mriId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.task_id) {
            console.log('🚀 任务已启动:', data.task_id);

            // 订阅任务更新
            subscribeTask(data.task_id, callback);

            showNotification(
                '任务已启动',
                '正在后台分析，请等待通知...',
                'info'
            );
        } else {
            showNotification('启动失败', data.error || '未知错误', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('错误', '网络请求失败', 'error');
    });
}

// 订阅任务更新
function subscribeTask(taskId, callback) {
    if (!socket || !socket.connected) {
        initWebSocket();
    }

    taskSubscriptions.set(taskId, callback);
    socket.emit('subscribe_task', {task_id: taskId});

    console.log(`📡 已订阅任务: ${taskId}`);
}

// 取消订阅任务
function unsubscribeTask(taskId) {
    if (socket && socket.connected) {
        socket.emit('unsubscribe_task', {task_id: taskId});
    }
    taskSubscriptions.delete(taskId);
    console.log(`🔕 已取消订阅任务: ${taskId}`);
}

// 更新进度条UI
function updateProgressBar(taskId, progress, status, message) {
    const progressBar = document.querySelector(`[data-task-id="${taskId}"] .progress-bar`);
    const statusBadge = document.querySelector(`[data-task-id="${taskId}"] .status-badge`);
    const messageText = document.querySelector(`[data-task-id="${taskId}"] .progress-message`);

    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;

        // 根据状态改变颜色
        progressBar.className = 'progress-bar ';
        if (status === 'running') {
            progressBar.classList.add('bg-primary', 'progress-bar-striped', 'progress-bar-animated');
        } else if (status === 'completed') {
            progressBar.classList.add('bg-success');
        } else if (status === 'failed') {
            progressBar.classList.add('bg-danger');
        }
    }

    if (statusBadge) {
        statusBadge.textContent = getStatusText(status);
        statusBadge.className = `badge status-badge bg-${getStatusColor(status)}`;
    }

    if (messageText) {
        messageText.textContent = message;
    }
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'pending': '等待中',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败'
    };
    return statusMap[status] || status;
}

// 获取状态颜色
function getStatusColor(status) {
    const colorMap = {
        'pending': 'secondary',
        'running': 'primary',
        'completed': 'success',
        'failed': 'danger'
    };
    return colorMap[status] || 'secondary';
}

// 批量启动分析
function startBatchAnalysis(mriIds, callback) {
    fetch('/analysis/start-batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ mri_ids: mriIds })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 订阅所有任务
            if (data.task_ids) {
                data.task_ids.forEach(taskId => {
                    subscribeTask(taskId, callback);
                });
            }

            showNotification(
                '批量分析已启动',
                `共${data.total}个任务，正在后台处理...`,
                'info'
            );
        } else {
            showNotification('批量分析失败', data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('错误', '网络请求失败', 'error');
    });
}

// 获取 CSRF Token
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

// 显示通知
function showNotification(title, message, type = 'info', onClick = null) {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.style.cursor = onClick ? 'pointer' : 'default';

    notification.innerHTML = `
        <strong>${title}</strong><br>
        ${message}
        <button type="button" class="close" data-dismiss="alert">&times;</button>
    `;

    if (onClick) {
        notification.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') {
                onClick();
            }
        });
    }

    document.body.appendChild(notification);

    // 3秒后自动关闭
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 150);
    }, 3000);
}

// 确认对话框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 页面加载时初始化WebSocket
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
});

// 导出函数
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        startAnalysis,
        startBatchAnalysis,
        subscribeTask,
        unsubscribeTask,
        showNotification,
        confirmAction
    };
}
