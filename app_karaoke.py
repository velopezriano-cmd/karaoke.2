import streamlit as st
import re
import json
import syncedlyrics
from googleapiclient.discovery import build

# --- CONFIGURACIÓN ---
API_KEY = "AIzaSyDZgLBFuQeqBrEDc4OQrjFGkdGkuJNW73o"

st.set_page_config(page_title="Vega's Karaoke Official", page_icon="🎤", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stTextInput > div > div > input { background-color: #282828; color: white; border: 1px solid #1DB954; }
    .stButton>button { 
        background-color: #1DB954; color: white; border-radius: 50px; font-weight: bold; width: 100%;
    }
    .lyric-box {
        background: black; padding: 30px; border-radius: 20px; 
        border: 3px solid #1DB954; text-align: center; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 Karaoke Official Stream")

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
            return response['items'][0]['id']['videoId']
        return None
    except: return None

if st.button("🚀 PREPARAR ESCENARIO"):
    if cancion and artista:
        with st.spinner("📡 Sincronizando escenario..."):
            video_id = buscar_video_api(f"{cancion} {artista} karaoke instrumental")
            lrc_data = syncedlyrics.search(f"{cancion} {artista}", providers=['lrclib'])

            if video_id and lrc_data:
                # Parsear letras
                lyrics_list = []
                for line in lrc_data.split('\n'):
                    match = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                    if match:
                        time_sec = int(match.group(1)) * 60 + float(match.group(2))
                        text = match.group(3).strip()
                        if text: lyrics_list.append({'time': time_sec, 'text': text})
                
                lyrics_json = json.dumps(lyrics_list)

                # 1. MOSTRAR EL VIDEO (Usando el widget nativo de Streamlit para que el Play sea visible)
                st.video(f"https://www.youtube.com/watch?v={video_id}")

                # 2. CAJA DE LETRAS (JavaScript busca el video nativo de Streamlit)
                st.markdown(f"""
                    <div class="lyric-box">
                        <h1 id="lyric-text" style="color: white; font-size: 35px; min-height: 50px;">¡Dale al Play arriba!</h1>
                        <p id="lyric-next" style="color: #535353; font-size: 18px;"></p>
                    </div>

                    <script>
                        // Función para buscar el video de Streamlit y sincronizar
                        const syncLyrics = () => {{
                            const video = window.parent.document.querySelector('video');
                            const lyrics = {lyrics_json};
                            const display = window.parent.document.getElementById('lyric-text');
                            const nextDisplay = window.parent.document.getElementById('lyric-next');

                            if (video) {{
                                video.ontimeupdate = () => {{
                                    const currentTime = video.currentTime;
                                    let activeIdx = -1;
                                    for (let i = 0; i < lyrics.length; i++) {{
                                        if (currentTime >= lyrics[i].time) activeIdx = i;
                                        else break;
                                    }}
                                    if (activeIdx !== -1) {{
                                        display.innerText = lyrics[activeIdx].text;
                                        nextDisplay.innerText = lyrics[activeIdx+1] ? "Siguiente: " + lyrics[activeIdx+1].text : "";
                                    }}
                                }};
                            }}
                        }};
                        // Intentamos conectar con el video tras un breve delay
                        setTimeout(syncLyrics, 2000);
                    </script>
                """, unsafe_allow_html=True)
            else:
                st.error("No se pudo encontrar el video o la letra sincronizada.")
