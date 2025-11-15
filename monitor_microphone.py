#!/usr/bin/env python3
"""
实时麦克风状态监控脚本
用于调试Web应用的麦克风功能
"""

import speech_recognition as sr
import time
import threading

def monitor_microphone():
    """实时监控麦克风状态"""
    print("🔍 开始监控麦克风状态...")
    
    recognizer = sr.Recognizer()
    
    # 获取可用麦克风列表
    mic_list = sr.Microphone.list_microphone_names()
    print(f"📋 可用麦克风设备: {mic_list}")
    
    # 尝试使用MacBook Pro麦克风（设备索引2）
    device_index = 2
    if device_index < len(mic_list):
        try:
            print(f"🎯 尝试使用设备 {device_index}: {mic_list[device_index]}")
            microphone = sr.Microphone(device_index=device_index)
            
            print("🎤 麦克风初始化成功！")
            print("🔊 正在测试麦克风活性...")
            
            # 测试录音
            with microphone as source:
                print("✅ 麦克风已激活")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                print("🔊 环境噪音调整完成")
                
                print("\n🗣️  请说点什么（5秒内）...")
                start_time = time.time()
                
                try:
                    # 监听语音
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    print(f"✅ 录音完成！用时: {time.time() - start_time:.2f}秒")
                    
                    # 尝试识别
                    print("🧠 正在识别...")
                    text = recognizer.recognize_google(audio, language='zh-CN')
                    print(f"🎯 识别结果: {text}")
                    
                    return True
                    
                except sr.WaitTimeoutError:
                    print("❌ 等待超时 - 未检测到语音")
                    return False
                except Exception as e:
                    print(f"❌ 录音过程出错: {type(e).__name__}: {e}")
                    return False
                    
        except Exception as e:
            print(f"❌ 麦克风设备 {device_index} 初始化失败: {e}")
            return False
    else:
        print(f"❌ 设备索引 {device_index} 超出范围")
        return False

def test_microphone_continuous():
    """连续测试麦克风"""
    print("=" * 60)
    print("🧪 实时麦克风测试工具")
    print("=" * 60)
    print("💡 这个工具会实时显示麦克风状态")
    print("🎯 请对着麦克风说话来测试")
    print("🛑 按 Ctrl+C 停止测试")
    print("=" * 60)
    
    try:
        while True:
            print(f"\n⏰ 测试时间: {time.strftime('%H:%M:%S')}")
            success = monitor_microphone()
            
            if success:
                print("✅ 麦克风工作正常！")
            else:
                print("❌ 麦克风检测失败")
                
            print("\n" + "-" * 40)
            time.sleep(2)  # 等待2秒后再次测试
            
    except KeyboardInterrupt:
        print("\n🛑 测试已停止")
        print("=" * 60)

if __name__ == "__main__":
    test_microphone_continuous()