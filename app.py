from flask import Flask, render_template, jsonify, request, Response
import json
from translator import SocialAnxietyTranslator
import threading
import time
import os

app = Flask(__name__)
translator = SocialAnxietyTranslator()

# 存储最新的翻译结果
latest_result = None
is_processing = False

@app.route('/favicon.ico')
def favicon():
    return '', 204  # 返回空响应，避免404错误

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    global latest_result, is_processing
    
    if is_processing:
        return jsonify({'error': '正在处理中，请稍候'})
    
    is_processing = True
    
    def process_audio_async():
        global latest_result, is_processing
        try:
            latest_result = {'original_text': '正在准备麦克风...', 'translation': '等待AI分析...', 'status_hint': '🎤 正在激活麦克风...'}
            def cb(msg):
                global latest_result
                base_text = (latest_result or {}).get('original_text') or '等待录音...'
                translation_hint = (latest_result or {}).get('translation') or '等待AI分析...'
                latest_result = {'original_text': base_text, 'translation': translation_hint, 'status_hint': msg}
            text = translator.speech_to_text_with_progress(cb)
            if not text:
                latest_result = {'original_text': '语音识别失败', 'translation': '请检查麦克风并重试'}
            else:
                latest_result = {'original_text': text, 'translation': '分析中...', 'status_hint': '🧠 已识别，正在分析...'}
                translation = translator.translate_politeness(text)
                latest_result = {'original_text': text, 'translation': translation}
        except Exception as e:
            latest_result = {
                'original_text': '处理出错',
                'translation': f'错误: {str(e)}'
            }
        finally:
            is_processing = False
    
    # 在新线程中处理音频，避免阻塞
    thread = threading.Thread(target=process_audio_async)
    thread.start()
    
    return jsonify({'status': '开始录音处理'})

@app.route('/get_result', methods=['GET'])
def get_result():
    global latest_result, is_processing
    
    if is_processing:
        resp = {'status': 'processing'}
        if latest_result:
            resp['result'] = latest_result
        return jsonify(resp)
    
    if latest_result:
        return jsonify({
            'status': 'completed',
            'result': latest_result
        })
    
    return jsonify({'status': 'waiting'})

@app.route('/clear_result', methods=['POST'])
def clear_result():
    global latest_result
    latest_result = None
    try:
        translator._reset_stream_state()
    except Exception:
        pass
    return jsonify({'status': 'cleared'})


@app.route('/begin_manual_recording', methods=['POST'])
def begin_manual_recording():
    global latest_result
    ok = translator.start_manual_recording()
    if ok:
        latest_result = {'original_text': '正在录音...', 'translation': '等待结束', 'status_hint': '🎤 正在录音，点击结束'}
        return jsonify({'status': 'recording_started'})
    return jsonify({'error': '无法开始录音'}), 500

@app.route('/end_manual_recording', methods=['POST'])
def end_manual_recording():
    global latest_result, is_processing
    is_processing = True
    try:
        text = translator.stop_manual_recording()
        if not text:
            latest_result = {'original_text': '识别失败', 'translation': '请重试'}
            is_processing = False
            return jsonify({'status': 'completed', 'result': latest_result})
        latest_result = {'original_text': text, 'translation': '分析中...', 'status_hint': '🧠 已识别，正在分析...'}
        def _analyze_async(t):
            global latest_result, is_processing
            try:
                translation = translator.translate_politeness(t)
                latest_result = {'original_text': t, 'translation': translation}
            except Exception as e:
                latest_result = {'original_text': t, 'translation': f'分析失败: {str(e)}'}
            finally:
                is_processing = False
        threading.Thread(target=_analyze_async, args=(text,), daemon=True).start()
        return jsonify({'status': 'recognized', 'result': latest_result})
    except Exception as e:
        is_processing = False
        return jsonify({'error': str(e)}), 500

@app.route('/start_streaming', methods=['POST'])
def start_streaming():
    ok = translator.start_streaming()
    if ok:
        return jsonify({'status': 'streaming_started'})
    return jsonify({'status': 'error'}), 500

@app.route('/stop_streaming', methods=['POST'])
def stop_streaming():
    translator.stop_streaming()
    return jsonify({'status': 'streaming_stopped'})

@app.route('/stream_transcription')
def stream_transcription():
    def generate():
        while True:
            if not translator._streaming:
                break
            try:
                seg = translator.stream_queue.get(timeout=1)
                yield f"data: {seg}\n\n"
            except Exception:
                yield f"data: \n\n"
    resp = Response(generate(), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering'] = 'no'
    return resp

@app.route('/stream_analysis')
def stream_analysis():
    def generate():
        while True:
            if not translator._streaming:
                break
            try:
                seg = translator.analysis_queue.get(timeout=1)
                payload = json.dumps({'analysis': seg})
                yield f"data: {payload}\n\n"
            except Exception:
                yield f"data: \n\n"
    resp = Response(generate(), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering'] = 'no'
    return resp

@app.route('/stream_summary')
def stream_summary():
    def generate():
        while True:
            if not translator._streaming:
                break
            try:
                seg = translator.summary_queue.get(timeout=1)
                payload = json.dumps({'summary': seg})
                yield f"data: {payload}\n\n"
            except Exception:
                yield f"data: \n\n"
    resp = Response(generate(), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering'] = 'no'
    return resp

@app.route('/reset_session', methods=['POST'])
def reset_session():
    try:
        translator.stop_streaming()
        translator._reset_stream_state()
    except Exception:
        pass
    global latest_result
    latest_result = None
    return jsonify({'status': 'reset'})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, threaded=True, host='0.0.0.0', port=8080)
