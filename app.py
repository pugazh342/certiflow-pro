# app.py
import os
import time
from pathlib import Path
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

import config
from modules.ingestor import process_upload
from modules.pdf_engine import render_certificate
from modules.state_manager import StateManager
from modules.mailer import ZeroCostMailer

load_dotenv()

st.set_page_config(page_title="CertiFlow Pro Cockpit", layout="wide")

if "manifest" not in st.session_state:
    st.session_state.manifest = {}
if "active_step" not in st.session_state:
    st.session_state.active_step = 1
if "kill_switch" not in st.session_state:
    st.session_state.kill_switch = False

state_mgr = StateManager()

st.title("🛡️ CertiFlow Pro: HITL Dispatch Cockpit")
st.markdown("---")

# Global Checkpoint Inspection on boot
existing_manifest = state_mgr.load_manifest()
if existing_manifest and st.session_state.active_step == 1:
    resumable = state_mgr.get_resumable_records(existing_manifest)
    if len(resumable) > 0:
        st.warning(f"⚠️ Unfinished Job Detected! {len(resumable)} records remain pending/failed from a prior session.")
        col1, col2 = st.columns(2)
        if col1.button("🔄 Resume Existing Job"):
            st.session_state.manifest = existing_manifest
            st.session_state.active_step = 2
            st.rerun()
        if col2.button("🗑️ Discard & Start Fresh"):
            if config.CHECKPOINT_FILE.exists():
                config.CHECKPOINT_FILE.unlink()
            st.session_state.manifest = {}
            st.rerun()

# --- STEP 1: INGESTION ---
if st.session_state.active_step == 1:
    st.header("Step 1: Data Ingest & Sanitization")
    uploaded_file = st.file_uploader("Upload Target Recipients (.csv)", type=["csv"])
    
    if uploaded_file:
        valid_df, invalid_df, status_msg = process_upload(uploaded_file)
        if status_msg != "Success":
            st.error(status_msg)
        else:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader("✅ Validated Records")
                st.dataframe(valid_df, use_container_width=True)
            with c2:
                st.subheader("⚠️ Quarantine")
                if not invalid_df.empty:
                    st.error(f"{len(invalid_df)} records dropped.")
                    st.dataframe(invalid_df)
                else:
                    st.success("Zero syntax errors.")

            if not valid_df.empty:
                if st.button("Lock Manifest & Proceed to Renderer ➡️", type="primary"):
                    st.session_state.manifest = state_mgr.initialize_job(valid_df)
                    st.session_state.active_step = 2
                    st.rerun()

# --- STEP 2: GENERATION ---
elif st.session_state.active_step == 2:
    st.header("Step 2: PDF Rendering Factory")
    
    pending_count = sum(1 for m in st.session_state.manifest.values() if m["status"] == "PENDING")
    st.write(f"Total Queue Size: **{len(st.session_state.manifest)}** | Pending Render: **{pending_count}**")
    
    if st.button("🔨 Execute Local PDF Batch Render"):
        progress_bar = st.progress(0)
        manifest = st.session_state.manifest
        keys = list(manifest.keys())
        
        for i, rec_id in enumerate(keys):
            item = manifest[rec_id]
            if item["status"] == "PENDING":
                success, path_or_err = render_certificate(item["record"])
                if success:
                    state_mgr.update_record(manifest, rec_id, "GENERATED", pdf_path=path_or_err)
                else:
                    state_mgr.update_record(manifest, rec_id, "FAILED", error=path_or_err)
            progress_bar.progress((i + 1) / len(keys))
            
        st.session_state.manifest = state_mgr.load_manifest()
        st.success("Batch Rendering Operation Complete.")
        st.rerun()
    

    # Artifact Verifier
    generated_docs = [m for m in st.session_state.manifest.values() if m["status"] in ["GENERATED", "SENT"]]
    if generated_docs:
        st.subheader("🔍 Visual Verification Sandbox")
        sample = st.selectbox("Select rendered artifact to inspect:", generated_docs, format_func=lambda x: x["record"]["Name"])
        
        if sample and Path(sample["pdf_path"]).exists():
            with open(sample["pdf_path"], "rb") as f:
                st.download_button("📥 Download PDF Artifact", f, file_name=Path(sample["pdf_path"]).name)
            
        if st.button("Approve Artifacts & Open Dispatch Gate ➡️", type="primary"):
            st.session_state.active_step = 3
            st.rerun()

