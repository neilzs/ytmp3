import streamlit as st
import yt_dlp
import os
import re
import time
from pathlib import Path

# Konfigurasi halaman
st.set_page_config(
    page_title="YouTube to MP3 Converter",
    page_icon="🎵",
    layout="centered"
)

# Fungsi untuk membersihkan nama file
def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_audio(url, bitrate="192"):
    try:
        with st.status("Downloading...", expanded=True) as status:
            # Buat folder temporer (sesuai best practice Streamlit Sharing)
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
                "extract_flat": False,
                "retries": 3,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                st.write("🔍 Getting video info...")
                info = ydl.extract_info(url, download=False)
                title = sanitize_filename(info.get('title', 'unknown'))
                
                st.write("📥 Downloading audio...")
                result = ydl.download([url])
                
                # Dapatkan nama file output
                temp_file = ydl.prepare_filename(info)
                final_file = temp_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                # Verifikasi file
                if not os.path.exists(final_file):
                    raise FileNotFoundError("Conversion failed - file not created")
                
                # Baca file sebagai binary
                with open(final_file, "rb") as f:
                    audio_bytes = f.read()
                
                # Hapus file temporer setelah dibaca
                if os.path.exists(final_file):
                    os.remove(final_file)
                
                status.update(label="Download complete!", state="complete", expanded=False)
                st.success(f"✅ {title}")
                
                # Tampilkan audio player
                st.audio(audio_bytes, format='audio/mp3')
                
                # Tombol download
                st.download_button(
                    label="⬇️ Download MP3",
                    data=audio_bytes,
                    file_name=f"{title}.mp3",
                    mime="audio/mp3",
                    key=f"dl_{title}"
                )
                
                return title

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

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
        if url:
            with st.spinner("Processing..."):
                download_audio(url, bitrate)
        else:
            st.warning("Please enter a YouTube URL")

# Catatan kaki
st.divider()
st.caption("""
⚠️ **Note**: 
- This tool uses yt-dlp and requires FFmpeg (already pre-installed on Streamlit Sharing)
- Files are temporarily stored during conversion and automatically deleted
- For educational purposes only
""")