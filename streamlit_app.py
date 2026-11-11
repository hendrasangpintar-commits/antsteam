# -*- coding: utf-8 -*-
"""
Streamlit host untuk app.py.
Streamlit TIDAK mengubah app.py / dashboard_server.py / index.html.
Streamlit hanya menjalankan app.py di background thread,
lalu menampilkan web dashboard (index.html) via iframe.

Jalankan:
    streamlit run streamlit_app.py
"""
import asyncio
import os
import sys
import threading
import time
import traceback

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


# penyimpanan error lintas rerun
if "_boot_err" not in st.session_state:
    st.session_state["_boot_err"] = None


@st.cache_resource
def boot_app_py():
    """
    Jalankan app.main() (yang juga start dashboard_server di port 7777)
    di thread background dengan event loop sendiri.
    """
    if bot_up():
        return "already"

    os.chdir(APP_DIR)
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)

    err_box = {"err": None}

    def _run():
        try:
            import app as bot_app                         # import modul (tidak otomatis jalanin main())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_app.main())       # ← INI yang start dashboard + worker
        except SystemExit:
            pass
        except Exception:
            err_box["err"] = traceback.format_exc()
            print("[streamlit host] app.main() error:\n", err_box["err"])

    threading.Thread(target=_run, daemon=True, name="app-main").start()
    return err_box


boot = boot_app_py()
if isinstance(boot, dict) and boot.get("err"):
    st.session_state["_boot_err"] = boot["err"]


# tunggu dashboard siap (max 30 detik)
if not bot_up():
    with st.spinner("Menunggu app.py start (dashboard di :7777)…"):
        for _ in range(60):
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
    if st.session_state["_boot_err"]:
        with st.expander("⚠ Error app.py", expanded=True):
            st.code(st.session_state["_boot_err"], language="text")


# ─── iframe ke index.html ──────────────────────────────
if bot_up():
    st.components.v1.iframe(src=BOT_WEB, height=1000, scrolling=True)
else:
    st.error("app.py belum siap. Cek expander **⚠ Error app.py** di sidebar.")