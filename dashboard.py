import streamlit as st
import sqlite3
import pandas as pd
import os
import time

from src.discovery import DiscoveryEngine
from src.filtering import InsightFilter
from src.generator import ContentGenerator
from src.quality_control import QualityControl
from src.db import create_run, update_run_stats, log_article, log_post
from src.config import Config

DB_PATH = os.path.join(os.path.dirname(__file__), "dashboard.db")

st.set_page_config(page_title="AI Content Studio", layout="wide", page_icon="✨")

# Premium CSS Styling
st.markdown("""
<style>
    .main-header { font-size: 38px !important; font-weight: 800; color: #1E88E5; margin-bottom: 0px; }
    .sub-header { font-size: 17px !important; color: #888888; margin-bottom: 30px; }
    .linkedin-card { 
        background-color: #1e1e1e; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #333333; 
        color: #ffffff; 
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto; 
        box-shadow: 2px 2px 15px rgba(0,0,0,0.4);
    }
    .linkedin-text { white-space: pre-wrap; font-size: 15px; line-height: 1.6; margin-top: 15px;}
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #1E88E5 !important;}
    .stProgress .st-bo { background-color: #1E88E5; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">✨ AI Content Studio</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your autonomous agent for scraping, vetting, and generating viral finance updates.</p>', unsafe_allow_html=True)

# Initialize session state
if 'pipeline_stage' not in st.session_state:
    st.session_state.pipeline_stage = 'IDLE'
if 'run_id' not in st.session_state:
    st.session_state.run_id = None
if 'scored_articles' not in st.session_state:
    st.session_state.scored_articles = []
if 'raw_count' not in st.session_state:
    st.session_state.raw_count = 0
if 'novel_count' not in st.session_state:
    st.session_state.novel_count = 0
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'final_post' not in st.session_state:
    st.session_state.final_post = None

def reset_pipeline():
    st.session_state.pipeline_stage = 'IDLE'
    st.session_state.run_id = None
    st.session_state.scored_articles = []
    st.session_state.selected_article = None
    st.session_state.final_post = None

col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown("### 🎛️ Control Center")
    with st.container(border=True):
        if st.session_state.pipeline_stage == 'IDLE':
            st.write("Ready to scour the markets.")
            if st.button("🚀 IGNITE PIPELINE", type="primary", use_container_width=True):
                st.session_state.pipeline_stage = 'DISCOVERY'
                st.session_state.run_id = create_run()
                st.rerun()
        else:
            st.write("Agent is currently deployed.")
            if st.button("🛑 STOP & RESET", use_container_width=True):
                reset_pipeline()
                st.rerun()

with col2:
    if st.session_state.pipeline_stage == 'IDLE':
        st.info("System is standing by. Click 'IGNITE PIPELINE' to begin the autonomous sequence.")
        
    elif st.session_state.pipeline_stage == 'DISCOVERY':
        with st.status("🔍 **Phase 1:** Global Discovery Engine Active...", expanded=True) as status:
            discovery = DiscoveryEngine()
            st.write("📡 Scanning RSS Feeds (Moneycontrol, Mint, ET)...")
            raw_articles = discovery.fetch_rss_feeds()
            st.session_state.raw_count = len(raw_articles)
            
            st.write("🧠 Querying ChromaDB Vector Engine to prevent duplication...")
            novel_articles = discovery.filter_duplicates(raw_articles)
            st.session_state.novel_count = len(novel_articles)
            
            st.write(f"🟢 Found **{len(novel_articles)}** novel articles out of {len(raw_articles)} total.")
            status.update(label="Discovery Phase Complete!", state="complete", expanded=False)
            
        if len(novel_articles) == 0:
            st.warning("No fresh market news found today. System halting to conserve API quota.")
            update_run_stats(st.session_state.run_id, st.session_state.raw_count, 0, 0, "COMPLETED_NO_NEW")
            st.session_state.pipeline_stage = 'DONE'
            time.sleep(1)
            st.rerun()
        else:
            # Move to filtering
            st.session_state.pipeline_stage = 'FILTERING'
            st.session_state.novel_articles = novel_articles
            time.sleep(1)
            st.rerun()

    elif st.session_state.pipeline_stage == 'FILTERING':
        with st.status("⚖️ **Phase 2:** AI Insight Vetting...", expanded=True) as status:
            filtering = InsightFilter()
            
            st.write(f"⚡ Batch evaluating {len(st.session_state.novel_articles)} articles in a **single API call**...")
            
            scored = filtering.score_articles_batch(st.session_state.novel_articles)
            
            for res in scored:
                db_status = 'HIGH_SIGNAL' if res['score'] >= Config.MINIMUM_SIGNAL_SCORE else 'REJECTED_NOISE'
                log_article(st.session_state.run_id, res['article']['title'], res['article']['link'], res['score'], res['reasoning'], db_status)
            
            scored.sort(key=lambda x: x['score'], reverse=True)
            st.session_state.scored_articles = scored
            status.update(label="AI Vetting Complete!", state="complete", expanded=False)
            
        high_signal = [x for x in scored if x['score'] >= Config.MINIMUM_SIGNAL_SCORE]
        update_run_stats(st.session_state.run_id, st.session_state.raw_count, st.session_state.novel_count, len(high_signal), "IN_PROGRESS")
        
        if len(high_signal) > 0:
            st.success(f"🏆 Found {len(high_signal)} 'Gold-Tier' articles (Score: {Config.MINIMUM_SIGNAL_SCORE}+)!")
            st.session_state.selected_article = high_signal[0]
            st.session_state.pipeline_stage = 'GENERATION'
            time.sleep(2)
            st.rerun()
        else:
            st.warning(f"All {len(scored)} articles failed the strict CA/GenZ Quality Bar. (See override options below).")
            st.session_state.pipeline_stage = 'MANUAL_INTERVENTION'
            time.sleep(1)
            st.rerun()

    elif st.session_state.pipeline_stage == 'MANUAL_INTERVENTION':
        st.error("🚨 **Human Intervention Required**: The AI determined no articles were interesting enough today.")
        st.write("Browse the rejected articles below and manually override the AI's decision if you find one worthy.")
        
        for idx, res in enumerate(st.session_state.scored_articles):
            with st.expander(f"📊 Score {res['score']}/30 — {res['article']['title'][:65]}..."):
                st.write(f"**AI Reasoning:** {res['reasoning']}")
                st.write(f"**Excerpt:** {res['article']['summary']}")
                if st.button("Force Generate Post from this Article", key=f"force_{idx}"):
                    st.session_state.selected_article = res
                    st.session_state.pipeline_stage = 'GENERATION'
                    st.rerun()

    elif st.session_state.pipeline_stage == 'GENERATION':
        art = st.session_state.selected_article
        st.info(f"**Target Topic**: {art['article']['title']} (AI Score: {art['score']}/30)")
        
        with st.status("🖨️ **Phase 3:** Content Generation & Dispatch...", expanded=True) as status:
            st.write("Drafting viral 80/20 Hinglish Post...")
            generator = ContentGenerator()
            draft_post = generator.generate_post(art)
            
            if not draft_post:
                st.write("❌ Generation Failed (API Limit/Error).")
                update_run_stats(st.session_state.run_id, st.session_state.raw_count, st.session_state.novel_count, 0, "FAILED_GENERATION")
            else:
                st.write("Initiating strict Quality Control Node...")
                qc = QualityControl()
                passed_qc = qc.ai_review(draft_post)
                
                log_post(st.session_state.run_id, art['article']['title'], draft_post, passed_qc)
                
                if passed_qc:
                    st.write("✅ QC Passed! Firing Telegram and Email Webhooks...")
                    qc.request_human_approval(draft_post, art['article']['title'])
                    update_run_stats(st.session_state.run_id, st.session_state.raw_count, st.session_state.novel_count, 1, "SUCCESS")
                else:
                    st.write("❌ QC Rejected. Stored locally but not sent to devices.")
                    update_run_stats(st.session_state.run_id, st.session_state.raw_count, st.session_state.novel_count, 0, "FAILED_QC")
                    
                st.session_state.final_post = draft_post
                
            st.session_state.pipeline_stage = 'DONE'
            status.update(label="Pipeline Fully Executed!", state="complete", expanded=False)
            st.rerun()

    elif st.session_state.pipeline_stage == 'DONE':
        if st.session_state.final_post:
            st.balloons()
            st.success("🎉 **Success!** Your post has been delivered to your devices.")
            
            st.markdown("### 📱 LinkedIn Preview")
            st.markdown(f'''
            <div class="linkedin-card">
                <b>👤 AI Finance Agent (You)</b> &bull; <i>Just now</i>
                <div class="linkedin-text">{st.session_state.final_post}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown("<br/>### 📋 Copy Draft", unsafe_allow_html=True)
            st.write("Click the **Copy Icon** in the top right corner of the box below to paste it straight to LinkedIn!")
            st.code(st.session_state.final_post, language="markdown")
            
        else:
            st.error("Pipeline finished but generation encountered an error. Click Reset to try again.")

st.divider()

if st.session_state.pipeline_stage in ['IDLE', 'DONE'] or st.session_state.pipeline_stage == 'MANUAL_INTERVENTION':
    st.subheader("🗄️ System Archives (Last 5 Runs)")
    try:
        conn = sqlite3.connect(DB_PATH)
        runs_df = pd.read_sql_query("SELECT id as 'ID', timestamp as 'Date', status as 'Status', total_fetched as 'RSS Scraped', novel_found as 'Unique', high_signal_found as 'High Signal' FROM runs ORDER BY id DESC LIMIT 5", conn)
        conn.close()
        st.dataframe(runs_df, hide_index=True, use_container_width=True)
    except:
        pass
