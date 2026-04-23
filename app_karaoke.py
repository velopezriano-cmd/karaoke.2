import streamlit as st
import os
import re
import json
import subprocess
import syncedlyrics

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Vega's Karaoke Streamlit", page_icon="🎤", layout="centered")

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

st.title("🎤 Escenario Karaoke")
st.write("Escribe la canción y el artista para generar el ritmo y la letra.")

# --- ENTRADA DE DATOS ---
col1, col2 = st.columns(2)
with col1:
    cancion = st.text_input("🎵 Canción", placeholder="Ej: Hentai")
with col2:
    artista = st.text_input("🎤 Artista", placeholder="Ej: Rosalía")

if st.button("🚀 PREPARAR KARAOKE"):
    if cancion and artista:
        with st.spinner("🎸 Descargando ritmo (esto evita el error 403)..."):
            try:
                audio_file = "ritmo_final.mp3"
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                
                query = f"ytsearch1:{cancion} {artista} karaoke instrumental version"
                
                # --- SOLUCIÓN PUNTO 2: CONFIGURACIÓN ANTIBLOQUEO ---
                resultado = subprocess.run([
                    "yt-dlp", 
                    "-x", 
                    "--audio-format", "mp3", 
                    "--audio-quality", "0", 
                    "--no-check-certificate", 
                    "--prefer-free-formats",
                    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "-o", audio_file, 
                    query
                ], capture_output=True, text=True)

                # Verificar si se descargó
                if not os.path.exists(audio_file):
                    st.error("❌ Error al descargar de YouTube (HTTP 403 o similar).")
                    with st.expander("Ver detalles técnicos del error"):
                        st.code(resultado.stderr)
                    st.stop()

                # --- BÚSQUEDA DE LETRA ---
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

                    # Mostrar audio
                    audio_bytes = open(audio_file, 'rb').read()
                    st.audio(audio_bytes, format='audio/mp3')

                    # Pantalla de letra y JavaScript
                    st.markdown(f"""
                        <div id="karaoke-screen" style="background: black; padding: 40px; border-radius: 20px; border: 4px solid #1DB954; text-align: center; margin-top: 20px; min-height: 200px; display: flex; flex-direction: column; justify-content: center;">
                            <h1 id="lyric-text" style="color: white; font-family: sans-serif; font-size: 40px; margin: 0;">¡Dale al Play!</h1>
                            <p id="lyric-next" style="color: #535353; font-family: sans-serif; font-size: 20px; margin-top: 20px;"></p>
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
                    st.warning("No se encontró letra sincronizada.")
                    st.audio(audio_file)

            except Exception as e:
                st.error(f"Error inesperado: {e}")
    else:
        st.info("Introduce canción y artista.")
