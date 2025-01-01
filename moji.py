import streamlit as st
import whisper
import tempfile
import os
import subprocess
from pathlib import Path
import logging
import streamlit_authenticator as stauth 
from auth_config import load_auth_config


# YAMLファイルの設定を読み込む
config = load_auth_config('stmoji/config.yaml')

# Authenticatorオブジェクトの作成
authenticator = stauth.Authenticate(
    credentials=config['credentials'],
    cookie_name=config['cookie']['name'],
    key=config['cookie']['key'],
    expiry_days=config['cookie']['expiry_days']
)

# ログインウィジェット
name, authentication_status, username = authenticator.login("ログイン", "main")

if authentication_status:
    st.success(f"ようこそ, {name}さん!")
    # ログアウトボタン
    authenticator.logout("ログアウト", "sidebar")
    st.title("アプリケーションのメインページ")
elif authentication_status is False:
    st.error("ユーザー名またはパスワードが正しくありません。")
elif authentication_status is None:
    st.warning("認証情報を入力してください。")
# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Whisperモデルのロード

def convert_audio_to_wav(input_path, output_path, progress_bar):
    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-ar', '16000',
            '-ac', '1',
            '-c:a', 'pcm_s16le',
            '-y',
            output_path
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception("音声変換に失敗しました。")
        
        progress_bar.progress(0.4)
        return True
    except Exception as e:
        raise Exception(f"音声変換中にエラーが発生しました: {str(e)}")

# モデルのキャッシュ化
@st.cache_resource
def load_whisper_model():
    """
    Whisperモデルをロードする関数
    Returns:
        whisper.Whisper: ロードされたWhisperモデル
    """
    try:
        return whisper.load_model("base")  # baseモデルを使用
    except Exception as e:
        logger.error(f"モデルのロードに失敗: {e}")
        raise Exception("Whisperモデルのロードに失敗しました。")

def transcribe_audio(audio_path, selected_language):
    wav_path = None
    try:
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        progress_text.text("Whisperモデルを準備中...")
        model = load_whisper_model()
        progress_bar.progress(0.2)
        
        progress_text.text("音声ファイルを変換中...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
            wav_path = temp_wav.name
        
        convert_audio_to_wav(audio_path, wav_path, progress_bar)
        progress_bar.progress(0.6)
        
        progress_text.text("文字起こしを実行中...")
        result = model.transcribe(wav_path, language=selected_language)
        
        progress_bar.progress(1.0)
        progress_text.text("処理が完了しました！")
        
        return result["text"]
    
    finally:
        if wav_path and os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
            except Exception as e:
                logger.error(f"一時ファイルの削除に失敗: {e}")

def main():
    st.set_page_config(page_title="音声文字起こしアプリ", page_icon="🎤")
    
    st.title("音声文字起こしアプリ")
    st.write("対応フォーマット: MP3, WAV, M4A, FLAC, OGG, AAC, WMA")
    
    languages = {
        "自動検出": None,
        "日本語": "ja",
        "英語": "en",
        "中国語": "zh",
        "韓国語": "ko",
        "スペイン語": "es",
        "フランス語": "fr",
        "ドイツ語": "de"
    }
    
    selected_language = st.selectbox(
        "文字起こしする言語を選択してください：",
        list(languages.keys()),
        index=0
    )
    
    uploaded_file = st.file_uploader(
        "ファイルを選択してください",
        type=['mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac', 'wma']
    )
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as temp_audio:
            temp_audio.write(uploaded_file.read())
            audio_path = temp_audio.name
        
        if st.button("文字起こしを開始"):
            try:
                with st.spinner("文字起こしを実行中..."):
                    transcribed_text = transcribe_audio(
                        audio_path,
                        languages[selected_language]
                    )
                    
                    st.success("文字起こしが完了しました！")
                    
                    st.text_area(
                        "文字起こし結果：",
                        transcribed_text,
                        height=300
                    )
                    
                    st.download_button(
                        label="テキストファイルをダウンロード",
                        data=transcribed_text,
                        file_name="transcription.txt",
                        mime="text/plain"
                    )
            
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
            
            finally:
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

if __name__ == "__main__":
    main()