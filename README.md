# WhisperX Worker

RunPodを使用したWhisperXによる音声認識・話者分離システム

## セットアップ

1. 依存パッケージのインストール：
```bash
pip install -r requirements.txt
```

2. 環境変数の設定：
`.env.example`ファイルを`.env`にコピーして、実際の値を設定してください。

```bash
cp .env.example .env
```

`.env`ファイルの内容：
```
RUNPOD_API_KEY=your_runpod_api_key_here
HUGGINGFACE_TOKEN=your_huggingface_token_here
RUNPOD_URL_RUN=https://api.runpod.ai/v2/your_endpoint_id/run
```

## 使用方法

### 基本的な音声認識
```bash
python test.py
```

### 話者分離なしの認識
```bash
python test2.py
```

### 高精度な話者分離付き認識（議事録生成）
```bash
python test3.py
```

## 必要なAPIキー

- **RunPod API Key**: RunPodのダッシュボードから取得
- **Hugging Face Token**: Hugging Faceアカウントから取得（話者分離機能に必要）

## ファイル構成

- `test.py`: 基本的な音声認識テスト
- `test2.py`: 話者分離なしの認識テスト  
- `test3.py`: 高精度な話者分離付き認識（議事録形式）
- `Result/`: 出力ファイルが保存されるフォルダ
- `temporary/`: 一時的な音声ファイル置き場