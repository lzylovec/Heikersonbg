// 获取DOM元素
const recordBtn = document.getElementById('recordBtn');
const clearBtn = document.getElementById('clearBtn');
const streamBtn = document.getElementById('streamBtn');
const stopStreamBtn = document.getElementById('stopStreamBtn');
const resetSessionBtn = document.getElementById('resetSessionBtn');
const stopRecordBtn = document.getElementById('stopRecordBtn');
const statusText = document.getElementById('statusText');
const statusIndicator = document.querySelector('.status-indicator');
const originalText = document.getElementById('originalText');
const translatedText = document.getElementById('translatedText');
const liveTranscript = document.getElementById('liveTranscript');
const liveIntent = document.getElementById('liveIntent');
const liveSummary = document.getElementById('liveSummary');
const loading = document.getElementById('loading');
const micLevelFill = document.getElementById('micLevelFill');
const micStateEl = document.getElementById('micState');
const micLevelText = document.getElementById('micLevelText');

let isRecording = false;
let checkResultInterval = null;
let eventSource = null;
let analysisSource = null;
let summarySource = null;
let micAudioContext = null;
let micAnalyser = null;
let micDataArray = null;
let micStream = null;
let micMonitorRAF = null;
let micMonitorActive = false;
let isStreaming = false;
let isFinishingRecording = false;

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

async function initMicMonitor() {
    try {
        try {
            micStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
        } catch (e) {
            micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }
        micAudioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = micAudioContext.createMediaStreamSource(micStream);
        micAnalyser = micAudioContext.createAnalyser();
        micAnalyser.fftSize = 2048;
        source.connect(micAnalyser);
        micDataArray = new Uint8Array(micAnalyser.fftSize);
        micMonitorActive = true;
        micStateEl.textContent = '麦克风已激活';
        updateMicLevel();
    } catch (e) {
        micStateEl.textContent = '无法访问麦克风';
    }
}

function updateMicLevel() {
    if (!micMonitorActive || !micAnalyser) return;
    micAnalyser.getByteTimeDomainData(micDataArray);
    let sum = 0;
    for (let i = 0; i < micDataArray.length; i++) {
        const v = micDataArray[i] - 128;
        sum += v * v;
    }
    const rms = Math.sqrt(sum / micDataArray.length);
    const level = Math.min(100, Math.max(0, Math.round((rms / 64) * 100)));
    micLevelFill.style.width = level + '%';
    micLevelText.textContent = level + '%';
    if (level > 12) {
        micStateEl.textContent = '检测到声音';
    } else {
        micStateEl.textContent = '静音中';
    }
    micMonitorRAF = requestAnimationFrame(updateMicLevel);
}

function stopMicMonitor() {
    micMonitorActive = false;
    if (micMonitorRAF) cancelAnimationFrame(micMonitorRAF);
    if (micStream) micStream.getTracks().forEach(t => t.stop());
    if (micAudioContext) micAudioContext.close();
}

async function ensureMicMonitor() {
    try {
        if (micAudioContext && micAnalyser && micMonitorActive) {
            try { await micAudioContext.resume(); } catch (_) {}
            micStateEl.textContent = '麦克风已激活';
            return true;
        }
        await initMicMonitor();
        if (!micMonitorActive && !['localhost','127.0.0.1'].includes(location.hostname)) {
            micStateEl.textContent = '需在本地或HTTPS启用';
        }
        return micMonitorActive;
    } catch (_) {
        return false;
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
        isStreaming = true;
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
            }
        };
        eventSource.onerror = () => {
            if (isStreaming) stableUpdateStatus('❌ 实时转写连接错误');
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
            if (isStreaming) stableUpdateStatus('❌ 实时分析连接错误');
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
            if (isStreaming) stableUpdateStatus('❌ 实时摘要连接错误');
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
        isStreaming = false;
        stableUpdateStatus('⏹️ 已停止连续转写');
    } catch (err) {
        console.error(err);
    }
}

// 开始录音
async function startRecording() {
    if (isRecording) return;
    
    isRecording = true;
    isFinishingRecording = false;
    recordBtn.classList.add('recording');
    recordBtn.querySelector('.btn-text').textContent = '正在录音...';
    stableUpdateStatus('🎤 正在准备麦克风...', true);
    
    // 清除之前的结果
    originalText.textContent = '正在听取语音...';
    translatedText.textContent = '等待AI分析...';
    
    try {
        const monitorOk = await ensureMicMonitor();
        if (!monitorOk) {
            micStateEl.textContent = '浏览器未授权';
        }
        const response = await fetch('/begin_manual_recording', {
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
        
        stableUpdateStatus('🎤 正在录音，点击结束录音', true);
        stopRecordBtn.style.display = 'inline-block';
        
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
    stopRecordBtn.style.display = 'none';
}

async function finishRecording() {
    if (isFinishingRecording) return;
    isFinishingRecording = true;
    // 先立即更新UI，避免用户感觉未结束
    stopRecordBtn.disabled = true;
    stopRecordBtn.style.display = 'none';
    isRecording = false;
    recordBtn.classList.remove('recording');
    recordBtn.querySelector('.btn-text').textContent = '开始录音';
    loading.style.display = 'block';
    stableUpdateStatus('⏹️ 已结束录音，正在识别...', true);
    try {
        const response = await fetch('/end_manual_recording', { method: 'POST' });
        const data = await response.json();
        if (data.error) {
            alert(data.error);
            return;
        }
        if (data.status === 'recognized' && data.result) {
            originalText.textContent = data.result.original_text;
            translatedText.textContent = '分析中...';
            stableUpdateStatus('🧠 已识别，正在分析...', true);
            if (checkResultInterval) { clearInterval(checkResultInterval); }
            checkResultInterval = setInterval(checkResult, 1000);
        } else if (data.status === 'completed' && data.result) {
            displayResult(data.result);
            stableUpdateStatus('✅ 分析完成！');
        }
    } catch (e) {
        console.error(e);
        stableUpdateStatus('❌ 识别失败');
    } finally {
        isFinishingRecording = false;
        stopRecordBtn.disabled = false;
    }
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
stopRecordBtn.addEventListener('click', finishRecording);
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
        // 只有在本地安全源（localhost/127.0.0.1）或用户手势后监控更可靠
        if (['localhost','127.0.0.1'].includes(location.hostname)) {
            initMicMonitor();
        }
    } else {
        updateStatus('❌ 需要麦克风权限才能使用录音功能');
        micStateEl.textContent = '浏览器未授权';
    }
});