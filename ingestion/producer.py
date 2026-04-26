import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.tuoitre_spider import TuoiTreSpider
from ingestion.filter import DeduplicationFilter
from processing.worker import process_article
from shared.logger import get_logger

logger = get_logger("Producer")

def run_ingestion():
    logger.info("Khởi tạo Spider và Filter...")
    spider = TuoiTreSpider()
    dedup_filter = DeduplicationFilter()
    
    logger.info("Crawl danh sách URLs từ RSS...")
    latest_articles = spider.get_latest_news_entries()
    
    if not latest_articles:
        logger.warning("Không tìm thấy URLs nào từ RSS.")
        return
        
    logger.info(f"Tìm thấy {len(latest_articles)} URLs từ RSS.")
    
    # Lọc bài cũ qua Redis
    new_articles = dedup_filter.filter_new_articles(latest_articles)
    logger.info(f"Sau khi lọc trùng: Còn {len(new_articles)} URLs mới cần crawl chi tiết.")
    
    # crawl content thô cho từng URL mới
    for idx, article_info in enumerate(new_articles):
        url = article_info['url']
        logger.info(f"[{idx+1}/{len(new_articles)}] Đang crawl raw HTML: {url}")
        
        url_start_time = time.time()
        crawled_data = spider.crawl_article(article_info)
        
        if crawled_data and crawled_data.get('content'):
            crawl_time = time.time() - url_start_time
            logger.info(f"Crawl dữ liệu thành công mất {crawl_time:.2f}s. Đang đẩy vào Celery Queue...")
            
            crawled_data['pipeline_start_time'] = url_start_time
            
            # đẩy dữ liệu thô vào Queue
            process_article.delay(crawled_data)
        else:
            logger.warning(f"Không lấy được nội dung hoặc bài bị loại bởi danh mục cho URL: {url}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_ingestion()
