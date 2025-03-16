import requests
import base64

API_KEY = "MY_SECRET_KEY"
SERVER_URL = "http://localhost:5000"

def upload_file(filepath):
    with open(filepath, 'rb') as f:
        file_bytes = f.read()
    content_b64 = base64.b64encode(file_bytes).decode('utf-8')
    filename = filepath.split('/')[-1]
    data = {
        "filename": filename,
        "content": content_b64
    }
    headers = {
        "X-API-Key": API_KEY
    }
    response = requests.post(f"{SERVER_URL}/upload", json=data, headers=headers)
    return response.json()

def download_file(filename, save_path):
    headers = {
        "X-API-Key": API_KEY
    }
    response = requests.get(f"{SERVER_URL}/download/{filename}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        content_b64 = data['content']
        file_bytes = base64.b64decode(content_b64)
        with open(save_path, 'wb') as f:
            f.write(file_bytes)
        return {"status": "success", "message": f"File saved to {save_path}"}
    else:
        return response.json()

def list_files():
    headers = {
        "X-API-Key": API_KEY
    }
    response = requests.get(f"{SERVER_URL}/list_files", headers=headers)
    return response.json()

if __name__ == "__main__":
  
    print(upload_file('/path/to/your/file.txt'))
    print(download_file('file.txt', '/path/to/save/file.txt'))
    print(list_files())