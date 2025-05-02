import streamlit as st
import yt_dlp
import os
import re
from io import BytesIO

# Konfigurasi halaman
st.set_page_config(
    page_title="YouTube MP3 Converter",
    page_icon="🎵",
    layout="centered"
)

# Fungsi untuk membersihkan nama file
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def setup_ffmpeg():
    """Menggunakan FFmpeg bawaan Streamlit Sharing"""
    return {"ffmpeg_location": "/usr/bin/ffmpeg"} if os.path.exists("/usr/bin/ffmpeg") else {}

def download_audio(url, bitrate="192"):
    try:
        with st.status("Processing...", expanded=True) as status:
            # Setup FFmpeg
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "%(title)s.%(ext)s",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate,
                }],
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                **setup_ffmpeg()
            }

            st.write("🔍 Getting video info...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = sanitize_filename(info.get('title', 'unknown'))
                
                st.write("📥 Downloading audio...")
                
                # Download ke memory buffer
                audio_buffer = BytesIO()
                ydl.download([url])
                temp_filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                if os.path.exists(temp_filename):
                    with open(temp_filename, "rb") as f:
                        audio_buffer.write(f.read())
                    os.remove(temp_filename)
                else:
                    raise FileNotFoundError("Conversion failed")
                
                audio_bytes = audio_buffer.getvalue()
                
                if not audio_bytes:
                    raise ValueError("Empty audio file")
                
                status.update(label="Conversion complete!", state="complete", expanded=False)
                return audio_bytes, title

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None, None

# UI Streamlit
st.title("YouTube to MP3 Converter 🎵")
st.markdown("Convert YouTube videos to MP3 in your browser")

url = st.text_input("YouTube URL:", placeholder="https://www.youtube.com/watch?v=...", key="url_input")

col1, col2 = st.columns([3, 1])
with col1:
    bitrate = st.select_slider("Quality:", options=["128", "192", "256", "320"], value="192")
with col2:
    convert_btn = st.button("Convert", type="primary")

if convert_btn:
    if url:
        if "youtube.com/watch?" in url or "youtu.be/" in url:
            audio_bytes, title = download_audio(url, bitrate)
            
            if audio_bytes and title:
                st.success(f"✅ {title}")
                st.audio(audio_bytes, format='audio/mp3')
                
                # Tombol download di luar form
                st.download_button(
                    label="⬇️ Download MP3",
                    data=audio_bytes,
                    file_name=f"{title}.mp3",
                    mime="audio/mp3",
                    key=f"dl_{hash(title)}"  # Key unik untuk setiap download
                )
        else:
            st.warning("Please enter a valid YouTube URL")
    else:
        st.warning("Please enter a URL")

# Footer
st.divider()
st.caption("""
⚠️ **Note**: 
- Works with videos under 15 minutes
- No files are stored permanently
- Conversion may take a few moments
""")
