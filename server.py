from flask import Flask, request, jsonify
import base64
import os
from vosk_api.python.example.llmchat import process_audio_and_chat

app = Flask(__name__)
API_KEY = "MY_SECRET_KEY"  # Optional API key for authentication

# Upload API
@app.route('/upload', methods=['POST'])
def upload():
    client_key = request.headers.get('X-API-Key')
    if API_KEY and client_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json(force=True)
    if not data or 'filename' not in data or 'content' not in data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    filename = data['filename']
    content_b64 = data['content']
    result = ""

    try:
        file_bytes = base64.b64decode(content_b64)
    except Exception as e:
        return jsonify({"status": "error", "message": "Base64 decode failed"}), 400

    with open(filename, 'wb') as f:
        f.write(file_bytes)
    print(f"[*] Received file '{filename}' ({len(file_bytes)} bytes)")

    if filename != 'reply.txt':
        result = process_audio_and_chat()
        print("result", result)

    return jsonify({"status": "success", "message": "File received", "result": result}), 200

# Download API
@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    client_key = request.headers.get('X-API-Key')
    if API_KEY and client_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        with open(filename, 'rb') as f:
            file_bytes = f.read()
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"}), 404

    content_b64 = base64.b64encode(file_bytes).decode('utf-8')
    file_type = filename.rsplit('.', 1)[-1] if '.' in filename else ""

    response = {
        "filename": filename,
        "content": content_b64,
        "type": file_type
    }
    return jsonify(response), 200

# List Files API
@app.route('/list_files', methods=['GET'])
def list_files():
    files = os.listdir('.')
    return jsonify({"files": files}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)