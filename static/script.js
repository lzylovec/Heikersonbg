// 获取DOM元素
const recordBtn = document.getElementById('recordBtn');
const clearBtn = document.getElementById('clearBtn');
const streamBtn = document.getElementById('streamBtn');
const stopStreamBtn = document.getElementById('stopStreamBtn');
const resetSessionBtn = document.getElementById('resetSessionBtn');
const statusText = document.getElementById('statusText');
const statusIndicator = document.querySelector('.status-indicator');
const originalText = document.getElementById('originalText');
const translatedText = document.getElementById('translatedText');
const liveTranscript = document.getElementById('liveTranscript');
const liveIntent = document.getElementById('liveIntent');
const liveSummary = document.getElementById('liveSummary');
const loading = document.getElementById('loading');

let isRecording = false;
let checkResultInterval = null;
let eventSource = null;
let analysisSource = null;
let summarySource = null;

// 更新状态显示
function updateStatus(text, processing = false) {
    statusText.textContent = text;
    if (processing) {
        statusIndicator.classList.add('processing');
        statusIndicator.style.background = '#f39c12';
    } else {
        statusIndicator.classList.remove('processing');
        statusIndicator.style.background = '#2ecc71';
    }
}

let lastStatusText = '';
let lastStatusTime = 0;
const STATUS_COOLDOWN_MS = 2000;
function stableUpdateStatus(text, processing = false) {
    const now = Date.now();
    if (text === lastStatusText) {
        updateStatus(text, processing);
        lastStatusTime = now;
        return;
    }
    if (now - lastStatusTime < STATUS_COOLDOWN_MS) {
        return;
    }
    updateStatus(text, processing);
    lastStatusText = text;
    lastStatusTime = now;
}

// 显示结果
function displayResult(result) {
    originalText.textContent = result.original_text;
    translatedText.textContent = result.translation;
    
    // 添加淡入动画
    originalText.parentElement.classList.add('fade-in');
    translatedText.parentElement.classList.add('fade-in');
    
    setTimeout(() => {
        originalText.parentElement.classList.remove('fade-in');
        translatedText.parentElement.classList.remove('fade-in');
    }, 500);
}

// 清除结果
function clearResults() {
    originalText.textContent = '等待录音...';
    translatedText.textContent = '翻译结果将在这里显示';
    liveTranscript.textContent = '连接后开始显示实时转写...';
    liveIntent.textContent = '连接后显示每句的AI分析...';
    liveSummary.textContent = '连接后显示多句聚合的实时摘要...';
    stableUpdateStatus('准备就绪，点击录音按钮开始');
    
    // 停止检查结果
    if (checkResultInterval) {
        clearInterval(checkResultInterval);
        checkResultInterval = null;
    }
}

// 开始连续转写
async function startStreaming() {
    try {
        const res = await fetch('/start_streaming', { method: 'POST' });
        const data = await res.json();
        if (data.status !== 'streaming_started') {
            alert('启动连续转写失败');
            return;
        }
        stableUpdateStatus('📡 已启动连续转写...', true);
        liveTranscript.textContent = '';
        stopStreamBtn.style.display = 'inline-block';
        liveIntent.textContent = '';
        liveSummary.textContent = '';
        if (eventSource) {
            eventSource.close();
        }
        eventSource = new EventSource('/stream_transcription');
        eventSource.onmessage = (e) => {
            if (e.data && e.data.trim().length > 0) {
                liveTranscript.textContent += e.data + '\n';
                originalText.textContent = e.data;
            }
        };
        eventSource.onerror = () => {
            stableUpdateStatus('❌ 实时转写连接错误');
        };

        // 分析流
        if (analysisSource) {
            analysisSource.close();
        }
        analysisSource = new EventSource('/stream_analysis');
        analysisSource.onmessage = (e) => {
            if (e.data && e.data.trim().length > 0) {
                let text = e.data;
                try {
                    const obj = JSON.parse(e.data);
                    text = obj.analysis || e.data;
                } catch (_) {}
                liveIntent.textContent += text + '\n';
            }
        };
        analysisSource.onerror = () => {
            stableUpdateStatus('❌ 实时分析连接错误');
        };

        // 摘要流
        if (summarySource) {
            summarySource.close();
        }
        summarySource = new EventSource('/stream_summary');
        summarySource.onmessage = (e) => {
            if (e.data && e.data.trim().length > 0) {
                let text = e.data;
                try {
                    const obj = JSON.parse(e.data);
                    text = obj.summary || e.data;
                } catch (_) {}
                liveSummary.textContent = text;
            }
        };
        summarySource.onerror = () => {
            stableUpdateStatus('❌ 实时摘要连接错误');
        };
    } catch (err) {
        console.error(err);
        updateStatus('❌ 启动失败');
    }
}

