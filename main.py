import schedule
import time
from src.discovery import DiscoveryEngine
from src.filtering import InsightFilter
from src.generator import ContentGenerator
from src.quality_control import QualityControl
from src.db import create_run, update_run_stats, log_article, log_post
from src.config import Config

def run_pipeline():
    print("--- Starting Automated Content Generation Pipeline ---")
    run_id = create_run()
    
    discovery = DiscoveryEngine()
    raw_articles = discovery.fetch_rss_feeds()
    novel_articles = discovery.filter_duplicates(raw_articles)
    
    if not novel_articles:
        print("No novel articles found. Exiting pipeline.")
        update_run_stats(run_id, len(raw_articles), 0, 0, "COMPLETED_NO_NOVEL")
        return
        
    print(f"Scoring {len(novel_articles)} novel articles in BULK...")
    filtering = InsightFilter()
    
    scored = filtering.score_articles_batch(novel_articles)
    high_signal_articles = []
    
    for res in scored:
        status = 'HIGH_SIGNAL' if res['score'] >= 24 else 'REJECTED_NOISE'
        log_article(run_id, res['article']['title'], res['article']['link'], res['score'], res['reasoning'], status)
        if status == 'HIGH_SIGNAL':
            high_signal_articles.append(res)
            
    high_signal_articles.sort(key=lambda x: x['score'], reverse=True)
    update_run_stats(run_id, len(raw_articles), len(novel_articles), len(high_signal_articles), "IN_PROGRESS")
    
    if not high_signal_articles:
        print("No articles met the criteria. Exiting pipeline.")
        update_run_stats(run_id, len(raw_articles), len(novel_articles), 0, "COMPLETED_NO_HIGH_SIGNAL")
        return
        
    print(f"Found {len(high_signal_articles)} high-signal articles. Gen for top 1.")
    top = high_signal_articles[0]
    
    print("Generating post draft...")
    generator = ContentGenerator()
    draft = generator.generate_post(top)
    
    if not draft:
        update_run_stats(run_id, len(raw_articles), len(novel_articles), len(high_signal_articles), "FAILED_GENERATION")
        return
        
    qc = QualityControl()
    passed_qc = qc.ai_review(draft)
    log_post(run_id, top['article']['title'], draft, passed_qc)
    
    if passed_qc:
        print("Passed QA. Triggering notifications...")
        qc.request_human_approval(draft, top['article']['title'])
        print(draft)
        update_run_stats(run_id, len(raw_articles), len(novel_articles), len(high_signal_articles), "SUCCESS_SENT_APPROVAL")
    else:
        update_run_stats(run_id, len(raw_articles), len(novel_articles), len(high_signal_articles), "FAILED_QC_REJECTED")

if __name__ == "__main__":
    print("Agent Scheduler Activated: Running the pipeline once every 3 days...")
    
    # Run once immediately on startup
    run_pipeline()
    
    # Schedule every 3 days
    schedule.every(3).days.do(run_pipeline)
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour
