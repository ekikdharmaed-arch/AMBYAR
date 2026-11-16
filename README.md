import random

import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Ambyar", page_icon="🎵", layout="wide")

GENRES = ["Koplo", "Dangdut", "Pop Jawa"]
MOODS = ["Patah hati", "Galau", "Nyesek", "Kangen", "Move on"]
PREVIEW = st.secrets["PREVIEW_BASE_URL"].rstrip("/")    # bucket R2 publik (folder preview/)
DOWNLOAD = st.secrets["DOWNLOAD_BASE_URL"].rstrip("/")  # Cloudflare Worker /download/:id


@st.cache_resource
def db():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


@st.cache_data(ttl=60)
def load_songs():
    res = (
        db()
        .table("songs")
        .select("id,title,genre,mood,preview_key,downloadable,download_count,artists(name)")
        .eq("is_published", True)
        .order("created_at", desc=True)
        .execute()
    )
    songs = []
    for s in res.data:
        s["artist"] = (s.get("artists") or {}).get("name", "Tanpa nama")
        songs.append(s)
    return songs


def card(s):
    with st.container(border=True):
        st.caption(f'{s["genre"]} · {s["mood"]}')
        st.subheader(s["title"])
        st.write(s["artist"])
        if s.get("preview_key"):
            st.audio(f'{PREVIEW}/{s["preview_key"]}')
        else:
            st.caption("Cuplikan belum tersedia")
        if s["downloadable"]:
            st.link_button("Unduh gratis", f'{DOWNLOAD}/{s["id"]}')
        else:
            st.caption("Unduhan belum tersedia untuk lagu ini")


songs = load_songs()

st.title("Ambyar")
st.write("Bingung milih lagu? Pilih suasana hatimu, putar cuplikannya, lalu unduh gratis.")

m1, m2 = st.columns(2)
m1.metric("Total lagu", len(songs))
m2.metric("Total unduhan", sum(s["download_count"] for s in songs))

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
    st.session_state["pick"] = random.choice(filtered)["id"] if filtered else None
    if not filtered:
        st.warning("Belum ada lagu yang cocok dengan filter ini.")

picked = next((s for s in songs if s["id"] == st.session_state.get("pick")), None)
if picked:
    st.markdown("### Untukmu hari ini")
    card(picked)

st.markdown("### Semua lagu")
if not filtered:
    st.info("Tidak ada lagu yang cocok. Coba kata kunci lain atau kosongkan filter.")
else:
    cols = st.columns(3)
    for i, s in enumerate(filtered):
        with cols[i % 3]:
            card(s)
