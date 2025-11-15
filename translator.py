import speech_recognition as sr
import dashscope
from dashscope import Generation
import os
from dotenv import load_dotenv
import json
import requests
from openai import OpenAI
import queue
import threading
from dashscope.audio.asr import Recognition
from http import HTTPStatus
import io
import wave
import pyaudio

load_dotenv()
api_key = os.getenv('DASHSCOPE_API_KEY')
# 配置OpenAI兼容模式
client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

dashscope.api_key = api_key

class SocialAnxietyTranslator:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # 尝试多个麦克风设备
        self.microphone = None
        self.stream_queue = queue.Queue()
        self.analysis_queue = queue.Queue()
        self.summary_queue = queue.Queue()
        self.segments_log = []
        self.analysis_log = []
        self._stop_listening = None
        self._streaming = False
        self._pa = None
        self._manual_stream = None
        self._manual_frames = []
        self._manual_recording = False
        self._manual_rate = 16000
        self._manual_channels = 1
        self._manual_chunk = 1024
        available_mics = sr.Microphone.list_microphone_names()
        print(f"可用麦克风设备: {available_mics}")
        
        # 尝试找到合适的麦克风
        for i, mic_name in enumerate(available_mics):
            try:
                print(f"尝试麦克风设备 {i}: {mic_name}")
                test_mic = sr.Microphone(device_index=i, sample_rate=16000, chunk_size=1024)
                with test_mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.microphone = test_mic
                print(f"✅ 使用麦克风设备 {i}: {mic_name}")
                break
            except Exception as e:
                print(f"❌ 设备 {i} 不可用: {e}")
                continue
        
        if self.microphone is None:
            # 使用默认麦克风
            try:
                self.microphone = sr.Microphone(sample_rate=16000, chunk_size=1024)
                print("使用默认麦克风")
            except Exception as e:
                print(f"❌ 无法初始化麦克风: {e}")
                raise Exception("无法找到可用的麦克风设备")

    

    def start_streaming(self):
        if self._streaming:
            return True
        self._reset_stream_state()
        def _callback(recognizer, audio):
            try:
                text = recognizer.recognize_google(audio, language='zh-CN')
                if text:
                    self.segments_log.append(text)
                    self.stream_queue.put(text)
                    threading.Thread(target=self._analyze_segment, args=(text,), daemon=True).start()
            except Exception:
                pass
        try:
            self._stop_listening = self.recognizer.listen_in_background(self.microphone, _callback, phrase_time_limit=5)
            self._streaming = True
            return True
        except Exception as e:
            print(f"❌ 无法启动连续转写: {e}")
            self._streaming = False
            return False

    def stop_streaming(self):
        if self._stop_listening:
            try:
                self._stop_listening(wait_for_stop=False)
            except Exception:
                pass
        self._streaming = False

    def start_manual_recording(self):
        if self._manual_recording:
            return True
        try:
            self._pa = pyaudio.PyAudio()
            _kwargs = {}
            try:
                _dev = getattr(self.microphone, 'device_index', None)
                if _dev is not None:
                    _kwargs['input_device_index'] = _dev
            except Exception:
                pass
            self._manual_stream = self._pa.open(format=pyaudio.paInt16, channels=self._manual_channels, rate=self._manual_rate, input=True, frames_per_buffer=self._manual_chunk, **_kwargs)
            self._manual_frames = []
            self._manual_recording = True
            def _capture():
                while self._manual_recording:
                    try:
                        data = self._manual_stream.read(self._manual_chunk, exception_on_overflow=False)
                        self._manual_frames.append(data)
                    except Exception:
                        break
            threading.Thread(target=_capture, daemon=True).start()
            return True
        except Exception as e:
            print(f"❌ 无法开始手动录音: {e}")
            self._manual_recording = False
            return False

    def stop_manual_recording(self):
        if not self._manual_recording and not self._manual_frames:
            return None
        try:
            self._manual_recording = False
            try:
                if self._manual_stream:
                    self._manual_stream.stop_stream()
                    self._manual_stream.close()
            except Exception:
                pass
            try:
                if self._pa:
                    self._pa.terminate()
            except Exception:
                pass
            pcm = b''.join(self._manual_frames)
            self._manual_frames = []
            buf = io.BytesIO()
            wf = wave.open(buf, 'wb')
            wf.setnchannels(self._manual_channels)
            wf.setsampwidth(2)
            wf.setframerate(self._manual_rate)
            wf.writeframes(pcm)
            wf.close()
            buf.seek(0)
            with sr.AudioFile(buf) as source:
                audio = self.recognizer.record(source)
            try:
                text = self.recognizer.recognize_google(audio, language='zh-CN')
                return text
            except Exception:
                try:
                    text = self.recognizer.recognize_sphinx(audio, language='zh-CN')
                    return text
                except Exception:
                    pass
            return None
        except Exception as e:
            print(f"❌ 手动录音处理失败: {e}")
            return None

    def _reset_stream_state(self):
        try:
            while True:
                self.stream_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            while True:
                self.analysis_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            while True:
                self.summary_queue.get_nowait()
        except queue.Empty:
            pass
        self.segments_log.clear()
        self.analysis_log.clear()

    def _analyze_segment(self, text):
        try:
            print(f"分析分句: {text}")
            completion = client.chat.completions.create(
                model="qwen3-max",
                messages=[
                    {"role": "system", "content": "你是一个社交意图分析专家，识别中文客套话并给出真实意图与建议回应"},
                    {"role": "user", "content": f"文本：{text}\n请输出：类型、真实意图、建议回应"}
                ],
                stream=False,
                temperature=0.2
            )
            result = completion.choices[0].message.content
            self.analysis_log.append(result)
            self.analysis_queue.put(result)
            threading.Thread(target=self._update_summary, daemon=True).start()
        except Exception as e:
            print(f"AI分析失败: {e}")
            try:
                response = Generation.call(
                    model='qwen-turbo',
                    prompt=f"请分析是否为客套话，并给出真实意图与建议回应：{text}",
                    stream=False,
                    temperature=0.2
                )
                if hasattr(response, 'status_code') and response.status_code == 200:
                    self.analysis_log.append(response.output.text)
                    self.analysis_queue.put(response.output.text)
                    threading.Thread(target=self._update_summary, daemon=True).start()
                else:
                    self.analysis_queue.put(f"分析失败: {getattr(response, 'message', 'unknown error')}")
            except Exception as e2:
                self.analysis_queue.put(f"分析失败: {e2}")

    def _update_summary(self):
        try:
            last_segments = self.segments_log[-5:]
            last_analyses = self.analysis_log[-5:]
            content = "\n".join([f"- 语句: {s}" for s in last_segments]) + "\n" + \
                      "\n".join([f"- 分析: {a}" for a in last_analyses])
            completion = client.chat.completions.create(
                model="qwen3-max",
                messages=[
                    {"role": "system", "content": "你是摘要助手，请将最近语句与分析总结为简洁中文要点，突出真实意图与互动建议"},
                    {"role": "user", "content": f"请基于以下内容生成不超过5条的要点摘要：\n{content}"}
                ],
                stream=False,
                temperature=0.2
            )
            summary = completion.choices[0].message.content
            self.summary_queue.put(summary)
        except Exception as e:
            try:
                response = Generation.call(
                    model='qwen-turbo',
                    prompt=f"请对以下内容生成简洁要点摘要：\n{content}",
                    stream=False,
                    temperature=0.2
                )
                if hasattr(response, 'status_code') and response.status_code == 200:
                    self.summary_queue.put(response.output.text)
                else:
                    self.summary_queue.put(f"摘要失败: {getattr(response, 'message', 'unknown error')}")
            except Exception as e2:
                self.summary_queue.put(f"摘要失败: {e2}")
        
    def speech_to_text(self):
        """将语音转换为文本"""
        if self.microphone is None:
            print("❌ 麦克风未初始化")
            return None
            
        try:
            print("🎤 正在激活麦克风...")
            
            # 重新检查麦克风状态
            with self.microphone as source:
                print("✅ 麦克风已激活")
                print("🎤 请说话...（最多10秒）")
                
                # 调整环境噪音
                print("🔊 调整环境噪音...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("✅ 环境噪音调整完成")
                
                # 监听语音 - 关键步骤！
                print("👂 正在监听语音，请说话...")
                print("💡 提示：当麦克风真正启用时，这里会显示录音状态")
                
                # 使用更长的超时时间和更敏感的检测
                audio = self.recognizer.listen(
                    source, 
                    timeout=15,  # 更长的超时时间
                    phrase_time_limit=10  # 短语时间限制
                )
                print("✅ 录音完成！检测到语音输入")
                
        except sr.WaitTimeoutError:
            print("❌ 等待超时，未检测到语音输入")
            print("💡 可能原因：")
            print("   - 麦克风权限未开启")
            print("   - 麦克风硬件问题")
            print("   - 环境太安静或声音太小")
            return None
        except Exception as e:
            print(f"❌ 录音过程出错: {e}")
            print(f"错误类型: {type(e).__name__}")
            return None
            
        try:
            print("🧠 正在识别语音...")
            text = self.recognizer.recognize_google(audio, language='zh-CN')
            print(f"🎯 识别到的文本: {text}")
            return text
        except sr.UnknownValueError:
            print("❌ 无法识别语音内容")
            print("🔄 尝试备用识别引擎...")
            try:
                text = self.recognizer.recognize_sphinx(audio, language='zh-CN')
                print(f"🎯 Sphinx识别结果: {text}")
                return text
            except Exception as sphinx_e:
                print(f"❌ 备用识别也失败: {sphinx_e}")
                return None
        except sr.RequestError as e:
            print(f"❌ 语音识别服务错误: {e}")
            print("💡 请检查网络连接")
            return None
        
    def translate_politeness(self, text):
        """使用大模型判断是否为客套话并翻译真实意图"""
        if not text:
            return None
            
        prompt = f"""
        你是一个社交意图分析专家。请分析以下中文文本，判断说话者是否在说客套话，
        并给出其真实意图。如果是客套话，请直接翻译出真实含义；如果不是客套话，
        请说明这是真诚的表达。
        
        文本: "{text}"
        
        请按照以下格式回复：
        分析: [简要分析]
        类型: [客套话/真诚表达]
        真实意图: [翻译后的真实含义，如果是客套话]
        建议回应: [给社恐人士的建议回应]
        """
        
        try:
            # 使用OpenAI兼容模式调用qwen3-max
            print(f"🤖 正在调用qwen3-max模型分析文本: {text}")
            
            completion = client.chat.completions.create(
                model="qwen3-max",
                messages=[
                    {"role": "system", "content": "你是一个专业的社交意图分析专家，擅长识别中文客套话和分析真实意图。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                temperature=0.7
            )
            
            result = completion.choices[0].message.content
            print(f"✅ AI分析结果: {result}")
            return result
            
        except Exception as e:
            print(f"❌ 调用大模型API时出错: {e}")
            print("🔄 尝试使用备用方法...")
            
            # 备用方法：使用原来的dashscope方法
            try:
                response = Generation.call(
                    model='qwen-turbo',
                    prompt=prompt,
                    stream=False,
                    temperature=0.7
                )
                
                if response.status_code == 200:
                    result = response.output.text
                    print(f"✅ 备用方法成功: {result}")
                    return result
                else:
                    print(f"❌ 备用方法也失败: {response.status_code}")
                    return None
                    
            except Exception as e2:
                print(f"❌ 所有方法都失败: {e2}")
                return None
        
    def process_audio(self):
        """完整的语音处理流程"""
        print("=== 社恐翻译器启动 ===")
        
        # 语音识别
        text = self.speech_to_text()
        if not text:
            return None
        
        # AI翻译
        translation = self.translate_politeness(text)
        return {
            'original_text': text,
            'translation': translation
        }

    def speech_to_text_with_progress(self, on_status, max_attempts=3):
        if self.microphone is None:
            return None
        for attempt in range(1, max_attempts + 1):
            try:
                on_status('🎤 正在激活麦克风...')
                with self.microphone as source:
                    on_status('✅ 麦克风已激活')
                    on_status('🔊 正在校准环境噪音...')
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                    self.recognizer.dynamic_energy_threshold = True
                    self.recognizer.pause_threshold = 0.5
                    self.recognizer.non_speaking_duration = 0.15
                    on_status(f'🎤 麦克风就绪（第{attempt}次），请开始说话')
                    audio = self.recognizer.listen(
                        source,
                        timeout=15,
                        phrase_time_limit=8
                    )
                    on_status('⏹️ 录音完成，正在识别...')
            except sr.WaitTimeoutError:
                on_status(f'❌ 未检测到语音（第{attempt}次），正在重试')
                continue
            except Exception:
                on_status(f'❌ 录音出错（第{attempt}次），正在重试')
                continue
            # 识别阶段
            try:
                on_status('🧠 正在识别语音...')
                result = self.recognizer.recognize_google(audio, language='zh-CN', show_all=True)
                if isinstance(result, dict) and 'alternative' in result and len(result['alternative']) > 0:
                    text = result['alternative'][0].get('transcript', '')
                else:
                    text = result if isinstance(result, str) else ''
                if text and text.strip():
                    on_status('✅ 已识别，正在分析...')
                    return text.strip()
                else:
                    raise sr.UnknownValueError()
            except sr.UnknownValueError:
                on_status(f'❌ 无法识别（第{attempt}次），尝试备用识别')
                try:
                    text = self.recognizer.recognize_sphinx(audio, language='zh-CN')
                    if text and text.strip():
                        on_status('✅ 已识别，正在分析...')
                        return text.strip()
                except Exception:
                    pass
                try:
                    wav_path = "/tmp/social_anxiety_input.wav"
                    wav_data = audio.get_wav_data(convert_rate=16000, convert_width=2)
                    with open(wav_path, "wb") as f:
                        f.write(wav_data)
                    recognition = Recognition(model='paraformer-realtime-v2', format='wav', sample_rate=16000, language_hints=['zh'], callback=None)
                    result = recognition.call(wav_path)
                    if result.status_code == HTTPStatus.OK:
                        sentences = result.get_sentence()
                        joined = "".join([s.get('text') if isinstance(s, dict) else str(s) for s in sentences])
                        if joined.strip():
                            on_status('✅ 已识别，正在分析...')
                            return joined.strip()
                except Exception:
                    pass
                on_status(f'❌ 识别失败（第{attempt}次）')
                continue
            except sr.RequestError:
                on_status(f'❌ 语音识别服务错误（第{attempt}次）')
                continue
        on_status('❌ 多次尝试仍未识别，请检查麦克风并重试')
        return None

if __name__ == "__main__":
    translator = SocialAnxietyTranslator()
    result = translator.process_audio()
    
    if result:
        print("\n=== 最终结果 ===")
        print(f"原话: {result['original_text']}")
        print(f"翻译: {result['translation']}")
    else:
        print("处理失败")