#!/usr/bin/env python3
"""
测试新的OpenAI兼容API调用方式
验证qwen3-max模型是否能正确调用
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_new_api():
    """测试新的OpenAI兼容API"""
    print("🧪 测试新的OpenAI兼容API...")
    print("=" * 50)
    
    try:
        # 初始化客户端
        client = OpenAI(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        print("✅ 客户端初始化成功")
        
        # 测试调用
        print("🤖 调用qwen3-max模型...")
        
        completion = client.chat.completions.create(
            model="qwen3-max",
            messages=[
                {"role": "system", "content": "你是一个专业的社交意图分析专家。"},
                {"role": "user", "content": "请分析这句话：'改天我们一起吃饭吧'"}
            ],
            stream=False,
            temperature=0.7
        )
        
        result = completion.choices[0].message.content
        print(f"✅ 调用成功！")
        print(f"📝 分析结果: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False

def test_speech_recognition_api():
    """测试语音识别API是否可用"""
    print("\n🎤 测试语音识别API...")
    
    try:
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        
        # 测试Google语音识别
        print("1️⃣ 测试Google语音识别服务...")
        
        # 使用一个很短的音频片段测试
        with sr.Microphone(device_index=2) as source:
            print("录制测试音频...")
            audio = recognizer.record(source, duration=2)
            
            try:
                text = recognizer.recognize_google(audio, language='zh-CN')
                print(f"✅ Google语音识别可用: {text}")
                return True
            except Exception as e:
                print(f"❌ Google语音识别失败: {e}")
                
                # 尝试英文识别
                try:
                    text_en = recognizer.recognize_google(audio, language='en-US')
                    print(f"✅ 英文识别可用: {text_en}")
                    return True
                except Exception as e2:
                    print(f"❌ 英文识别也失败: {e2}")
                    return False
                    
    except Exception as e:
        print(f"❌ 语音识别测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 社恐翻译器 - API兼容性测试")
    print("=" * 60)
    
    # 测试新的API
    api_success = test_new_api()
    
    # 测试语音识别
    speech_success = test_speech_recognition_api()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"OpenAI兼容API: {'✅ 正常' if api_success else '❌ 失败'}")
    print(f"语音识别API: {'✅ 正常' if speech_success else '❌ 失败'}")
    
    if api_success and speech_success:
        print("\n🎉 所有测试通过！系统应该可以正常工作。")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")