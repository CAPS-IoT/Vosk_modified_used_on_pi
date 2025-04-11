#!/usr/bin/env python3

import wave
import requests
import json
import re
import os
import base64
from vosk import Model, KaldiRecognizer, SetLogLevel

# === parameter ===
HISTORY_ROUND = 2                 # chat history
AUDIO_FILE = "/home/weihaoxu/vosk-build/vosk_api/python/example/rec5.wav"           #audio file path
API_KEY = "MY_SECRET_KEY" 
# close vosk debug log
SetLogLevel(0)

# === memory of model ===
conversation_memory = []  #[{"role": "user", "content": "xxx"}, {"role": "assistant", "content": "yyy"}, ...]

# === add to memory ===
def add_to_memory(user_text, ai_text, memory, max_rounds=2):
    memory.append({"role": "user", "content": user_text})
    memory.append({"role": "assistant", "content": ai_text})
    # preserve recent max_rounds 
    if len(memory) > max_rounds * 2:
        memory[:] = memory[-max_rounds * 2:]

# === Chat with LLM and keep the history ===
def llmchat(question):
    host = "http://localhost" ##where the llm model is download
    port = "11434"
    model = "deepseek-r1:7b"

    url = f"{host}:{port}/api/chat"
    headers = {"Content-Type": "application/json"}

    system_prompt = (
        "You're an intelligent voice assistant that helps perform tasks based on the user's voice commands,"
        "For example, setting alarms, reminders, playing music, checking the weather, answering questions, etc. Meanwhile, you're a friendly and chatty helper,"
        "If a user makes small talk with you, you can also respond naturally,"
        "For clear tasks, please reply in an executive tone such as [already set up for you] [remind you],"
        "For chats, please respond in a relaxed and natural tone to increase rapport,"
        "If it is not clear what the user intends, kindly ask for clarification of the question,"
        "Note: Responses must be in English."
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
        response = requests.post(url, json=data, headers=headers, timeout=300)
        if response.status_code == 200:
            answer = response.json().get("message", {}).get("content", "")
            answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
            answer = re.sub(r'```json', '', answer)
            answer = re.sub(r'```', '', answer)
            return answer.strip()
        else:
            print(f"Error:{response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception{e}")
		
def process_audio_and_chat():
    if not os.path.exists(AUDIO_FILE):
        return "Audio file not found."
    wf = wave.open(AUDIO_FILE, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("wav file should be one single channel")
        return "Invalid audio file format."
		
    model = Model("/home/weihaoxu/vosk-build/vosk-model-small-en-us-0.15")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    rec.SetPartialWords(True)
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
        print("No valid speech recognized.")
        return "No valid speech recognized."

    print(f"\n The recognized text isï¼{full_text}\n")

    # === call LLM ===
    print("\n Talking to the LLM...\n")
    answer = llmchat(full_text)

    if answer:
        print("\n The reply isï¼\n")
        print(answer)
        add_to_memory(full_text, answer, conversation_memory, max_rounds=HISTORY_ROUND)
        try:
            headers = {
            
                'X-API-Key': 'MY_SECRET_KEY',  
                'Content-Type': 'application/json'
            }
            response = requests.post(
                "http://192.168.178.117:5000/upload",
                headers=headers,
                json={"filename": "reply.txt", "content": base64.b64encode(answer.encode()).decode()}
            )
            if response.status_code == 200:
                print("Already uploaded")
                get_response = requests.get(
                    "http://192.168.178.117:5000/download/reply.txt",
                    headers=headers
                )
                if get_response.status_code == 200:
                    response_data = get_response.json()
                    content_b64 = response_data.get("content", "")
                    decoded_content = base64.b64decode(content_b64).decode('utf-8')
                    print("Reply is:", decoded_content)
                else:
                    print(f"Failed to get result:{get_response.status_code} - {get_response.text}")
            else:
                print(f"Failed to upload:{response.status_code} - {response.text}")
        except Exception as e:
            print(f"Upload exception:{e}")
        return answer
    else:
        print("\nHaven't recieved a reply.")
        return "Failed to get response from LLM."

# === testing ===
if __name__ == "__main__":
    result = process_audio_and_chat()
    print("\n The final result isï¼", result)
