#!/usr/bin/env python3

import wave
import sys
import requests
import json
import re
from vosk import Model, KaldiRecognizer, SetLogLevel
from collections import deque

# 关闭vosk debug日志
SetLogLevel(0)

# 对话历史队列，保存最近两轮对话
chat_history = deque(maxlen=4)  # 每轮包含用户和助手各一句，4表示2轮

# 加载音频文件
wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("音频文件必须为 WAV 格式单声道 PCM。")
    sys.exit(1)

# 加载VOSK语音识别模型
model = Model("/home/xuwei/vosk-build2/vosk-api/python/example/vosk-model-small-en-us-0.15")

# 初始化识别器
rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(True)
rec.SetPartialWords(True)

# 存储最终识别文本
final_text_list = []
count = 0

print("\n🎙️ 正在识别音频内容...\n")
while True:
    data = wf.readframes(4000)
    count += 1
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        text = result.get("text", "").strip()
        if text:  # 过滤掉空白结果
            final_text_list.append(text)
            print(f"[识别片段 {count}]：{text}")

# 获取最后识别结果
final_result = json.loads(rec.FinalResult())
final_text = final_result.get("text", "").strip()
if final_text:
    final_text_list.append(final_text)
    print(f"[最终识别]：{final_text}")

# 拼接所有识别文本
full_text = ' '.join(final_text_list)
print("\n📝 识别完成，文本如下：\n")
print(full_text)


# 调用 LLM 的函数（带历史上下文和系统提示词）
def llmchat_with_context(question):
    host = "http://localhost"
    port = "11434"
    model = "deepseek-r1:latest"

    url = f"{host}:{port}/api/chat"
    headers = {"Content-Type": "application/json"}

    # 系统提示词
    system_prompt = (
        "你是一个智能语音助手，可以根据用户的语音指令帮忙执行任务，"
        "例如设置闹钟、提醒事项、播放音乐、查询天气、回答问题等，同时你也是一个友好善谈的助手，"
        "如果用户跟你闲聊，你也可以自然地回应。"
        "对于明确的任务，请以【已帮您设置】【提醒您】等执行性语气回复，"
        "对于聊天内容，请以轻松自然的语气回应，增加亲和力。"
        "如果不清楚用户意图，请友好地请求对方澄清问题。"
        
    )

    # 构建消息体，包含系统提示、历史对话和当前问题
    messages = [{"role": "system", "content": system_prompt}]

    # 加入历史上下文
    for msg in chat_history:
        messages.append(msg)

    # 当前用户提问
    messages.append({"role": "user", "content": question})

    data = {
        "model": model,
        "options": {
            "temperature": 0.0
        },
        "stream": False,
        "messages": messages
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            answer = response.json().get("message", {}).get("content", "")
            # 清洗无关格式
            answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
            answer = re.sub(r'```json', '', answer)
            answer = re.sub(r'```', '', answer)
            return answer.strip()
        else:
            print(f"❌ 错误：{response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 异常：{e}")
        return None


# 根据识别内容调用大模型
if full_text:
    print("\n🤖 正在向大模型提问...\n")
    # 调用LLM
    answer = llmchat_with_context(full_text)

    if answer:
        print("\n💡 大模型回复如下：\n")
        print(answer)
        # 存储本轮对话到历史记录（用户问题+助手回答）
        chat_history.append({"role": "user", "content": full_text})
        chat_history.append({"role": "assistant", "content": answer})
    else:
        print("⚠️ 未能获得大模型回复。")
else:
    print("⚠️ 未识别到有效文本，无法提问大模型。")
