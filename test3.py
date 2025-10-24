import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -------------------------
# 設定（環境変数から取得）
# -------------------------
RUNPOD_URL_RUN = os.getenv(
    "RUNPOD_URL_RUN", "https://api.runpod.ai/v2/kvrcq5slzrsolf/run")  # ワーカーのエンドポイント
API_KEY = os.getenv("RUNPOD_API_KEY", "")  # RunPodのAPIキー
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")   # HuggingFaceトークン

AUDIO_URL = "https://github.com/Bellk4/whisperX_worker/raw/main/temporary/audio1.mp3"
BATCH_SIZE = 32
MIN_SPEAKERS = 2
MAX_SPEAKERS = 5
LANGUAGE = "ja"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -------------------------
# ジョブ送信
# -------------------------
payload = {
    "input": {
        "audio_file": AUDIO_URL,
        "language": LANGUAGE,
        # "batch_size": BATCH_SIZE,
        # "temperature": 0.2,
        "align_output": True,
        "diarization": True,
        "huggingface_access_token": HUGGINGFACE_TOKEN,
        "min_speakers": MIN_SPEAKERS,
        "max_speakers": MAX_SPEAKERS,
        "debug": True
    }
}

response = requests.post(
    RUNPOD_URL_RUN, headers=HEADERS, data=json.dumps(payload))

if response.status_code != 200:
    print(f"ジョブ送信エラー: {response.status_code}")
    print(response.text)
    exit()

job_info = response.json()
job_id = job_info.get("id")
print(f"ジョブ送信成功！ジョブID: {job_id}")

# -------------------------
# ジョブ完了待機（ポーリング）
# -------------------------
RUNPOD_URL_STATUS = f"https://api.runpod.ai/v2/kvrcq5slzrsolf/status/{job_id}"

while True:
    status_resp = requests.get(RUNPOD_URL_STATUS, headers=HEADERS)
    if status_resp.status_code != 200:
        print(f"ステータス取得エラー: {status_resp.status_code}")
        print(f"URL: {RUNPOD_URL_STATUS}")
        try:
            error_json = status_resp.json()
            print(
                f"エラー詳細: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"レスポンステキスト: {status_resp.text}")
        time.sleep(5)
        continue

    status_json = status_resp.json()
    status = status_json.get("status")
    print(f"ジョブステータス: {status}")

    if status == "COMPLETED":
        print("ジョブ完了！結果取得中…")
        output = status_json.get("output")
        print(json.dumps(output, indent=2, ensure_ascii=False))
        break
    elif status == "FAILED":
        print("ジョブ失敗")
        print(json.dumps(status_json, indent=2, ensure_ascii=False))
        break

    time.sleep(5)  # 5秒ごとにチェック
