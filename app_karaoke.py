import streamlit as st
import os
import re
import json
import subprocess
import syncedlyrics
from googleapiclient.discovery import build

# --- CONFIGURACIÓN ---
# PEGA TU CLAVE AQUÍ ABAJO:
API_KEY = "AIzaSyDZgLBFuQeqBrEDc4OQrjFGkdGkuJNW73o"

st.set_page_config(page_title="Vega's Karaoke PRO", page_icon="🎤", layout="centered")

# Estilo visual Spotify Dark
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
st.write("Búsqueda mediante API oficial de YouTube (Sin bloqueos)")

# --- ENTRADA DE DATOS ---
col1, col2 = st.columns(2)
with col1:
    cancion = st.text_input("🎵 Canción", placeholder="Ej: Ni borracho")
with col2:
    artista = st.text_input("🎤 Artista", placeholder="Ej: Quevedo")

def buscar_video_api(query):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=1,
            type='video'
        )
        response = request.execute()
        if response['items']:
            video_id = response['items'][0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"
        return None
    except Exception as e:
        st.error(f"Error en la API de Google: {e}")
        return None

if st.button("🚀 PREPARAR KARAOKE"):
    if cancion and artista:
        with st.spinner("📡 Consultando a Google y descargando ritmo..."):
            try:
                # 1. Buscar el video oficial con la API
                termino = f"{cancion} {artista} karaoke instrumental"
                url_video = buscar_video_api(termino)
                
                if not url_video:
                    st.error("No se encontró ningún video con ese nombre.")
                    st.stop()

                audio_file = "ritmo_final.mp3"
                if os.path.exists(audio_file): os.remove(audio_file)
                
                # 2. Descargar el audio (ya con el link directo es más difícil que falle)
                resultado = subprocess.run([
                    "yt-dlp", "-x", "--audio-format", "mp3", 
                    "--no-check-certificate", 
                    "-o", audio_file, 
                    url_video
                ], capture_output=True, text=True)

                if not os.path.exists(audio_file):
                    st.error("❌ Falló la descarga del audio.")
                    with st.expander("Detalles"): st.code(resultado.stderr)
                    st.stop()

                # 3. Buscar letra
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
                    audio_bytes = open(audio_file, 'rb').read()
                    st.audio(audio_bytes, format='audio/mp3')

                    st.markdown(f"""
                        <div id="karaoke-screen" style="background: black; padding: 40px; border-radius: 20px; border: 4px solid #1DB954; text-align: center; margin-top: 20px;">
                            <h1 id="lyric-text" style="color: white; font-size: 40px; margin: 0;">¡Dale al Play!</h1>
                            <p id="lyric-next" style="color: #535353; font-size: 20px; margin-top: 20px;"></p>
                        </div>
                        <script>
                            const audio = window.parent.document.querySelector('audio');
                            const lyrics = {lyrics_json};
                            const display = window.parent.document.getElementById('lyric-text');
                            const nextDisplay = window.parent.document.getElementById('lyric-next');
                            if (audio) {{
                                audio.ontimeupdate = () => {{
                                    let activeIdx = -1;
                                    for (let i = 0; i < lyrics.length; i++) {{
                                        if (audio.currentTime >= lyrics[i].time) activeIdx = i;
                                        else break;
                                    }}
                                    if (activeIdx !== -1) {{
                                        display.innerText = lyrics[activeIdx].text;
                                        nextDisplay.innerText = lyrics[activeIdx + 1] ? "Siguiente: " + lyrics[activeIdx + 1].text : "";
                                    }}
                                }};
                            }}
                        </script>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Letra no encontrada.")
                    st.audio(audio_file)

            except Exception as e:
                st.error(f"Error inesperado: {e}")
