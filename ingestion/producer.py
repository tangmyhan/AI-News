import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.tuoitre_spider import TuoiTreSpider
from ingestion.vnexpress_spider import VNExpressSpider
from ingestion.filter import DeduplicationFilter
from processing.worker import process_article
from shared.celery_app import celery_app
from shared.logger import get_logger

logger = get_logger("Producer")

def crawl_with_spider(spider, dedup_filter, spider_name):
    logger.info(f"[{spider_name}] Crawl danh sách URLs từ RSS...")
    latest_articles = spider.get_latest_news_entries()
    
    if not latest_articles:
        logger.warning(f"[{spider_name}] Không tìm thấy URLs nào từ RSS.")
        return
        
    logger.info(f"[{spider_name}] Tìm thấy {len(latest_articles)} URLs từ RSS.")
    
    # Lọc bài cũ qua Redis
    new_articles = dedup_filter.filter_new_articles(latest_articles)
    logger.info(f"[{spider_name}] Sau khi lọc trùng: Còn {len(new_articles)} URLs mới cần crawl chi tiết.")
    
    # crawl content thô cho từng URL mới
    for idx, article_info in enumerate(new_articles):
        url = article_info['url']
        logger.info(f"[{spider_name}] [{idx+1}/{len(new_articles)}] Đang crawl raw HTML: {url}")
        
        crawled_data = spider.crawl_article(article_info)
        
        if crawled_data and crawled_data.get('content'):
            logger.info(f"[{spider_name}] Crawl dữ liệu thành công. Đang đẩy vào Celery Queue...")
            # đẩy dữ liệu thô vào Queue
            process_article.delay(crawled_data)
        else:
            logger.warning(f"[{spider_name}] Không lấy được nội dung hoặc bài bị loại bởi danh mục cho URL: {url}")

@celery_app.task(name="ingestion.run_crawler")
def run_ingestion():
    logger.info("Khởi tạo Spiders và Filter...")
    dedup_filter = DeduplicationFilter()
    
    # Crawl Tuổi Trẻ
    tuoitre_spider = TuoiTreSpider()
    crawl_with_spider(tuoitre_spider, dedup_filter, "TuoiTre")
    
    # Crawl VnExpress
    vnexpress_spider = VNExpressSpider()
    crawl_with_spider(vnexpress_spider, dedup_filter, "VnExpress")
    
    logger.info("Hoàn tất quá trình lấy tin cho tất cả các báo.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_ingestion()
