#!/usr/bin/env python3
"""
社恐翻译器测试脚本
用于测试语音识别和AI翻译功能
"""

import os
import sys
from translator import SocialAnxietyTranslator

def test_translator():
    """测试翻译器功能"""
    print("🧪 开始测试社恐翻译器...")
    
    # 初始化翻译器
    translator = SocialAnxietyTranslator()
    
    # 测试文本
    test_texts = [
        "改天我们一起吃饭吧",
        "你最近怎么样",
        "有空常联系",
        "你的想法很有意思",
        "我考虑一下"
    ]
    
    print("\n📋 测试文本分析：")
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. 测试文本: {text}")
        print("   正在分析...")
        
        try:
            result = translator.translate_politeness(text)
            if result:
                print(f"   ✅ 分析结果: {result}")
            else:
                print(f"   ❌ 分析失败")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    
    print("\n🎯 测试完成！")
    print("\n💡 提示：")
    print("   - 如果文本分析成功，说明AI模型连接正常")
    print("   - 要测试语音识别，请在Web界面中点击录音按钮")
    print("   - 确保麦克风权限已开启")

if __name__ == "__main__":
    test_translator()