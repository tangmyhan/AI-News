from shared.celery_app import celery_app
from processing.nlp_service import NLPProcessor
from shared.logger import get_logger
from dotenv import load_dotenv
from database.db_client import db_client
from database.models import Article
from sqlalchemy.dialects.postgresql import insert

# Load env in worker environment
load_dotenv()

logger = get_logger("CeleryWorker")

# Initialize NLP service
nlp_processor = None

# nhận bài viết thô từ queue, xử lý qua NLP, và lưu vào PostgreSQL.
@celery_app.task(name="processing.worker.process_article", bind=True, max_retries=3)
def process_article(self, article_data: dict):
    global nlp_processor
    if nlp_processor is None:
        logger.info("Initializing NLP Processor in Worker...")
        nlp_processor = NLPProcessor()
        
    title = article_data.get('title', '')
    url = article_data.get('url', '')
    
    logger.info(f"Worker received article: {title}")
    
    try:
        result = nlp_processor.process(article_data)
        
        if result is None:
            relevance = {"is_relevant": False, "relevance_score": 0.0}
            analysis = {}
        else:
            relevance = result.get("relevance", {})
            analysis = result.get("analysis", {}) or {}

        # Đóng gói payload cho DB
        insert_stmt = insert(Article).values(
            title=article_data.get('title', ''),
            url=url,
            published_date=article_data.get('published', ''),
            sapo=article_data.get('sapo', ''),
            content=article_data.get('content', ''),
            categories=article_data.get('categories', []),
            entities=article_data.get('entities', []),
            topics=article_data.get('topics', []),
            is_relevant=relevance.get('is_relevant', False),
            relevance_score=relevance.get('relevance_score'),
            summary=analysis.get('summary', []),
            impact_label=analysis.get('impact_label', ''),
            impact_score=analysis.get('impact_score'),
            impact_reason=analysis.get('impact_reason', '')
        )

        # Xử lý trùng lặp Database (Upsert)
        update_dict = {
            c.name: c for c in insert_stmt.excluded if not c.primary_key
        }
        
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=['url'],
            set_=update_dict
        )

        # lưu trữ
        db_session = db_client.get_session()
        try:
            db_session.execute(upsert_stmt)
            db_session.commit()
            
            if relevance.get("is_relevant"):
                logger.info(f"Successfully processed and saved relevant article. Impact: {analysis.get('impact_label')}")
            else:
                logger.info(f"Article saved. Not relevant. Score: {relevance.get('relevance_score')}")
        except Exception as db_err:
            db_session.rollback()
            logger.error(f"Database error saving article {url}: {db_err}")
            raise
        finally:
            db_session.close()
            
        return {
            "status": "success",
            "url": url,
            "result": result
        }
    except Exception as exc:
        logger.error(f"Error processing article {url}: {exc}")
        raise self.retry(exc=exc, countdown=10)
