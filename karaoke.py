import streamlit as st
import syncedlyrics
import re
import os
import subprocess
import time

# --- CONFIGURACIÓN DE ESTILO ---
st.set_page_config(page_title="Spotify Karaoke TFM", page_icon="🎤")

st.markdown("""
    <style>
    .karaoke-box {
        background-color: #121212;
        padding: 30px;
        border-radius: 20px;
        border: 4px solid #1DB954;
        text-align: center;
        margin-top: 20px;
    }
    .lyrics-main {
        color: white;
        font-size: 40px;
        font-weight: bold;
        line-height: 1.2;
    }
    .lyrics-next {
        color: #535353;
        font-size: 20px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎤 Modo Karaoke Sincronizado")
st.write("Introduce una canción para buscar su ritmo y letra.")

# --- ENTRADAS DE USUARIO ---
col1, col2 = st.columns(2)
with col1:
    cancion_input = st.text_input("🎵 Nombre de la canción:", placeholder="Ej: Mood")
with col2:
    artista_input = st.text_input("🎤 Artista:", placeholder="Ej: 24kGoldn")

# --- LÓGICA DE PROCESAMIENTO ---
if st.button("🚀 Iniciar Escenario"):
    if cancion_input and artista_input:
        with st.status("Preparando el escenario..."):
            
            # 1. Buscar Letra Sincronizada (LRC)
            st.write("🔎 Buscando letra sincronizada...")
            lrc_data = syncedlyrics.search(f"{cancion_input} {artista_input}", providers=['lrclib'])
            
            if not lrc_data:
                st.error("❌ No se encontró letra sincronizada para esta canción.")
            else:
                # 2. Descargar Audio Instrumental (usando yt-dlp)
                st.write("🎸 Extrayendo ritmo instrumental...")
                audio_file = "karaoke_audio.mp3"
                
                # Comando para descargar (yt-dlp debe estar en requirements.txt)
                query_yt = f"ytsearch1:{cancion_input} {artista_input} karaoke instrumental"
                try:
                    # Borramos archivo previo si existe
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                    
                    # Descarga silenciosa
                    subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio_file, query_yt], capture_output=True)
                    
                    # 3. Procesar líneas de tiempo
                    lineas = []
                    for line in lrc_data.split('\n'):
                        match = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                        if match:
                            t = int(match.group(1)) * 60 + float(match.group(2))
                            txt = match.group(3).strip()
                            if txt: lineas.append((t, txt))

                    # --- INTERFAZ DE REPRODUCCIÓN ---
                    st.success("¡Todo listo! Dale al PLAY abajo para empezar.")
                    
                    # Mostramos el reproductor de audio
                    audio_bytes = open(audio_file, 'rb').read()
                    st.audio(audio_bytes, format='audio/mp3')

                    st.info("Nota: En Streamlit, la letra no se puede 'auto-scrollear' sincronizada perfectamente con el audio como en un vídeo de YouTube debido a las limitaciones del navegador, pero aquí tienes la letra completa para seguirla:")
                    
                    # Mostramos la letra completa con scroll elegante
                    letra_limpia = re.sub(r'\[.*?\]', '', lrc_data)
                    st.text_area("Letra de la canción", value=letra_limpia, height=400)

                except Exception as e:
                    st.error(f"Error al procesar el audio: {e}")
    else:
        st.warning("Por favor, rellena ambos campos.")

# --- INSTRUCCIONES PARA GITHUB ---
with st.expander("ℹ️ Instrucciones para que esto funcione en GitHub"):
    st.markdown("""
    1. Asegúrate de tener un archivo **requirements.txt** en tu repo con:
       ```
       streamlit
       syncedlyrics
       yt-dlp
       ```
    2. Importante: **Streamlit Cloud** a veces bloquea las descargas de YouTube. Si el audio falla, es por restricciones del servidor.
    """)
