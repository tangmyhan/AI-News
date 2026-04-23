from shared.celery_app import celery_app
from processing.nlp_service import NLPProcessor
from shared.logger import get_logger
from dotenv import load_dotenv

# Load env in worker environment
load_dotenv()

logger = get_logger("CeleryWorker")

# Initialize NLP service
nlp_processor = None

@celery_app.task(name="processing.worker.process_article", bind=True, max_retries=3)
def process_article(self, article_data: dict):
    """
    Task nhận bài viết thô từ queue, xử lý qua NLP, và lưu vào database.
    """
    global nlp_processor
    if nlp_processor is None:
        logger.info("Initializing NLP Processor in Worker...")
        nlp_processor = NLPProcessor()
        
    title = article_data.get('title', '')
    url = article_data.get('url', '')
    
    logger.info(f"Worker received article: {title}")
    
    try:
        result = nlp_processor.process(article_data)
        
        # TODO: LƯU DB POSTGRES Ở ĐÂY
        
        relevance = result.get("relevance", {})
        if relevance.get("is_relevant"):
            analysis = result.get("analysis", {}) or {}
            logger.info(f"Successfully processed relevant article. Impact: {analysis.get('impact_label')}")
        else:
            logger.info(f"Article is not relevant. Score: {relevance.get('relevance_score')}")
        
        return {
            "status": "success",
            "url": url,
            "result": result
        }
    except Exception as exc:
        logger.error(f"Error processing article {url}: {exc}")
        raise self.retry(exc=exc, countdown=10)
