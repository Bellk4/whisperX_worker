import requests
import json
import time
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === 設定 ===
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
ENDPOINT_ID = "kvrcq5slzrsolf"
AUDIO_URL = "https://github.com/Bellk4/whisperX_worker/raw/main/temporary/audio1.mp3"

# === WhisperX 設定 ===
WHISPERX_CONFIG = {
    "language": "ja",
    "align_output": True,
    "diarization": False,
    "min_speakers": 1,
    "max_speakers": 5,
    "debug": True,
    "huggingface_access_token": os.getenv("HUGGINGFACE_TOKEN", ""),
}

# WHISPERX_CONFIG = {
#     "language": "ja",
#     "align_output": True,
#     "diarization": False,
#     "min_speakers": 1,
#     "max_speakers": 5,
#     "debug": True,
#     "huggingface_access_token": os.getenv("HUGGINGFACE_TOKEN", ""),
# }

# === メイン ===


def main():
    print("=== WhisperX Worker 実行テスト ===\n")

    print("【設定確認】")
    for k, v in WHISPERX_CONFIG.items():
        print(f"  {k}: {v}")
    print("")

    result = run_whisperx_async(AUDIO_URL)
    if result:
        process_result(result)
    else:
        print("❌ WhisperX の実行に失敗しました。")


# === 非同期ジョブ送信 ===
def run_whisperx_async(audio_url, custom_config=None):
    config = WHISPERX_CONFIG.copy()
    if custom_config:
        config.update(custom_config)

    payload = {"input": {"audio_file": audio_url, **
                         {k: v for k, v in config.items() if v is not None}}}
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"

    print("🚀 WhisperX 非同期ジョブ送信中...\n")

    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code != 200:
            print(f"❌ HTTPエラー: {res.status_code}")
            print(res.text)
            return None

        data = res.json()
        job_id = data.get("id")
        if not job_id:
            print("❌ ジョブIDを取得できませんでした。")
            print(data)
            return None

        print(f"🆔 ジョブID: {job_id}\n")
        return wait_for_completion(job_id)

    except requests.RequestException as e:
        print(f"❌ 通信エラー: {e}")
        return None


# === ジョブ完了待機 ===
def wait_for_completion(job_id):
    url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}

    print("⌛ WhisperX の処理完了を待機中...\n")

    for attempt in range(120):  # 最大20分待機
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                status = data.get("status", "")
                if status == "COMPLETED":
                    print("✅ ジョブ完了!\n")
                    return data
                elif status in ["FAILED", "CANCELLED", "TIMED_OUT"]:
                    print(f"❌ ジョブ失敗: {status}")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    return None
                else:
                    print(f"⏳ ステータス: {status}...({attempt+1}/120)")
            else:
                print(f"⚠️ ステータス取得エラー: {res.status_code}")
        except requests.RequestException as e:
            print(f"⚠️ 通信エラー: {e}")

        time.sleep(10)

    print("⏰ タイムアウト（20分経過）")
    return None


# === 結果整形 ===
def process_result(result):
    output = result.get("output", {})

    if not isinstance(output, dict) or "segments" not in output:
        print("⚠️ 結果形式が不正です。")
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    segments = output["segments"]
    lang = output.get("detected_language", "不明")

    print("=== 音声認識結果 ===")
    print(f"言語: {lang}")
    print(f"セグメント数: {len(segments)}\n")

    for i, seg in enumerate(segments, 1):
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("text", "")
        speaker = seg.get("speaker")
        if speaker:
            print(f"[{i}] {start:.2f}s - {end:.2f}s ({speaker}): {text}")
        else:
            print(f"[{i}] {start:.2f}s - {end:.2f}s: {text}")

    print("\n=== 完了 ===")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 中断されました。")
        sys.exit(1)
