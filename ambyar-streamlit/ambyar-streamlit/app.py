import json
import random
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Ambyar", page_icon="🎵", layout="wide")

BASE = Path(__file__).parent.resolve()
GENRES = ["Koplo", "Dangdut", "Pop Jawa"]
MOODS = ["Patah hati", "Galau", "Nyesek", "Kangen", "Move on"]
MIME = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg", ".m4a": "audio/mp4"}


@st.cache_data(ttl=60)
def load_songs():
    """Baca katalog dari songs.json di folder yang sama dengan app.py."""
    try:
        data = json.loads((BASE / "songs.json").read_text(encoding="utf-8"))
    except Exception as e:
        return [], f"songs.json tidak bisa dibaca: {e}"
    songs = []
    for i, s in enumerate(data):
        s.setdefault("id", str(i))
        s.setdefault("artist", "Tanpa nama")
        s.setdefault("genre", "Koplo")
        s.setdefault("mood", "Galau")
        s.setdefault("downloadable", False)
        songs.append(s)
    return songs, None


def path_of(rel):
    """Ubah path relatif di songs.json menjadi path aman di dalam folder aplikasi."""
    if not rel:
        return None
    p = (BASE / rel).resolve()
    return p if p.is_file() and BASE in p.parents else None


@st.cache_data(max_entries=30, show_spinner=False)
def read_bytes(path):
    return Path(path).read_bytes()


def card(s, where):
    full = path_of(s.get("file"))
    # Cuplikan: pakai berkas "preview" jika ada. Berkas penuh hanya dipakai
    # sebagai cuplikan kalau lagunya boleh diunduh.
    play = path_of(s.get("preview")) or (full if s["downloadable"] else None)
    with st.container(border=True):
        st.caption(f'{s["genre"]} · {s["mood"]}')
        st.subheader(s["title"])
        st.write(s["artist"])
        if play:
            st.audio(str(play), format=MIME.get(play.suffix.lower(), "audio/mpeg"))
        else:
            st.caption("Cuplikan belum tersedia")
        if s["downloadable"] and full:
            st.download_button(
                "Unduh gratis",
                data=read_bytes(str(full)),
                file_name=f'{s["artist"]} - {s["title"]}{full.suffix}',
                mime=MIME.get(full.suffix.lower(), "application/octet-stream"),
                key=f'dl-{where}-{s["id"]}',
            )
        else:
            st.caption("Unduhan belum tersedia untuk lagu ini")


songs, err = load_songs()

st.title("Ambyar")
st.write("Bingung milih lagu? Pilih suasana hatimu, putar cuplikannya, lalu unduh gratis.")
if err:
    st.error(err)

m1, m2 = st.columns(2)
m1.metric("Total lagu", len(songs))
m2.metric("Total artis", len({s["artist"] for s in songs}))

with st.sidebar:
    st.header("Filter")
    q = st.text_input("Cari judul atau penyanyi").strip().lower()
    artists = st.multiselect("Artis", sorted({s["artist"] for s in songs}))
    genres = st.multiselect("Genre", GENRES)
    moods = st.multiselect("Suasana", MOODS)

filtered = [
    s
    for s in songs
    if (not q or q in f'{s["title"]} {s["artist"]}'.lower())
    and (not artists or s["artist"] in artists)
    and (not genres or s["genre"] in genres)
    and (not moods or s["mood"] in moods)
]

if st.button("Pilihkan lagu untukku", type="primary"):
    if filtered:
        st.session_state["pick"] = random.choice(filtered)["id"]
    else:
        st.session_state["pick"] = None
        st.warning("Belum ada lagu yang cocok dengan filter ini.")

picked = next((s for s in songs if s["id"] == st.session_state.get("pick")), None)
if picked:
    st.markdown("### Untukmu hari ini")
    card(picked, "pick")

st.markdown("### Semua lagu")
if not filtered:
    st.info("Tidak ada lagu yang cocok. Coba kata kunci lain atau kosongkan filter.")
else:
    cols = st.columns(3)
    for i, s in enumerate(filtered):
        with cols[i % 3]:
            card(s, "grid")
