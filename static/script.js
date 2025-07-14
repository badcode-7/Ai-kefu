// 生成唯一的会话ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 配置
const config = {
    apiBaseUrl: window.location.origin,
    sessionId: localStorage.getItem('chat_session_id') || generateSessionId(),
    userName: '用户'
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 保存会话ID到本地存储
    localStorage.setItem('chat_session_id', config.sessionId);
    
    // 更新状态指示器
    updateStatus('connected', '已连接');
    
    // 添加欢迎消息
    addMessage('bot', '您好！我是DeepSeek AI客服助手。请问有什么可以帮您？');
    
    // 检查后端健康状态
    checkBackendHealth();
});

// 更新连接状态显示
function updateStatus(status, text) {
    const indicator = document.getElementById('status-indicator');
    const icon = indicator.querySelector('i');
    
    indicator.innerHTML = `<i class="fas fa-circle"></i> ${text}`;
    
    switch(status) {
        case 'connected':
            icon.style.color = '#38b000';
            break;
        case 'connecting':
            icon.style.color = '#ffaa00';
            break;
        case 'error':
            icon.style.color = '#e63946';
            break;
    }
}

// 检查后端健康状态
async function checkBackendHealth() {
    try {
        updateStatus('connecting', '检查服务状态...');
        const response = await fetch(`${config.apiBaseUrl}/health/detail`);
        const data = await response.json();
        
        if(data.status === 'healthy') {
            updateStatus('connected', '服务运行正常');
        } else {
            updateStatus('error', '服务异常');
        }
    } catch (error) {
        console.error('健康检查失败:', error);
        updateStatus('error', '服务连接失败');
    }
}

// 自动调整输入框高度
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

// 添加消息到聊天窗口
function addMessage(sender, content) {
    const chatContainer = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
    
    const now = new Date();
    const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span>${sender === 'user' ? config.userName : 'AI客服'}</span>
            <span>${timestamp}</span>
        </div>
        <div class="message-content">${content}</div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 显示"正在输入"指示器
function showTypingIndicator() {
    const chatContainer = document.getElementById('chat-container');
    const typingDiv = document.createElement('div');
    
    typingDiv.classList.add('message', 'bot-message');
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 隐藏"正在输入"指示器
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// 发送消息到后端
async function sendMessage() {
    const input = document.getElementById('user-input');
    const button = document.getElementById('send-button');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 禁用输入和按钮
    input.disabled = true;
    button.disabled = true;
    
    // 添加用户消息
    addMessage('user', message);
    
    // 清空输入框
    input.value = '';
    autoResize(input);
    
    // 显示"正在输入"指示器
    showTypingIndicator();
    
    try {
        // 准备请求数据
        const requestData = {
            session_id: config.sessionId,
            query: message,
            stream: false
        };
        
        // 发送请求
        const response = await fetch(`${config.apiBaseUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 添加AI回复
        addMessage('bot', data.response);
        
    } catch (error) {
        console.error('发送消息失败:', error);
        addMessage('bot', `抱歉，暂时无法处理您的请求。错误信息: ${error.message}`);
    } finally {
        // 隐藏"正在输入"指示器
        hideTypingIndicator();
        
        // 重新启用输入和按钮
        input.disabled = false;
        button.disabled = false;
        input.focus();
    }
}