// 停止连续转写
async function stopStreaming() {
    try {
        await fetch('/stop_streaming', { method: 'POST' });
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        if (analysisSource) {
            analysisSource.close();
            analysisSource = null;
        }
        if (summarySource) {
            summarySource.close();
            summarySource = null;
        }
        stopStreamBtn.style.display = 'none';
        stableUpdateStatus('⏹️ 已停止连续转写');
    } catch (err) {
        console.error(err);
    }
}

// 开始录音
async function startRecording() {
    if (isRecording) return;
    
    isRecording = true;
    recordBtn.classList.add('recording');
    recordBtn.querySelector('.btn-text').textContent = '正在录音...';
    stableUpdateStatus('🎤 正在准备麦克风...', true);
    
    // 清除之前的结果
    originalText.textContent = '正在听取语音...';
    translatedText.textContent = '等待AI分析...';
    
    try {
        // 发送开始录音请求
        const response = await fetch('/start_recording', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            stopRecording();
            return;
        }
        
        stableUpdateStatus('🔄 正在处理录音，请稍候...', true);
        loading.style.display = 'block';
        
        // 开始定期检查结果
        checkResultInterval = setInterval(checkResult, 1000);
        
    } catch (error) {
        console.error('录音失败:', error);
        alert('录音失败，请重试');
        stopRecording();
    }
}

// 停止录音状态
function stopRecording() {
    isRecording = false;
    recordBtn.classList.remove('recording');
    recordBtn.querySelector('.btn-text').textContent = '开始录音';
    loading.style.display = 'none';
}

// 检查结果
async function checkResult() {
    try {
        const response = await fetch('/get_result');
        const data = await response.json();
        
        if (data.status === 'completed' && data.result) {
            // 结果显示完成
            displayResult(data.result);
            stableUpdateStatus('✅ 分析完成！');
            stopRecording();
            
            // 停止检查
            if (checkResultInterval) {
                clearInterval(checkResultInterval);
                checkResultInterval = null;
            }
        } else if (data.status === 'processing') {
            stableUpdateStatus('正在分析中...', true);
            if (data.result && data.result.original_text) {
                originalText.textContent = data.result.original_text;
            }
            if (data.result && data.result.status_hint) {
                stableUpdateStatus(data.result.status_hint, true);
            }
        } else if (data.status === 'waiting') {
            stableUpdateStatus('等待处理结果...', true);
        }
        
    } catch (error) {
        console.error('获取结果失败:', error);
        stableUpdateStatus('获取结果失败');
        stopRecording();
        
        if (checkResultInterval) {
            clearInterval(checkResultInterval);
            checkResultInterval = null;
        }
    }
}

// 清除结果
async function clearResult() {
    try {
        await fetch('/clear_result', {
            method: 'POST'
        });
        clearResults();
    } catch (error) {
        console.error('清除失败:', error);
    }
}

// 事件监听器
recordBtn.addEventListener('click', startRecording);
clearBtn.addEventListener('click', clearResult);
streamBtn.addEventListener('click', startStreaming);
stopStreamBtn.addEventListener('click', stopStreaming);
resetSessionBtn.addEventListener('click', async () => {
    try {
        if (eventSource) { eventSource.close(); eventSource = null; }
        if (analysisSource) { analysisSource.close(); analysisSource = null; }
        if (summarySource) { summarySource.close(); summarySource = null; }
        await fetch('/reset_session', { method: 'POST' });
        stopStreamBtn.style.display = 'none';
        window.location.reload();
    } catch (err) {
        console.error(err);
    }
});

// 键盘快捷键
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !isRecording) {
        e.preventDefault();
        startRecording();
    } else if (e.code === 'Escape' && isRecording) {
        e.preventDefault();
        stopRecording();
    }
});

// 检查浏览器麦克风权限
async function checkMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        console.log('✅ 浏览器麦克风权限已获得');
        return true;
    } catch (error) {
        console.error('❌ 浏览器麦克风权限被拒绝:', error);
        updateStatus('❌ 浏览器麦克风权限被拒绝，请在浏览器设置中允许麦克风访问');
        return false;
    }
}

// 页面加载完成提示
window.addEventListener('load', async () => {
    updateStatus('正在检查麦克风权限...');
    
    const hasPermission = await checkMicrophonePermission();
    
    if (hasPermission) {
        setTimeout(() => {
            updateStatus('✅ 准备就绪！点击录音按钮或按空格键开始');
        }, 1000);
    } else {
        updateStatus('❌ 需要麦克风权限才能使用录音功能');
    }
});
        if (analysisSource) {
            analysisSource.close();
        }
        analysisSource = new EventSource('/stream_analysis');
        analysisSource.onmessage = (e) => {
            if (e.data && e.data.trim().length > 0) {
                liveIntent.textContent += e.data + '\n';
            }
        };
        analysisSource.onerror = () => {
            updateStatus('❌ 实时分析连接错误');
        };