# --- STEP 3: DISPATCH GATE ---
elif st.session_state.active_step == 3:
    st.header("Step 3: The Confirmation Gate")
    
    with st.expander("🔐 SMTP Environment Credentials Check", expanded=True):
        host = st.text_input("SMTP Host", value=os.getenv("SMTP_HOST", config.DEFAULT_SMTP_HOST))
        port = st.text_input("SMTP Port", value=os.getenv("SMTP_PORT", str(config.DEFAULT_SMTP_PORT)))
        user = st.text_input("Sender User/Email", value=os.getenv("SMTP_USER", ""))
        password = st.text_input("App Password", type="password", value=os.getenv("SMTP_PASS", ""))

    mailer = ZeroCostMailer(host, port, user, password)

    st.subheader("🧪 Stage 3A: Dry Run")
    test_email = st.text_input("Enter your personal email for a live verification packet:")
    if st.button("Send Dry-Run Sample"):
        first_gen = next((m for m in st.session_state.manifest.values() if m["status"] in ["GENERATED", "SENT"]), None)
        if not first_gen:
            st.error("No generated PDFs found to test.")
        else:
            ok, err = mailer.send_certificate(test_email, "DRY RUN TESTER", first_gen["pdf_path"], is_dry_run=True)
            if ok:
                st.success(f"Dry run delivered successfully to {test_email}")
            else:
                st.error(f"Dry run failed: {err}")

    st.markdown("---")
    st.subheader("🚀 Stage 3B: Live Execution")
    
    c_red, c_green = st.columns(2)
    with c_red:
        if st.button("🚨 ABORT / KILL DISPATCHER", type="primary", use_container_width=True):
            st.session_state.kill_switch = True
            st.error("SYSTEM HALTED BY USER.")
            
    with c_green:
        if st.button("APPROVE & DISPATCH ALL VALID CERTIFICATES", use_container_width=True):
            st.session_state.kill_switch = False
            st.session_state.active_step = 4
            st.rerun()

# --- STEP 4: TELEMETRY & POST-FLIGHT ---
elif st.session_state.active_step == 4:
    st.header("Step 4: Live Telemetry & Dispatch")
    
    host = os.getenv("SMTP_HOST", config.DEFAULT_SMTP_HOST)
    port = os.getenv("SMTP_PORT", str(config.DEFAULT_SMTP_PORT))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    mailer = ZeroCostMailer(host, port, user, password)

    terminal = st.empty()
    logs = []
    
    manifest = st.session_state.manifest
    targets = [rec_id for rec_id, data in manifest.items() if data["status"] == "GENERATED"]
    
    progress = st.progress(0)
    
    for idx, rec_id in enumerate(targets):
        if st.session_state.kill_switch:
            logs.append("⚠️ [KILL SWITCH ACTIVATED] - Halting outbound queue.")
            break
            
        item = manifest[rec_id]
        rec = item["record"]
        
        logs.append(f"[{time.strftime('%H:%M:%S')}] Connecting to SMTP -> Handing off PDF for {rec['Name']} ({rec['Email']})...")
        terminal.code("\n".join(logs[-15:]))
        
        ok, result_str = mailer.send_certificate(rec["Email"], rec["Name"], item["pdf_path"])
        
        if ok:
            state_mgr.update_record(manifest, rec_id, "SENT")
            logs.append(f"[{time.strftime('%H:%M:%S')}] 🟢 OK -> Delivery acknowledged.")
        else:
            state_mgr.update_record(manifest, rec_id, "FAILED", error=result_str)
            logs.append(f"[{time.strftime('%H:%M:%S')}] 🔴 ERR -> {result_str}")
            
        terminal.code("\n".join(logs[-15:]))
        progress.progress((idx + 1) / len(targets))

    st.markdown("---")
    st.subheader("📊 Post-Flight Settlement")
    audit_file_path = state_mgr.export_audit_log(st.session_state.manifest)
    
    with open(audit_file_path, "rb") as f:
        st.download_button("📥 Download Official Audit Report (.csv)", f, file_name=Path(audit_file_path).name, type="primary")
        
    if st.button("Reset Cockpit for New Run"):
        st.session_state.manifest = {}
        st.session_state.active_step = 1
        st.rerun()