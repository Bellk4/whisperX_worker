import requests
import json
import time

# --- 設定 ---
RUNPOD_API_KEY = "rpa_EF17ZX4Z6QSFAXOV823WT51UR4YYMLTP45HAHL1Ckg1btt"
ENDPOINT_ID = "kvrcq5slzrsolf"


def run_whisperx_sync(audio_url, language="en"):
    print(f" 音声ファイル: {audio_url}")
    print(f" 言語: {language}")

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": {
            "audio_file": audio_url,
            "language": language,
            "align_output": True,
            "debug": True
        }
    }

    sync_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
    print(f" ジョブ送信中...")

    try:
        response = requests.post(
            sync_url, headers=headers, json=payload, timeout=600)

        if response.status_code == 200:
            response_data = response.json()

            print("=== レスポンス ===")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            print("==================")

            if "status" in response_data and response_data["status"] == "IN_QUEUE":
                job_id = response_data["id"]
                print(f" キューに追加されました。完了を待機...")
                return check_job_status(job_id)
            else:
                return response_data

        else:
            print(f" エラー: HTTP {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f" エラー: {e}")
        return None


def check_job_status(job_id):
    status_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }

    max_attempts = 60
    attempt = 0

    while attempt < max_attempts:
        try:
            response = requests.get(status_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "UNKNOWN")

                if status == "COMPLETED":
                    print(" 完了！")
                    return data
                elif status in ["FAILED", "CANCELLED", "TIMED_OUT"]:
                    print(f" 失敗: {status}")
                    error_info = data.get("error", "不明")
                    print(f"   エラー: {error_info}")
                    return None
                else:
                    print(f" ステータス: {status}...")

            else:
                print(f" ステータス確認エラー: {response.status_code}")
                return None

        except Exception as e:
            print(f" エラー: {e}")
            return None

        attempt += 1
        time.sleep(10)

    print(" タイムアウト")
    return None


def process_result(result_data):
    if not result_data:
        return

    try:
        if "output" in result_data:
            output = result_data["output"]

            if isinstance(output, dict):
                if "segments" in output:
                    segments = output["segments"]
                    print(f" 音声認識結果 ({len(segments)}セグメント):")

                    for i, segment in enumerate(segments):
                        start = segment.get("start", 0)
                        end = segment.get("end", 0)
                        text = segment.get("text", "")
                        print(f"   [{i+1}] {start:.2f}s-{end:.2f}s: {text}")
            else:
                print(f" 結果: {output}")
        else:
            print(f" 予期しない形式")

    except Exception as e:
        print(f" 結果処理エラー: {e}")


def test_english():
    url = "https://github.com/runpod-workers/sample-inputs/raw/main/audio/gettysburg.wav"
    result = run_whisperx_sync(url, "en")
    if result:
        process_result(result)
    return result


if __name__ == "__main__":
    print("=== whisperX テスト ===")
    print("ローカルファイルをパブリックURLにする方法:")
    print("1. GitHub Releases（推奨）")
    print("2. Google Drive（共有設定）")
    print("3. Dropbox（dl=1パラメータ）")
    print("")
    print("使用方法: run_whisperx_sync('YOUR_URL', 'ja')")
    print("")
    print(" 英語テスト実行中...")
    test_english()
