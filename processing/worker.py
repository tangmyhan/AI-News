from shared.celery_app import celery_app
from processing.nlp_service import NLPProcessor
from shared.logger import get_logger
from dotenv import load_dotenv
import time
import json

load_dotenv()

logger = get_logger("CeleryWorker")

# Initialize NLP service
nlp_processor = None

@celery_app.task(name="processing.worker.process_article", bind=True, max_retries=3)
def process_article(self, article_data: dict):
    """
    Task nhận bài viết thô từ queue, xử lý qua NLP, và lưu vào database.
    """
    worker_start_time = time.time()
    pipeline_start_time = article_data.get('pipeline_start_time', worker_start_time)

    global nlp_processor
    if nlp_processor is None:
        logger.info("Initializing NLP Processor in Worker...")
        nlp_processor = NLPProcessor()
        
    title = article_data.get('title', '')
    url = article_data.get('url', '')
    
    logger.info(f"Worker received article: {title}")
    logger.info(f"Queue Time (from crawl start): {worker_start_time - pipeline_start_time:.2f}s")
    
    try:
        nlp_start_time = time.time()
        result = nlp_processor.process(article_data)
        nlp_time = time.time() - nlp_start_time
        
        if result is None:
            logger.info(f"Article is not relevant to business. Skipped: {url}")
            return {
                "status": "skipped",
                "reason": "not_relevant",
                "url": url
            }
            
        # TODO: LƯU DB POSTGRES Ở ĐÂY
        
        relevance = result.get("relevance", {})
        analysis = result.get("analysis", {}) or {}
        
        total_time = time.time() - pipeline_start_time
        logger.info(f"Successfully processed relevant article. Impact: {analysis.get('impact_label')}")
        logger.info("--- TIME STATISTICS ---")
        logger.info(f"- AI/NLP Time: {nlp_time:.2f}s")
        logger.info(f"- TOTAL TIME (from URL to done): {total_time:.2f}s")
        logger.info("--- RESULT DATA ---")
        logger.info("\n" + json.dumps(result, ensure_ascii=False, indent=4))
        
        return {
            "status": "success",
            "url": url,
            "result": result
        }
    except Exception as exc:
        logger.error(f"Error processing article {url}: {exc}")
        raise self.retry(exc=exc, countdown=10)
