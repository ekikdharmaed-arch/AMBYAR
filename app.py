import random

import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Ambyar", page_icon="🎵", layout="wide")

GENRES = ["Koplo", "Dangdut", "Pop Jawa"]
MOODS = ["Patah hati", "Galau", "Nyesek", "Kangen", "Move on"]
# ===== ISI 4 BARIS INI SAJA (tidak perlu secrets.toml) =====
# Aman ditaruh di kode publik: anon key dibatasi oleh RLS di Supabase.
# JANGAN pernah menaruh service_role key di sini.
SUPABASE_URL = "https://PROJECT-ID.supabase.co"
SUPABASE_ANON_KEY = "ISI_DENGAN_ANON_KEY"
PREVIEW_BASE_URL = ""   # bucket R2 publik (folder preview/), boleh kosong dulu
DOWNLOAD_BASE_URL = ""  # Cloudflare Worker /download, boleh kosong dulu
# ============================================================


def cfg(name, default):
    """Pakai nilai di atas; kalau Secrets Streamlit diisi, itu yang menang."""
    try:
        return st.secrets[name]
    except Exception:
        return default


SUPABASE_URL = cfg("SUPABASE_URL", SUPABASE_URL)
SUPABASE_ANON_KEY = cfg("SUPABASE_ANON_KEY", SUPABASE_ANON_KEY)
PREVIEW = cfg("PREVIEW_BASE_URL", PREVIEW_BASE_URL).rstrip("/")
DOWNLOAD = cfg("DOWNLOAD_BASE_URL", DOWNLOAD_BASE_URL).rstrip("/")

if "PROJECT-ID" in SUPABASE_URL or "ISI_DENGAN" in SUPABASE_ANON_KEY:
    st.error("Isi SUPABASE_URL dan SUPABASE_ANON_KEY di bagian atas app.py.")
    st.stop()


@st.cache_resource
def db():
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


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
        if PREVIEW and s.get("preview_key"):
            st.audio(f'{PREVIEW}/{s["preview_key"]}')
        else:
            st.caption("Cuplikan belum tersedia")
        if s["downloadable"] and DOWNLOAD:
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
