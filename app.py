from flask import Flask, render_template, request, jsonify
import os
import requests
from werkzeug.utils import secure_filename
import openai

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# OpenAI API Key 설정
OPENAI_API_KEY = 'your openai api key'
openai.api_key = OPENAI_API_KEY

# RAG API 엔드포인트
RAG_API_URL = 'http://localhost:5001/rag'  # Response RAG Flask 엔드포인트
STT_API_URL = 'https://api.openai.com/v1/audio/transcriptions'  # 올바른 Whisper STT URL

# HTML 페이지 렌더링
@app.route('/')
def index():
    return render_template('index.html')

# 음성 파일 처리 및 STT 호출
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400

    audio_file = request.files['audio_data']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 순차적으로 파일 이름 설정 (audio1.wav, audio2.wav 등)
    filename = get_next_filename()
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(audio_path)

    # Step 2: STT API 호출 (음성을 텍스트로 변환)
    transcript = send_to_stt(audio_path)
    if not transcript:
        return jsonify({'error': 'STT failed'}), 500

    # Step 3: RAG Flask에 텍스트 전송
    rag_response = send_to_rag(transcript)

    if rag_response and rag_response.status_code == 200:
        response_data = rag_response.json()
        return jsonify({'response': response_data['answer']})
    else:
        return jsonify({'error': 'Error in RAG processing'}), 500

def get_next_filename():
    """저장할 파일 이름을 순차적으로 결정하는 함수"""
    i = 1
    while True:
        filename = f'audio{i}.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return filename
        i += 1

def send_to_stt(audio_path):
    """STT API로 음성 파일 전송하여 텍스트로 변환"""
    with open(audio_path, 'rb') as audio_file:
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
        }
        files = {
            'file': audio_file,
        }
        data = {
            'model': 'whisper-1',  # Whisper 모델 파라미터 추가
        }
        try:
            response = requests.post(STT_API_URL, headers=headers, files=files, data=data)
            if response.status_code == 200:
                return response.json().get('text')
            else:
                print(f"STT API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error in STT API: {e}")
            return None

def send_to_rag(transcript):
    """RAG Flask에 텍스트 전송하여 답변 받기"""
    data = {'query': transcript}
    try:
        response = requests.post(RAG_API_URL, json=data)
        return response
    except Exception as e:
        print(f"Error in RAG Flask: {e}")
        return None

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, port=5000)
