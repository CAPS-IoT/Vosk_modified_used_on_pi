from flask import Flask, request, jsonify
import base64

app = Flask(__name__)
API_KEY = "MY_SECRET_KEY"  # 与ESP32约定的API密钥

# 接收文件上传
@app.route('/upload', methods=['POST'])
def upload():
    # 可选：API密钥校验
    client_key = request.headers.get('X-API-Key')
    if API_KEY and client_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json(force=True)  # 获取JSON请求体
    if not data or 'filename' not in data or 'content' not in data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    filename = data['filename']
    content_b64 = data['content']
    try:
        file_bytes = base64.b64decode(content_b64)  # 解码Base64内容
    except Exception as e:
        return jsonify({"status": "error", "message": "Base64 decode failed"}), 400
    # 将文件保存到服务器本地
    with open(filename, 'wb') as f:
        f.write(file_bytes)
    print(f"[*] Received file '{filename}' ({len(file_bytes)} bytes)")
    return jsonify({"status": "success", "message": "File received"}), 200

# 提供文件下载
@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    # 可选：API密钥校验
    client_key = request.headers.get('X-API-Key')
    if API_KEY and client_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        with open(filename, 'rb') as f:
            file_bytes = f.read()
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"}), 404
    # 将文件内容编码为Base64字符串
    content_b64 = base64.b64encode(file_bytes).decode('utf-8')
    # 文件类型（扩展名）供参考
    file_type = ""
    if '.' in filename:
        file_type = filename.rsplit('.', 1)[-1]
    response = {
        "filename": filename,
        "content": content_b64,
        "type": file_type
    }
    # 注意：JSON 不适合传输过大的二进制数据，Base64 会增加约33%大小&#8203;:contentReference[oaicite:10]{index=10}
    return jsonify(response), 200

if __name__ == '__main__':
    # 运行Flask应用（生产环境应使用更可靠的部署方式）
    app.run(host='0.0.0.0', port=5000)
