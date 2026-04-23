import streamlit as st
import os
import re
import json
import subprocess
import syncedlyrics

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Vega's Karaoke SoundCloud", page_icon="🎤", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stTextInput > div > div > input { background-color: #282828; color: white; border: 1px solid #ff5500; }
    .stButton>button { 
        background-color: #ff5500; color: white; border-radius: 50px; 
        font-weight: bold; border: none; padding: 12px 24px; width: 100%;
    }
    .stButton>button:hover { background-color: #ff8800; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 Escenario Karaoke (v. Soundcloud)")
st.write("Usando SoundCloud para evitar los bloqueos de YouTube.")

col1, col2 = st.columns(2)
with col1:
    cancion = st.text_input("🎵 Canción", placeholder="Ej: Ni borracho")
with col2:
    artista = st.text_input("🎤 Artista", placeholder="Ej: Quevedo")

if st.button("🚀 PREPARAR KARAOKE"):
    if cancion and artista:
        with st.spinner("📡 Buscando ritmo en SoundCloud..."):
            try:
                audio_file = "ritmo_final.mp3"
                if os.path.exists(audio_file): os.remove(audio_file)
                
                # BUSCAMOS EN SOUNDCLOUD (Mucho menos bloqueos)
                query = f"scsearch1:{cancion} {artista} karaoke instrumental"
                
                resultado = subprocess.run([
                    "yt-dlp", 
                    "-x", "--audio-format", "mp3", 
                    "--no-check-certificate",
                    "-o", audio_file, 
                    query
                ], capture_output=True, text=True)

                if os.path.exists(audio_file):
                    # BÚSQUEDA DE LETRA
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
                            <div id="karaoke-screen" style="background: black; padding: 40px; border-radius: 20px; border: 4px solid #ff5500; text-align: center; margin-top: 20px;">
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
                        st.warning("Letra no encontrada, pero tienes el audio.")
                        st.audio(audio_file)
                else:
                    st.error("No se pudo obtener el audio ni siquiera de SoundCloud.")
                    with st.expander("Error técnico"):
                        st.code(resultado.stderr)

            except Exception as e:
                st.error(f"Error: {e}")
