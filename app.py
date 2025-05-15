import yt_dlp
from yt_dlp.utils import download_range_func
from pydub import AudioSegment
from scipy.io.wavfile import write
import tempfile
import numpy as np
import os
import streamlit as st
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
from streamlit_chromadb_connection.chromadb_connection import ChromadbConnection


YDL_OPTS = {
    'format': 'bestaudio/best',
    # 'outtmpl': 'audio/%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }],
    'download_ranges': download_range_func(None, [(300, 360)]),
    "force_keyframes_at_cuts": True,
}

CHROMA_CONFIG = {
    "client": "PersistentClient",
    "path": "audio/chroma_db",
}


AUDIO_DIR = "audio"

def fetch_audio_from_text(prompt, filename="output.wav"):
    conn = st.connection("chromadb", type=ChromadbConnection, **CHROMA_CONFIG)
    collection_name = "audio-collection"
    results = conn.query(collection_name=collection_name, query=prompt, num_results_limit=20)

    yt_ids = results["ids"][0]
    captions = results["documents"][0]

    sample_idx = np.random.choice(range(len(yt_ids)), size=5, replace=False).tolist()
    non_sample_idx = list(set(range(len(yt_ids))) - set(sample_idx))
    final_audios = []

    existing_files = os.listdir(AUDIO_DIR) + os.listdir(st.session_state.dir)

    while len(sample_idx) > 0:
        idx = sample_idx.pop(0)

        if f"{yt_ids[idx]}.wav" not in existing_files:
            directory = st.session_state.dir
            url = f"https://www.youtube.com/watch?v={yt_ids[idx]}"
            with yt_dlp.YoutubeDL({'outtmpl': str(directory) + '/%(id)s.%(ext)s', **YDL_OPTS }) as ydl:
                try:
                    if any("war" in captions[idx].lower() for word in ("war", "battle", "bunker")):
                        raise Exception("war-related content")
                    ydl.download([url])
                except Exception as e:
                    if len(non_sample_idx) > 0:
                        sample_idx.append(non_sample_idx.pop(0))
                    print(f"Error downloading {url}: {e}")
                    continue
        else:
            directory = AUDIO_DIR

        final_audios.append({"path": f"{directory}/{yt_ids[idx]}.wav", "caption": captions[idx]})

    print("final_audios", final_audios)
    return final_audios

st.set_page_config(page_title="🧘‍♀️ meditation mood maker", page_icon=":musical_note:")
st.title("🧘‍♀️ meditation mood maker")

st.write("this app generates meditative soundscapes based on your mood. it retrieves from a collection of ambient sounds and allows you to create a custom mix. if you like any sounds, you can download them and put them in your own playlists for you to enjoy during mindfulness sessions.")
st.write("this was inspired by Inez Insuelo's lecture on using sound vibrations for meditation.")

mood = st.text_input(
    "what kind of meditative atmosphere do you want to create? use descriptive language:",
    "calm, exploratory, fireside relaxation"
)

if "sounds" not in st.session_state:
    st.session_state.sounds = []
    st.session_state.dir = tempfile.mkdtemp()
    print("temp dir", st.session_state.dir)

if st.button("generate soundscapes"):
    st.session_state.sounds = []
    with st.spinner("generating meditative soundscapes..."):
        st.session_state.sounds = fetch_audio_from_text(mood)

if len(st.session_state.sounds) > 0:
    selected_sounds = []

    st.subheader("suggested ambient sounds:")
    
    for i, sound in enumerate(st.session_state.sounds):
        col1, col2 = st.columns([1, 3])
        with col1:
            selected = st.checkbox(sound["caption"], key=f"chk_{i}")
        with col2:
            st.audio(sound["path"], format="audio/wav")
        if selected:
            selected_sounds.append(sound)            

    if st.button("mix selected sounds") and len(selected_sounds) > 1:
        with st.spinner("crafting meditation mix..."):
            base = AudioSegment.silent(duration=60000)  # 1 minute of silence

            for sound in selected_sounds:
                audio = AudioSegment.from_wav(sound["path"])
                audio -= 10  # Lower volume so multiple layers aren't too loud
                base = base.overlay(audio)

            # Save mixed audio to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                mixed_path = f.name
                base.export(mixed_path, format="wav")

            st.subheader("mixed ambience 🎧")
            st.audio(mixed_path, format="audio/wav")
    else:
        st.info("select at least two sounds to mix and click mix!")