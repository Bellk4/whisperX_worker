import requests
import json
import time
import os
from datetime import datetime
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

AUDIO_URL = "https://github.com/Bellk4/whisperX_worker/raw/main/temporary/kwkm.wav"
BATCH_SIZE = 32
MIN_SPEAKERS = 2
MAX_SPEAKERS = 5
LANGUAGE = "ja"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -------------------------
# ファイル保存用関数
# -------------------------


def ensure_result_folder():
    """
    Resultフォルダが存在しない場合は作成する
    """
    result_folder = "Result"
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
        print(f"フォルダを作成しました: {result_folder}")
    return result_folder


def format_transcript_to_minutes(segments):
    """
    話者分離された結果を議事録形式でフォーマットする
    """
    if not segments:
        return "議事録データが見つかりませんでした。"

    # ヘッダー情報
    now = datetime.now()
    minutes = f"""
==========================================
            会議議事録
==========================================
作成日時: {now.strftime('%Y年%m月%d日 %H:%M:%S')}
音声ファイル: {AUDIO_URL.split('/')[-1]}
言語: {LANGUAGE}
話者数: {len(set(seg.get('speaker', 'UNKNOWN') for seg in segments if 'speaker' in seg))}
==========================================

"""

    current_speaker = None
    speaker_count = {}

    for segment in segments:
        speaker = segment.get('speaker', 'UNKNOWN')
        text = segment.get('text', '').strip()
        start_time = segment.get('start', 0)
        end_time = segment.get('end', 0)

        if not text:
            continue

        # 話者カウント
        if speaker not in speaker_count:
            speaker_count[speaker] = len(speaker_count) + 1

        # 時間フォーマット（分:秒）
        start_min = int(start_time // 60)
        start_sec = int(start_time % 60)
        end_min = int(end_time // 60)
        end_sec = int(end_time % 60)

        time_stamp = f"[{start_min:02d}:{start_sec:02d}-{end_min:02d}:{end_sec:02d}]"

        # 話者が変わった場合は改行を追加
        if current_speaker != speaker:
            if current_speaker is not None:
                minutes += "\n"
            current_speaker = speaker
            speaker_name = f"話者{speaker_count[speaker]}"
            minutes += f"{speaker_name} {time_stamp}:\n"

        minutes += f"  {text}\n"

    minutes += "\n" + "=" * 42 + "\n"
    minutes += f"議事録終了 (総時間: {int(segments[-1].get('end', 0) // 60)}分{int(segments[-1].get('end', 0) % 60):02d}秒)\n"
    minutes += "=" * 42 + "\n"

    return minutes


def save_minutes_to_file(content, filename=None):
    """
    議事録をResultフォルダに保存する
    """
    result_folder = ensure_result_folder()

    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"議事録_{timestamp}.txt"

    # Resultフォルダ内のパスを作成
    filepath = os.path.join(result_folder, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"議事録を保存しました: {filepath}")
        return filepath
    except Exception as e:
        print(f"ファイル保存エラー: {e}")
        return None


def save_json_to_file(data, filename=None):
    """
    JSONデータをResultフォルダに保存する
    """
    result_folder = ensure_result_folder()

    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"音声認識詳細_{timestamp}.json"

    # Resultフォルダ内のパスを作成
    filepath = os.path.join(result_folder, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"詳細データを保存しました: {filepath}")
        return filepath
    except Exception as e:
        print(f"JSONファイル保存エラー: {e}")
        return None


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

        # セグメント情報を取得
        segments = output.get("segments", []) if output else []

        if segments:
            # 議事録形式で整理
            minutes_content = format_transcript_to_minutes(segments)

            # コンソールに表示
            print("\n" + "="*50)
            print("          議事録（話者分離結果）")
            print("="*50)
            print(minutes_content)

            # ファイルに保存
            saved_file = save_minutes_to_file(minutes_content)

            # 詳細なJSONデータも保存（オプション）
            saved_json_file = save_json_to_file(output)

        else:
            print("セグメントデータが見つかりませんでした。")
            print("生データ:")
            print(json.dumps(output, indent=2, ensure_ascii=False))

            # 生データも保存
            save_json_to_file(output, "raw_output_" +
                              datetime.now().strftime('%Y%m%d_%H%M%S') + ".json")

        break
    elif status == "FAILED":
        print("ジョブ失敗")
        print(json.dumps(status_json, indent=2, ensure_ascii=False))
        break

    time.sleep(5)  # 5秒ごとにチェック
