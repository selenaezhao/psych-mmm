import yt_dlp
from yt_dlp.utils import download_range_func
from pydub import AudioSegment
from scipy.io.wavfile import write
import tempfile
import numpy as np
import os
import streamlit as st
from streamlit_chromadb_connection.chromadb_connection import ChromadbConnection


YDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': 'audio/%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }],
    'download_ranges': download_range_func(None, [(300, 360)]),
    "force_keyframes_at_cuts": True,
}

configuration = {
    "client": "PersistentClient",
    "path": "audio/chroma_db",
}

collection_name = "audio-collection"

AUDIO_DIR = "audio"

def fetch_audio_from_text(prompt, filename="output.wav"):
    conn = st.connection("chromadb", type=ChromadbConnection, **configuration)
    results = conn.query(collection_name=collection_name, query=prompt, num_results_limit=20)

    yt_ids = results["ids"][0]
    captions = results["documents"][0]

    sample_idx = np.random.choice(range(len(yt_ids)), size=5, replace=False).tolist()
    non_sample_idx = list(set(range(len(yt_ids))) - set(sample_idx))
    final_idx = []

    existing_files = os.listdir(AUDIO_DIR)

    while len(sample_idx) > 0:
        idx = sample_idx[0]

        if f"{yt_ids[idx]}.wav" not in existing_files:
            url = f"https://www.youtube.com/watch?v={yt_ids[idx]}"
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                try:
                    if "war" in captions[idx] or "battle" in captions[idx] or "bunker" in captions[idx]:
                        raise Exception("war-related content")
                    ydl.download([url])
                except Exception as e:
                    if len(non_sample_idx) > 0:
                        sample_idx.append(non_sample_idx[0])
                        non_sample_idx = non_sample_idx[1:]
                    print(f"Error downloading {url}: {e}")


        final_idx.append(idx)
        sample_idx = sample_idx[1:]

    return [{"id": yt_ids[idx], "caption": captions[idx]} for idx in final_idx]

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
            audio_path = os.path.join(AUDIO_DIR, f"{sound['id']}.wav")
            st.audio(audio_path, format="audio/wav")
        if selected:
            selected_sounds.append(sound)            

    if st.button("mix selected sounds") and len(selected_sounds) > 1:
        with st.spinner("crafting meditation mix..."):
            base = AudioSegment.silent(duration=60000)  # 1 minute of silence

            for sound in selected_sounds:
                audio = AudioSegment.from_wav(os.path.join(AUDIO_DIR, f"{sound['id']}.wav"))
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