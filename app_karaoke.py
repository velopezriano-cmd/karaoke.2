import streamlit as st
import os
import re
import json
import subprocess
import syncedlyrics
from googleapiclient.discovery import build

# --- CONFIGURACIÓN ---
API_KEY = "AIzaSyDZgLBFuQeqBrEDc4OQrjFGkdGkuJNW73o"

st.set_page_config(page_title="Vega's Karaoke Ultimate", page_icon="🎤", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stTextInput > div > div > input { background-color: #282828; color: white; border: 1px solid #1DB954; }
    .stButton>button { 
        background-color: #1DB954; color: white; border-radius: 50px; 
        font-weight: bold; border: none; padding: 12px 24px; width: 100%;
    }
    .stButton>button:hover { background-color: #1ed760; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 Escenario Karaoke PRO")
st.write("Búsqueda con API oficial y descarga reforzada (Anti-403)")

col1, col2 = st.columns(2)
with col1:
    cancion = st.text_input("🎵 Canción", placeholder="Ej: Ni borracho")
with col2:
    artista = st.text_input("🎤 Artista", placeholder="Ej: Quevedo")

def buscar_video_api(query):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.search().list(q=query, part='snippet', maxResults=1, type='video')
        response = request.execute()
        if response['items']:
            video_id = response['items'][0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"
        return None
    except Exception as e:
        st.error(f"Error API Google: {e}")
        return None

if st.button("🚀 PREPARAR KARAOKE"):
    if cancion and artista:
        with st.spinner("📡 Obteniendo audio desde servidor seguro..."):
            try:
                # 1. Búsqueda oficial
                url_video = buscar_video_api(f"{cancion} {artista} karaoke instrumental")
                if not url_video:
                    st.error("No se encontró el video.")
                    st.stop()

                audio_file = "ritmo_final.mp3"
                if os.path.exists(audio_file): os.remove(audio_file)
                
                # 2. DESCARGA REFORZADA (Cambiamos el User Agent y el Cliente)
                resultado = subprocess.run([
                    "yt-dlp", 
                    "-x", "--audio-format", "mp3", 
                    "--no-check-certificate",
                    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "--extractor-args", "youtube:player_client=ios,mweb", # Estos dos son los más resistentes
                    "--force-ipv4", # YouTube bloquea más las IPs v6 de servidores
                    "-o", audio_file, 
                    url_video
                ], capture_output=True, text=True)

                if not os.path.exists(audio_file):
                    st.error("❌ YouTube sigue bloqueando. Intentando método alternativo...")
                    # Reintento con cliente Android si falla el primero
                    subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "--extractor-args", "youtube:player_client=android", "-o", audio_file, url_video])

                if os.path.exists(audio_file):
                    # 3. Letras
                    lrc_data = syncedlyrics.search(f"{cancion} {artista}", providers=['lrclib'])
                    if lrc_data:
                        lyrics_list = []
                        for line in lrc_data.split('\n'):
                            match = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                            if match:
                                time_sec = int(match.group(1)) * 60 + float(match.group(2))
                                text = match.group(3).strip()
                                if text: lyrics_list.append({'time': time_sec, 'text': text})
                        
                        lyrics_json = json.dumps(lyrics_list)
                        st.audio(open(audio_file, 'rb').read(), format='audio/mp3')

                        st.markdown(f"""
                            <div id="karaoke-screen" style="background: black; padding: 40px; border-radius: 20px; border: 4px solid #1DB954; text-align: center;">
                                <h1 id="lyric-text" style="color: white; font-size: 35px;">¡Play!</h1>
                                <p id="lyric-next" style="color: #535353;"></p>
                            </div>
                            <script>
                                const audio = window.parent.document.querySelector('audio');
                                const lyrics = {lyrics_json};
                                if (audio) {{
                                    audio.ontimeupdate = () => {{
                                        let idx = -1;
                                        for (let i=0; i<lyrics.length; i++) if (audio.currentTime >= lyrics[i].time) idx = i;
                                        if (idx !== -1) {{
                                            window.parent.document.getElementById('lyric-text').innerText = lyrics[idx].text;
                                            window.parent.document.getElementById('lyric-next').innerText = lyrics[idx+1] ? "Siguiente: " + lyrics[idx+1].text : "";
                                        }}
                                    }};
                                }}
                            </script>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Sin letra sincronizada.")
                        st.audio(audio_file)
                else:
                    st.error("No se pudo saltar el bloqueo de YouTube. Prueba otra canción.")
                    st.code(resultado.stderr)

            except Exception as e:
                st.error(f"Error: {e}")
