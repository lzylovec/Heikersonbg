#!/usr/bin/env python3
"""
macOS麦克风权限检查和修复脚本
"""

import os
import subprocess
import platform

def check_microphone_permission():
    """检查macOS麦克风权限"""
    print("🔍 检查麦克风权限...")
    
    if platform.system() != "Darwin":
        print("⚠️  非macOS系统，跳过权限检查")
        return True
    
    try:
        # 检查终端是否有麦克风权限
        result = subprocess.run([
            "osascript", "-e", 
            "tell application \"System Events\" to get the privacy setting for microphone"
        ], capture_output=True, text=True)
        
        print("💡 请确保在系统偏好设置中给终端应用麦克风权限")
        print("🔧 操作步骤:")
        print("   1. 打开 系统偏好设置 > 安全性与隐私 > 隐私")
        print("   2. 选择左侧的 麦克风")
        print("   3. 在右侧列表中勾选 终端 或 iTerm")
        print("   4. 如果已勾选，尝试取消后重新勾选")
        print("   5. 重启终端应用")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查权限时出错: {e}")
        return False

def check_audio_devices():
    """检查音频设备"""
    print("\n🔊 检查音频设备...")
    
    try:
        # 使用system_profiler检查音频设备
        result = subprocess.run(["system_profiler", "SPAudioDataType"], 
                              capture_output=True, text=True)
        
        if "Microphone" in result.stdout or "Input" in result.stdout:
            print("✅ 检测到音频输入设备")
            return True
        else:
            print("⚠️  未检测到麦克风设备")
            return False
            
    except Exception as e:
        print(f"❌ 检查音频设备失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 macOS麦克风权限诊断工具")
    print("=" * 50)
    
    check_microphone_permission()
    check_audio_devices()
    
    print("\n📝 额外建议:")
    print("   - 确保麦克风硬件连接正常")
    print("   - 检查麦克风是否被其他应用占用")
    print("   - 尝试重启应用和系统")
    print("   - 考虑使用外部USB麦克风")
    
    print("\n" + "=" * 50)