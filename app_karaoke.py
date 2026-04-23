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
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 Karaoke Official Stream")
st.write("Versión de alta fidelidad con reproductor oficial.")

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

                # INTERFAZ DUAL: VIDEO + LETRAS
                st.markdown(f"""
                    <div id="video-placeholder"></div>
                    <div style="background: black; padding: 30px; border-radius: 20px; border: 3px solid #1DB954; text-align: center; margin-top: 20px;">
                        <h1 id="lyric-text" style="color: white; font-size: 35px; min-height: 50px;">¡Dale al Play!</h1>
                        <p id="lyric-next" style="color: #535353; font-size: 18px;"></p>
                    </div>

                    <script src="https://www.youtube.com/iframe_api"></script>
                    <script>
                        var player;
                        const lyrics = {lyrics_json};
                        
                        function onYouTubeIframeAPIReady() {{
                            player = new YT.Player('video-placeholder', {{
                                height: '360',
                                width: '100%',
                                videoId: '{video_id}',
                                events: {{
                                    'onStateChange': onPlayerStateChange
                                }}
                            }});
                        }}

                        function onPlayerStateChange(event) {{
                            if (event.data == YT.PlayerState.PLAYING) {{
                                setInterval(function() {{
                                    var currentTime = player.getCurrentTime();
                                    var activeIdx = -1;
                                    for (let i = 0; i < lyrics.length; i++) {{
                                        if (currentTime >= lyrics[i].time) activeIdx = i;
                                        else break;
                                    }}
                                    if (activeIdx !== -1) {{
                                        window.parent.document.getElementById('lyric-text').innerText = lyrics[activeIdx].text;
                                        window.parent.document.getElementById('lyric-next').innerText = lyrics[activeIdx+1] ? "Siguiente: " + lyrics[activeIdx+1].text : "";
                                    }}
                                }}, 500);
                            }}
                        }}
                    </script>
                """, unsafe_allow_html=True)
            else:
                st.error("No se pudo encontrar el video o la letra.")
