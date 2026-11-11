# -*- coding: utf-8 -*-
"""
Streamlit host untuk app.py.
Streamlit TIDAK mengubah app.py / dashboard_server.py / index.html.
Streamlit hanya menjalankan app.main() di background thread,
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
APP_PY = os.path.join(APP_DIR, "app.py")

st.set_page_config(
    page_title="ANTS GLORY",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
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


if "_boot_log" not in st.session_state:
    st.session_state["_boot_log"] = []


def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    st.session_state["_boot_log"].append(f"[{ts}] {msg}")


@st.cache_resource
def boot_app_py():
    """Jalankan app.main() (yang juga start dashboard_server di :7777) di thread."""
    if bot_up():
        return {"stage": "already-running", "err": None}

    os.chdir(APP_DIR)
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)

    err_box = {"stage": "thread-not-started", "err": None}

    def _run():
        try:
            err_box["stage"] = "importing app"
            import app as bot_app
            err_box["stage"] = "creating event loop"
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            err_box["stage"] = "calling app.main()"
            loop.run_until_complete(bot_app.main())
            err_box["stage"] = "app.main() returned"
        except SystemExit as e:
            err_box["stage"] = "SystemExit"
            err_box["err"] = f"SystemExit({e})"
        except BaseException:
            err_box["stage"] = "exception"
            err_box["err"] = traceback.format_exc()

    threading.Thread(target=_run, daemon=True, name="app-main").start()
    err_box["stage"] = "thread-started"
    return err_box


# ─── boot ──────────────────────────────────────────────
if not st.session_state["_boot_log"]:
    log(f"bot_up sebelum boot: {bot_up()}")

boot = boot_app_py()
log(f"boot stage: {boot.get('stage')}")

if not bot_up():
    log("menunggu port 7777 siap (max 30s)…")
    with st.spinner("Menunggu app.py start (dashboard di :7777)…"):
        ready = False
        for _ in range(60):
            time.sleep(0.5)
            if bot_up():
                ready = True
                break
        if ready:
            log("port 7777 siap")
        else:
            log("TIMEOUT: port 7777 tidak pernah siap")


# ─── sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ ANTS GLORY")
    st.markdown(f"**Status:** {'🟢 ONLINE' if bot_up() else '🔴 OFFLINE'}")
    st.caption(f"web: {BOT_WEB}")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    st.divider()
    st.markdown("**Boot log:**")
    for line in st.session_state["_boot_log"]:
        st.text(line)

    if isinstance(boot, dict):
        st.markdown(f"**Stage:** `{boot.get('stage')}`")
        if boot.get("err"):
            st.error("app.main() error:")
            st.code(boot["err"], language="text")


# ─── konten ────────────────────────────────────────────
if bot_up():
    st.components.v1.iframe(src=BOT_WEB, height=1000, scrolling=True)
else:
    st.error("app.py belum siap. Cek **Boot log** & **Stage** di sidebar.")