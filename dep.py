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

def get_ydl_opts(bitrate):
    """Konfigurasi yt-dlp dengan headers dan parameter khusus"""
    return {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate,
        }],
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': False,
        'extract_flat': False,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.youtube.com/',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'player_skip': ['configs'],
            }
        },
    }

def download_audio(url, bitrate="192"):
    try:
        with st.status("Processing...", expanded=True) as status:
            st.write("🔍 Connecting to YouTube...")
            
            ydl_opts = get_ydl_opts(bitrate)
            audio_buffer = BytesIO()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Ekstrak info dulu untuk validasi
                info = ydl.extract_info(url, download=False)
                title = sanitize_filename(info.get('title', 'unknown'))
                
                st.write("📥 Downloading audio (this may take a while)...")
                
                # Download dengan retry otomatis
                ydl.download([url])
                
                # Proses file hasil download
                temp_filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                if os.path.exists(temp_filename):
                    with open(temp_filename, "rb") as f:
                        audio_buffer.write(f.read())
                    os.remove(temp_filename)
                else:
                    raise FileNotFoundError("Conversion failed - no output file")
                
                audio_bytes = audio_buffer.getvalue()
                
                if len(audio_bytes) == 0:
                    raise ValueError("Empty audio file - possibly blocked by YouTube")
                
                status.update(label="Conversion complete!", state="complete", expanded=False)
                return audio_bytes, title

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None, None

# UI Streamlit
st.title("🎵 YouTube to MP3 Converter")
st.markdown("Convert YouTube videos to MP3 audio files")

url = st.text_input("YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")

col1, col2 = st.columns([3, 1])
with col1:
    bitrate = st.select_slider("Audio Quality:", options=["128", "192", "256", "320"], value="192")
with col2:
    if st.button("Convert", type="primary"):
        if url and ("youtube.com/watch?" in url or "youtu.be/" in url):
            with st.spinner("Processing your request..."):
                audio_bytes, title = download_audio(url, bitrate)
                
                if audio_bytes and title:
                    st.success(f"✅ Successfully converted: {title}")
                    st.audio(audio_bytes, format='audio/mp3')
                    
                    st.download_button(
                        label="⬇️ Download MP3",
                        data=audio_bytes,
                        file_name=f"{title}.mp3",
                        mime="audio/mp3",
                        key=f"dl_{hash(title)}"
                    )
        else:
            st.warning("Please enter a valid YouTube URL")

# Footer
st.divider()
st.caption("""
⚠️ **Note**: 
- For personal use only (respect copyright laws)
- May not work for some age-restricted or private videos
- Conversion speed depends on video length
""")
