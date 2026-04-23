import streamlit as st
import os
import re
import json
import subprocess
import syncedlyrics

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Vega's Karaoke", page_icon="🎤", layout="centered")

# Estilo visual estilo Spotify Dark
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stTextInput > div > div > input { background-color: #282828; color: white; border: 1px solid #1DB954; }
    .stButton>button { 
        background-color: #1DB954; color: white; border-radius: 50px; 
        font-weight: bold; border: none; padding: 10px 20px;
    }
    .stButton>button:hover { background-color: #1ed760; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 Escenario Karaoke")
st.write("Introduce una canción para extraer el ritmo y sincronizar la letra.")

# --- ENTRADA DE DATOS ---
col1, col2 = st.columns(2)
with col1:
    cancion = st.text_input("Canción", placeholder="Ej: Hentai")
with col2:
    artista = st.text_input("Artista", placeholder="Ej: Rosalía")

if st.button("🚀 PREPARAR ESCENARIO"):
    if cancion and artista:
        with st.spinner("🎸 Buscando ritmo instrumental y sincronizando letras..."):
            try:
                # 1. Descarga de Audio (Filtro Instrumental)
                audio_file = "ritmo_karaoke.mp3"
                if os.path.exists(audio_file): os.remove(audio_file)
                
                query = f"ytsearch1:{cancion} {artista} karaoke instrumental version"
                subprocess.run([
                    "yt-dlp", "-x", "--audio-format", "mp3", 
                    "--audio-quality", "0", "-o", audio_file, query
                ], capture_output=True)

                # 2. Búsqueda de Letras Sincronizadas
                lrc_data = syncedlyrics.search(f"{cancion} {artista}", providers=['lrclib'])
                
                if lrc_data:
                    # Parsear LRC a JSON para JavaScript
                    lyrics_list = []
                    for line in lrc_data.split('\n'):
                        match = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                        if match:
                            time_sec = int(match.group(1)) * 60 + float(match.group(2))
                            text = match.group(3).strip()
                            if text: lyrics_list.append({'time': time_sec, 'text': text})
                    
                    lyrics_json = json.dumps(lyrics_list)

                    # 3. Interfaz de Audio y Letras
                    audio_bytes = open(audio_file, 'rb').read()
                    st.audio(audio_bytes, format='audio/mp3')

                    # El "Cerebro" en JavaScript para sincronización automática
                    st.markdown(f"""
                        <div id="display-box" style="background: black; padding: 40px; border-radius: 20px; border: 4px solid #1DB954; text-align: center; margin-top: 20px; min-height: 200px;">
                            <h1 id="lyric-text" style="color: white; font-family: sans-serif; font-size: 40px; margin: 0;">¡Dale al Play arriba!</h1>
                            <p id="lyric-next" style="color: #535353; font-family: sans-serif; font-size: 20px; margin-top: 20px;"></p>
                        </div>

                        <script>
                            // Localizamos el audio que Streamlit acaba de insertar
                            const audio = window.parent.document.querySelector('audio');
                            const lyrics = {lyrics_json};
                            const display = window.parent.document.getElementById('lyric-text');
                            const nextDisplay = window.parent.document.getElementById('lyric-next');

                            if (audio) {{
                                audio.ontimeupdate = () => {{
                                    let activeIdx = -1;
                                    for (let i = 0; i < lyrics.length; i++) {{
                                        if (audio.currentTime >= lyrics[i].time) {{
                                            activeIdx = i;
                                        }} else {{
                                            break;
                                        }}
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
                    st.error("No se encontró letra sincronizada para esta canción.")
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
    else:
        st.warning("Por favor, rellena ambos campos.")
