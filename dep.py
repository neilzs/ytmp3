import streamlit as st
import yt_dlp
import os
import re
from io import BytesIO
import random

# Konfigurasi halaman
st.set_page_config(
    page_title="YT to MP3 Converter Pro",
    page_icon="🎧",
    layout="centered"
)

# Fungsi untuk membersihkan nama file
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_random_user_agent():
    """Generate random user agent untuk menghindari blokir"""
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    ]
    return random.choice(agents)

def get_ydl_opts(bitrate):
    """Konfigurasi yt-dlp dengan berbagai bypass"""
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
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['js', 'configs'],
                'skip': ['dash', 'hls']
            }
        },
        'socket_timeout': 30,
        'retries': 3,
        'throttled_rate': '1M',
        'force_ipv4': True,
        'geo_bypass': True,
        'geo_bypass_country': 'US'
    }

def try_alternative_download(url, bitrate):
    """Mencoba berbagai alternatif download"""
    attempts = [
        {'format': 'bestaudio[ext=m4a]'},
        {'format': 'worstaudio'},
        {'extractor_args': {'youtube': {'player_client': ['ios']}},
        {'extractor_args': {'youtube': {'player_client': ['tv_embedded']}}
    ]
    
    for attempt in attempts:
        try:
            opts = {**get_ydl_opts(bitrate), **attempt}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_buffer = BytesIO()
                ydl.download([url])
                
                temp_filename = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                if os.path.exists(temp_filename):
                    with open(temp_filename, "rb") as f:
                        audio_buffer.write(f.read())
                    os.remove(temp_filename)
                    return audio_buffer.getvalue(), info.get('title', 'unknown')
        except Exception as e:
            continue
    return None, None

def download_audio(url, bitrate="192"):
    try:
        with st.status("🔄 Processing...", expanded=True) as status:
            st.write("🔍 Connecting to YouTube...")
            
            # Coba metode utama dulu
            audio_bytes, title = try_alternative_download(url, bitrate)
            
            if not audio_bytes:
                raise Exception("All download methods failed")
            
            status.update(label="✅ Conversion complete!", state="complete", expanded=False)
            return audio_bytes, title

    except Exception as e:
        st.error(f"❌ Failed to download: {str(e)}")
        return None, None

# UI Streamlit
st.title("🎧 YouTube Audio Extractor Pro")
st.markdown("""
<div style="background-color:#f0f2f6;padding:10px;border-radius:10px">
⚠️ <b>Note:</b> For educational purposes only. Respect copyright laws.
</div>
""", unsafe_allow_html=True)

url = st.text_input("", placeholder="Paste YouTube URL here...")

col1, col2 = st.columns([3, 1])
with col1:
    bitrate = st.select_slider("Quality:", options=["128", "192", "256", "320"], value="192")
with col2:
    if st.button("Extract Audio", type="primary", use_container_width=True):
        if url and ("youtube.com" in url or "youtu.be" in url):
            with st.spinner("Processing..."):
                audio_bytes, title = download_audio(url, bitrate)
                
                if audio_bytes and title:
                    st.success(f"**{title}**")
                    st.audio(audio_bytes, format='audio/mp3')
                    
                    st.download_button(
                        label="Download MP3",
                        data=audio_bytes,
                        file_name=f"{title}.mp3",
                        mime="audio/mp3",
                        type="primary"
                    )
        else:
            st.warning("Please enter a valid YouTube URL")

# Footer
st.divider()
st.caption("""
ℹ️ Tips: If download fails, try again later or use a different video.
""")
