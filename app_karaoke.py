import streamlit as st
import re
import json
import syncedlyrics
from googleapiclient.discovery import build

# --- CONFIGURACIÓN ---
API_KEY = "AIzaSyDZgLBFuQeqBrEDc4OQrjFGkdGkuJNW73o"

st.set_page_config(page_title="Vega's Karaoke Pure Rhythm", page_icon="🎤", layout="centered")

# Estilo Spotify Dark con toques neón
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stTextInput > div > div > input { background-color: #282828; color: white; border: 1px solid #1DB954; }
    .stButton>button { 
        background-color: #1DB954; color: white; border-radius: 50px; font-weight: bold; width: 100%;
        box-shadow: 0 4px 15px rgba(29, 185, 84, 0.3);
    }
    .lyric-box {
        background: rgba(0,0,0,0.8); padding: 30px; border-radius: 20px; 
        border: 2px solid #1DB954; text-align: center; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 Karaoke Pure Rhythm")
st.write("Filtros avanzados para asegurar versiones sin voz.")

col1, col2 = st.columns(2)
with col1:
    cancion = st.text_input("🎵 Canción", placeholder="Ej: Hentai")
with col2:
    artista = st.text_input("🎤 Artista", placeholder="Ej: Rosalía")

def buscar_videos_api(query):
    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        # Filtro agresivo: añadimos términos negativos para evitar voces
        terminos_negativos = "-vocal -cover -lyrics -original -remix"
        query_pro = f"{query} instrumental karaoke official {terminos_negativos}"
        
        request = youtube.search().list(
            q=query_pro, 
            part='snippet', 
            maxResults=3, # Traemos 3 opciones por si una tiene voz
            type='video',
            relevanceLanguage='es'
        )
        response = request.execute()
        return response.get('items', [])
    except: return []

if st.button("🚀 GENERAR ESCENARIO"):
    if cancion and artista:
        with st.spinner("🔍 Buscando la mejor versión instrumental..."):
            videos = buscar_videos_api(f"{cancion} {artista}")
            lrc_data = syncedlyrics.search(f"{cancion} {artista}", providers=['lrclib'])

            if videos and lrc_data:
                # Si hay varias opciones, dejamos que el usuario elija si la primera no le gusta
                opciones = {v['snippet']['title']: v['id']['videoId'] for v in videos}
                seleccion = st.selectbox("🎸 ¿No es el ritmo correcto? Prueba otra versión:", list(opciones.keys()))
                video_id = opciones[seleccion]

                # Parsear letras
                lyrics_list = []
                for line in lrc_data.split('\n'):
                    match = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                    if match:
                        time_sec = int(match.group(1)) * 60 + float(match.group(2))
                        text = match.group(3).strip()
                        if text: lyrics_list.append({'time': time_sec, 'text': text})
                
                lyrics_json = json.dumps(lyrics_list)

                # Reproductor
                st.video(f"https://www.youtube.com/watch?v={video_id}")

                # Pantalla de letras
                st.markdown(f"""
                    <div class="lyric-box">
                        <h1 id="lyric-text" style="color: white; font-size: 38px; font-weight: bold; min-height: 60px;">¡Dale al Play!</h1>
                        <p id="lyric-next" style="color: #b3b3b3; font-size: 20px;"></p>
                    </div>

                    <script>
                        const startSync = () => {{
                            const video = window.parent.document.querySelector('video');
                            const lyrics = {lyrics_json};
                            const display = window.parent.document.getElementById('lyric-text');
                            const nextDisplay = window.parent.document.getElementById('lyric-next');

                            if (video) {{
                                video.ontimeupdate = () => {{
                                    const time = video.currentTime;
                                    let current = -1;
                                    for (let i = 0; i < lyrics.length; i++) {{
                                        if (time >= lyrics[i].time) current = i;
                                        else break;
                                    }}
                                    if (current !== -1) {{
                                        display.innerText = lyrics[current].text;
                                        nextDisplay.innerText = lyrics[current+1] ? "Próximo: " + lyrics[current+1].text : "♪ ♪ ♪";
                                    }}
                                }};
                            }}
                        }};
                        setTimeout(startSync, 3000);
                    </script>
                """, unsafe_allow_html=True)
            else:
                st.error("No se encontró una versión instrumental válida o la letra.")
