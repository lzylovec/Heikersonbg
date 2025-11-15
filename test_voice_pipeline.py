#!/usr/bin/env python3
"""
语音识别流程验证脚本
检查语音是否真正被转换成文字
"""

import speech_recognition as sr
import time

def test_speech_to_text_pipeline():
    """测试完整的语音识别流程"""
    print("🎯 测试语音识别完整流程...")
    print("=" * 50)
    
    recognizer = sr.Recognizer()
    
    # 使用检测到的可用麦克风
    try:
        microphone = sr.Microphone(device_index=2)  # MacBook Pro麦克风
        print("✅ 麦克风初始化成功")
        
        with microphone as source:
            print("🔊 调整环境噪音...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ 环境噪音调整完成")
            
            print("\n🗣️  请清晰地说一句中文（5秒内）...")
            print("💡 例如：你好、改天一起吃饭吧、最近怎么样")
            
            # 录音
            start_time = time.time()
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=5)
            record_time = time.time() - start_time
            
            print(f"\n✅ 录音完成！")
            print(f"📊 录音时长: {record_time:.2f}秒")
            print(f"🎤 音频数据类型: {type(audio)}")
            print(f"📏 音频数据大小: {len(audio.get_raw_data()) if hasattr(audio, 'get_raw_data') else '未知'}")
            
            # 尝试多种识别方式
            print("\n🧠 开始语音识别...")
            
            # 方法1: Google语音识别
            print("1️⃣ 尝试Google语音识别...")
            try:
                text_google = recognizer.recognize_google(audio, language='zh-CN')
                print(f"✅ Google识别结果: {text_google}")
                return text_google, "Google"
            except Exception as e:
                print(f"❌ Google识别失败: {e}")
            
            # 方法2: Sphinx离线识别
            print("2️⃣ 尝试Sphinx离线识别...")
            try:
                text_sphinx = recognizer.recognize_sphinx(audio, language='zh-CN')
                print(f"✅ Sphinx识别结果: {text_sphinx}")
                return text_sphinx, "Sphinx"
            except Exception as e:
                print(f"❌ Sphinx识别失败: {e}")
            
            # 方法3: 尝试英文识别（备用）
            print("3️⃣ 尝试英文识别（备用）...")
            try:
                text_en = recognizer.recognize_google(audio, language='en-US')
                print(f"✅ 英文识别结果: {text_en}")
                return text_en, "English"
            except Exception as e:
                print(f"❌ 英文识别失败: {e}")
                
            print("\n❌ 所有识别方法都失败了")
            return None, "Failed"
            
    except Exception as e:
        print(f"❌ 麦克风初始化失败: {e}")
        return None, "MicError"

def test_with_mock_audio():
    """使用模拟音频测试"""
    print("\n🎭 使用模拟音频测试...")
    
    # 这里我们模拟一个"音频数据"
    # 在实际应用中，这会是真实的录音数据
    recognizer = sr.Recognizer()
    
    # 创建一个简单的音频数据对象（模拟）
    try:
        # 使用麦克风录制一小段静音作为测试
        with sr.Microphone(device_index=2) as source:
            print("录制测试音频...")
            audio = recognizer.record(source, duration=2)
            
            print("尝试识别测试音频...")
            try:
                text = recognizer.recognize_google(audio, language='zh-CN')
                print(f"测试结果: {text}")
            except:
                print("测试音频识别失败（预期结果，因为录制的是静音）")
                
    except Exception as e:
        print(f"模拟测试失败: {e}")

if __name__ == "__main__":
    print("🧪 语音识别流程验证工具")
    print("=" * 60)
    print("这个脚本会验证：")
    print("1. 麦克风是否真正启用")
    print("2. 语音是否被正确录制")
    print("3. 录音数据是否被转换成文字")
    print("4. 整个流程是否通畅")
    print("=" * 60)
    
    # 测试完整流程
    result_text, method = test_speech_to_text_pipeline()
    
    if result_text:
        print(f"\n🎉 测试成功！")
        print(f"📝 识别到的文字: {result_text}")
        print(f"🔧 使用的方法: {method}")
        print(f"✅ 语音确实被转换成了文字！")
        
        # 模拟发送给大模型
        print(f"\n🤖 模拟发送给大模型进行客套话分析...")
        print(f"📤 发送内容: \"{result_text}\"")
        print("✅ 流程验证完成！")
        
    else:
        print(f"\n❌ 测试失败，方法: {method}")
        print("🔧 建议检查：")
        print("   - 麦克风权限")
        print("   - 网络连接")
        print("   - 语音识别服务")
        
        # 运行模拟测试
        test_with_mock_audio()