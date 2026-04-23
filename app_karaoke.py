import streamlit as st
import os
import re
import json
import subprocess
import syncedlyrics

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Vega's Karaoke Streamlit", page_icon="🎤", layout="centered")

# CSS para estilo Spotify Dark
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    .stTextInput > div > div > input { background-color: #282828; color: white; border: 1px solid #1DB954; }
    .stButton>button { 
        background-color: #1DB954; color: white; border-radius: 50px; 
        font-weight: bold; border: none; padding: 12px 24px; width: 100%;
    }
    .stButton>button:hover { background-color: #1ed760; color: white; border: none; }
    h1, h2, h3, p { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 Escenario Karaoke")
st.write("Escribe el nombre de la canción y el artista para empezar el show.")

# --- ENTRADA DE DATOS ---
col1, col2 = st.columns(2)
with col1:
    cancion = st.text_input("🎵 Canción", placeholder="Ej: Hentai")
with col2:
    artista = st.text_input("🎤 Artista", placeholder="Ej: Rosalía")

if st.button("🚀 PREPARAR KARAOKE"):
    if cancion and artista:
        with st.spinner("🎸 Procesando pista instrumental y letras..."):
            try:
                # 1. Definir ruta del archivo
                audio_file = "ritmo_final.mp3"
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                
                # 2. Descarga de Audio con yt-dlp
                # Usamos filtros para asegurar que sea instrumental
                query = f"ytsearch1:{cancion} {artista} karaoke instrumental version"
                
                resultado = subprocess.run([
                    "yt-dlp", 
                    "-x", 
                    "--audio-format", "mp3", 
                    "--audio-quality", "0", 
                    "-o", audio_file, 
                    query
                ], capture_output=True, text=True)

                # Verificar si el archivo se creó correctamente
                if not os.path.exists(audio_file):
                    st.error("❌ No se pudo generar el archivo de audio.")
                    with st.expander("Ver detalles técnicos del error"):
                        st.code(resultado.stderr)
                    st.info("💡 Asegúrate de tener un archivo 'packages.txt' con 'ffmpeg' en tu GitHub.")
                    st.stop()

                # 3. Obtener Letras Sincronizadas
                lrc_data = syncedlyrics.search(f"{cancion} {artista}", providers=['lrclib'])
                
                if lrc_data:
                    # Convertir LRC a JSON para el script de sincronización
                    lyrics_list = []
                    for line in lrc_data.split('\n'):
                        match = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                        if match:
                            time_sec = int(match.group(1)) * 60 + float(match.group(2))
                            text = match.group(3).strip()
                            if text: lyrics_list.append({'time': time_sec, 'text': text})
                    
                    lyrics_json = json.dumps(lyrics_list)

                    # 4. Mostrar Reproductor de Audio
                    audio_bytes = open(audio_file, 'rb').read()
                    st.audio(audio_bytes, format='audio/mp3')

                    # 5. Contenedor de Letras y JavaScript de Sincronización
                    st.markdown(f"""
                        <div id="karaoke-screen" style="background: black; padding: 50px 20px; border-radius: 20px; border: 4px solid #1DB954; text-align: center; margin-top: 30px; min-height: 250px; display: flex; flex-direction: column; justify-content: center;">
                            <p style="color: #1DB954; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">Canta ahora:</p>
                            <h1 id="lyric-text" style="color: white; font-size: 42px; margin: 20px 0; line-height: 1.2;">¡Dale al Play arriba!</h1>
                            <div style="margin-top: 30px; border-top: 1px solid #333; padding-top: 20px;">
                                <p id="lyric-next" style="color: #6a6a6a; font-size: 20px; font-weight: normal;"></p>
                            </div>
                        </div>

                        <script>
                            // Función para sincronizar letras con el reproductor de Streamlit
                            const syncKaraoke = () => {{
                                const audio = window.parent.document.querySelector('audio');
                                const lyrics = {lyrics_json};
                                const textDisplay = window.parent.document.getElementById('lyric-text');
                                const nextDisplay = window.parent.document.getElementById('lyric-next');

                                if (audio) {{
                                    audio.ontimeupdate = () => {{
                                        const currentTime = audio.currentTime;
                                        let activeIdx = -1;

                                        for (let i = 0; i < lyrics.length; i++) {{
                                            if (currentTime >= lyrics[i].time) {{
                                                activeIdx = i;
                                            }} else {{
                                                break;
                                            }}
                                        }}

                                        if (activeIdx !== -1) {{
                                            textDisplay.innerText = lyrics[activeIdx].text;
                                            if (lyrics[activeIdx + 1]) {{
                                                nextDisplay.innerText = "Siguiente: " + lyrics[activeIdx + 1].text;
                                            }} else {{
                                                nextDisplay.innerText = "♪ (Fin) ♪";
                                            }}
                                        }}
                                    }};
                                }}
                            }};
                            
                            // Ejecutar sincronización
                            setTimeout(syncKaraoke, 1000);
                        </script>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ No se encontró letra sincronizada para esta canción. El audio sonará pero no habrá texto.")
                    st.audio(audio_file)

            except Exception as e:
                st.error(f"Error inesperado: {e}")
    else:
        st.info("Escribe algo arriba y pulsa el botón para empezar.")
