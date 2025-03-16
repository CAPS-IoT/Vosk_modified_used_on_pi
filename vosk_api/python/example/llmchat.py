#!/usr/bin/env python3

import wave
import requests
import json
import re
import os
from vosk import Model, KaldiRecognizer, SetLogLevel

# === 参数区 ===
HISTORY_ROUND = 2                 # 最近多少轮对话
AUDIO_FILE = "rec5.wav"           # 默认音频文件路径

# 关闭 vosk debug 日志
SetLogLevel(0)

# === 全局对话内存（代替文件） ===
conversation_memory = []  # 形如 [{"role": "user", "content": "xxx"}, {"role": "assistant", "content": "yyy"}, ...]

# === 添加一轮对话到内存 ===
def add_to_memory(user_text, ai_text, memory, max_rounds=2):
    memory.append({"role": "user", "content": user_text})
    memory.append({"role": "assistant", "content": ai_text})
    # 保留最近 max_rounds 轮
    if len(memory) > max_rounds * 2:
        memory[:] = memory[-max_rounds * 2:]

# === 调用 LLM 聊天，内存中保留历史 ===
def llmchat(question):
    host = "http://localhost"
    port = "11434"
    model = "deepseek-r1:latest"

    url = f"{host}:{port}/api/chat"
    headers = {"Content-Type": "application/json"}

    system_prompt = (
        "你是一个智能语音助手，可以根据用户的语音指令帮忙执行任务，"
        "例如设置闹钟、提醒事项、播放音乐、查询天气、回答问题等，同时你也是一个友好善谈的助手，"
        "如果用户跟你闲聊，你也可以自然地回应。"
        "对于明确的任务，请以【已帮您设置】【提醒您】等执行性语气回复，"
        "对于聊天内容，请以轻松自然的语气回应，增加亲和力。"
        "如果不清楚用户意图，请友好地请求对方澄清问题。"
        "注意：必须用英文回复。"
    )

    messages = [{"role": "system", "content": system_prompt}] + conversation_memory
    messages.append({"role": "user", "content": question})

    data = {
        "model": model,
        "options": {"temperature": 0.0},
        "stream": False,
        "messages": messages
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            answer = response.json().get("message", {}).get("content", "")
            # 去掉无关字符
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

# === 音频识别并调用大模型主函数 ===
def process_audio_and_chat():
    # === 加载音频文件 ===
    if not os.path.exists(AUDIO_FILE):
        print(f"⚠️ 找不到音频文件 {AUDIO_FILE}")
        return "Audio file not found."

    wf = wave.open(AUDIO_FILE, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("⚠️ 音频文件必须为 WAV 格式单声道 PCM。")
        return "Invalid audio file format."

    # === 加载 VOSK 语音识别模型 ===
    model = Model("/home/xuwei/vosk-build2/vosk_api/python/example/vosk-model-small-en-us-0.15")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    rec.SetPartialWords(True)

    # === 识别音频 ===
    final_text_list = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "").strip()
            if text:
                final_text_list.append(text)

    final_result = json.loads(rec.FinalResult())
    final_text = final_result.get("text", "").strip()
    if final_text:
        final_text_list.append(final_text)

    full_text = ' '.join(final_text_list).strip()

    if not full_text:
        print("⚠️ 未识别到有效文本，无法提问大模型。")
        return "No valid speech recognized."

    print(f"\n📝 识别完成文本：{full_text}\n")

    # === 调用大模型 ===
    print("\n🤖 正在向大模型提问...\n")
    answer = llmchat(full_text)

    if answer:
        print("\n💡 大模型回复如下：\n")
        print(answer)
        add_to_memory(full_text, answer, conversation_memory, max_rounds=HISTORY_ROUND)
        return answer
    else:
        print("⚠️ 未能获得大模型回复。")
        return "Failed to get response from LLM."

# === 测试调用 ===
if __name__ == "__main__":
    result = process_audio_and_chat()
    print("\n✅ 最终返回结果：", result)
