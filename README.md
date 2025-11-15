# 社恐翻译器

通过麦克风实现语音输入，将语音转为文本，然后调用大模型判断是否为"客套话"，输出真实意图的翻译器。

## 功能特点

- 🎤 语音识别：实时将语音转换为文本
- 🧠 AI翻译：识别客套话并输出真实意图  
- 💬 实时显示：在屏幕上显示翻译结果
- 🚀 流式输出：支持实时流式响应

## 安装

```bash
pip install -r requirements.txt
```

## 配置

在项目根目录创建 `.env` 文件，添加你的API密钥：

```
DASHSCOPE_API_KEY=sk-b67aded7e87d4f1cb06b8db0b3853f35
```

## 使用

```bash
python app.py
```

然后在浏览器中访问 `http://localhost:5000`

## 技术栈

- Python
- Flask (Web框架)
- SpeechRecognition (语音识别)
- DashScope (阿里云百炼大模型)
- HTML/CSS/JavaScript (前端界面)