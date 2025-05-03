import streamlit as st
import yt_dlp
import os
import re
from pathlib import Path

# Konfigurasi halaman
st.set_page_config(
    page_title="YouTube to MP3 Converter",
    page_icon="🎵",
    layout="centered"
)

# Fungsi sanitasi nama file
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

# Validasi URL
def is_valid_youtube_url(url):
    return re.match(r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$', url) is not None

def download_audio(url, bitrate="192"):
    try:
        with st.status("Downloading...", expanded=True) as status:
            temp_dir = "temp_downloads"
            os.makedirs(temp_dir, exist_ok=True)

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate,
                }],
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                st.write("🔍 Getting video info...")
                info = ydl.extract_info(url, download=False)
                title = sanitize_filename(info.get('title', 'unknown'))

                st.write("📥 Downloading audio...")
                ydl.download([url])

                temp_file = ydl.prepare_filename(info)
                base = Path(temp_file).with_suffix('')
                final_file = None
                for ext in ['.mp3', '.webm', '.m4a']:
                    test_file = str(base) + ext
                    if os.path.exists(test_file):
                        final_file = test_file
                        break

                if not final_file or not os.path.exists(final_file):
                    raise FileNotFoundError("Audio file not found after conversion")

                with open(final_file, "rb") as f:
                    audio_bytes = f.read()

                os.remove(final_file)

                status.update(label="Download complete!", state="complete", expanded=False)
                st.success(f"✅ {title}")

                return title, audio_bytes

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None, None

# UI Streamlit
st.title("YouTube to MP3 Converter 🎵")
st.write("Convert YouTube videos to high-quality MP3 audio")

with st.form("converter_form"):
    url = st.text_input("YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        bitrate = st.selectbox("Audio Quality:", ["128", "192", "256", "320"], index=1)
    with col2:
        st.write("")  # Spacer
        submitted = st.form_submit_button("Convert", type="primary")

if submitted:
    if url and is_valid_youtube_url(url):
        with st.spinner("Processing..."):
            title, audio_bytes = download_audio(url, bitrate)

            if audio_bytes:
                st.audio(audio_bytes, format='audio/mp3')
                st.download_button(
                    label="⬇️ Download MP3",
                    data=audio_bytes,
                    file_name=f"{title}.mp3",
                    mime="audio/mp3",
                    key=f"dl_{title}"
                )


st.divider()
st.caption("""
⚠️ **Note**: This tool uses yt-dlp and FFmpeg (must be installed on your system).
""")
