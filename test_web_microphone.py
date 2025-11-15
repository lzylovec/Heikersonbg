#!/usr/bin/env python3
"""
简单麦克风测试 - 直接在Web应用中使用
"""

import requests
import time

def test_web_microphone():
    """通过Web接口测试麦克风"""
    print("🎤 测试Web应用麦克风功能...")
    print("📱 请打开浏览器访问: http://localhost:8080")
    print("🎯 然后点击'开始录音'按钮进行测试")
    
    # 等待用户操作
    input("\n按回车键开始测试Web接口...")
    
    # 测试后端接口
    try:
        # 测试开始录音接口
        print("\n🧪 测试开始录音接口...")
        response = requests.post('http://localhost:8080/start_recording', 
                               json={})
        print(f"开始录音响应: {response.status_code}")
        print(f"响应内容: {response.json()}")
        
        # 等待一段时间让用户说话
        print("\n⏳ 等待5秒让用户说话...")
        time.sleep(5)
        
        # 检查结果
        print("\n🔍 检查结果...")
        result_response = requests.get('http://localhost:8080/get_result')
        result_data = result_response.json()
        print(f"结果响应: {result_data}")
        
        if result_data.get('status') == 'completed' and result_data.get('result'):
            result = result_data['result']
            print(f"\n✅ 测试成功!")
            print(f"📝 原始文本: {result.get('original_text', '无')}")
            print(f"🧠 AI翻译: {result.get('translation', '无')}")
        else:
            print(f"\n⚠️  测试状态: {result_data.get('status', '未知')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_web_microphone()