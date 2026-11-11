# -*- coding: utf-8 -*-
"""
Streamlit host untuk app.py.
Streamlit TIDAK mengubah app.py / dashboard_server.py / index.html.
Streamlit hanya menjalankan app.py di background thread,
lalu menampilkan web dashboard (index.html) via iframe.

Jalankan:
    streamlit run streamlit_app.py
"""
import os
import sys
import threading
import time

import requests
import streamlit as st

BOT_WEB = "http://localhost:7777"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PY  = os.path.join(APP_DIR, "app.py")

st.set_page_config(
    page_title="ANTS GLORY",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
#MainMenu, header, footer {visibility:hidden;}
.block-container{padding:0!important;max-width:none!important;}
iframe{border:0;}
</style>
""", unsafe_allow_html=True)


def bot_up() -> bool:
    try:
        return requests.get(f"{BOT_WEB}/api/stats", timeout=2).status_code == 200
    except Exception:
        return False


@st.cache_resource
def boot_app_py():
    """Jalankan app.py di thread background (sekali). app.py sendiri yang
    menyalakan dashboard_server (index.html) di port 7777."""
    if bot_up():
        return "already"

    # pastikan cwd = folder app.py, biar relative path (accounts.json, dll) valid
    os.chdir(APP_DIR)
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)

    def _run():
        try:
            # import app.py apa adanya → menjalankan seluruh isi modul
            import app  # noqa: F401
        except SystemExit:
            pass
        except Exception as e:
            print(f"[streamlit host] app.py error: {e}")

    threading.Thread(target=_run, daemon=True, name="app-py").start()
    return "spawned"


# ─── boot app.py ────────────────────────────────────────
boot_app_py()

# tunggu dashboard_server siap (max ~20 detik)
if not bot_up():
    with st.spinner("Menunggu app.py start…"):
        for _ in range(40):
            time.sleep(0.5)
            if bot_up():
                break


# ─── sidebar ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ ANTS GLORY")
    st.markdown(f"**Status:** {'🟢 ONLINE' if bot_up() else '🔴 OFFLINE'}")
    st.caption(f"web: {BOT_WEB}")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()


# ─── konten: iframe ke index.html ──────────────────────
if bot_up():
    st.components.v1.iframe(src=BOT_WEB, height=1000, scrolling=True)
else:
    st.error("app.py belum siap. Cek konsol / terminal.")