#!/usr/bin/env python3
"""
麦克风测试脚本
用于测试麦克风是否正常工作
"""

import speech_recognition as sr
import time

def test_microphone():
    """测试麦克风功能"""
    print("🎤 麦克风测试开始...")
    
    # 创建识别器
    recognizer = sr.Recognizer()
    
    # 获取麦克风设备列表
    print("\n📋 可用麦克风设备:")
    mic_list = sr.Microphone.list_microphone_names()
    for i, name in enumerate(mic_list):
        print(f"  {i}: {name}")
    
    # 使用默认麦克风
    try:
        with sr.Microphone() as source:
            print(f"\n🎯 使用默认麦克风: {mic_list[0] if mic_list else 'Default'}")
            print("🔊 正在调整环境噪音...")
            
            # 调整环境噪音
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ 环境噪音调整完成")
            
            print("\n🗣️  请说点什么（测试时间5秒）...")
            
            # 开始录音
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("✅ 录音完成！")
                
                # 尝试识别
                print("🧠 正在识别语音...")
                try:
                    text = recognizer.recognize_google(audio, language='zh-CN')
                    print(f"🎯 识别结果: {text}")
                    return True
                except sr.UnknownValueError:
                    print("❌ 无法识别语音内容")
                    return False
                except sr.RequestError as e:
                    print(f"❌ 语音识别服务错误: {e}")
                    return False
                    
            except sr.WaitTimeoutError:
                print("❌ 等待超时 - 没有检测到语音")
                return False
                
    except Exception as e:
        print(f"❌ 麦克风错误: {e}")
        print("💡 可能的原因:")
        print("   - 麦克风未连接或权限被拒绝")
        print("   - 麦克风被其他程序占用")
        print("   - 系统音频设置问题")
        return False

def test_microphone_with_device(device_id=None):
    """测试指定麦克风设备"""
    print(f"🎤 测试麦克风设备 {device_id}...")
    
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone(device_index=device_id) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🗣️  请说点什么...")
            
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=3)
            
            try:
                text = recognizer.recognize_google(audio, language='zh-CN')
                print(f"✅ 识别成功: {text}")
                return True
            except Exception as e:
                print(f"❌ 识别失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 设备 {device_id} 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 社恐翻译器 - 麦克风测试工具")
    print("=" * 50)
    
    # 测试默认麦克风
    success = test_microphone()
    
    if not success:
        print("\n🔧 尝试测试其他麦克风设备...")
        mic_list = sr.Microphone.list_microphone_names()
        
        for i in range(1, min(len(mic_list), 3)):  # 测试前3个设备
            if test_microphone_with_device(i):
                print(f"✅ 设备 {i} 工作正常！")
                break
        else:
            print("\n❌ 所有麦克风设备都无法正常工作")
            print("\n🔧 请检查:")
            print("   1. 麦克风是否正确连接")
            print("   2. 系统隐私设置中麦克风权限是否开启")
            print("   3. 麦克风是否被其他应用占用")
            print("   4. 系统音频输入设置是否正确")
    
    print("\n" + "=" * 50)
    print("🔚 测试完成")
    print("=" * 50)