import json
from ingestion.tuoitre_spider import TuoiTreSpider
from processing.nlp_service import NLPProcessor
from shared.logger import get_logger

logger = get_logger("Pipeline")

def run():
    logger.info("Initializing spider and NLP Processor...")
    spider = TuoiTreSpider()
    nlp = NLPProcessor()
    
    logger.info("Fetching latest URLs from Tuoi Tre RSS...")
    articles = spider.get_latest_news_entries()
    
    if not articles:
        logger.warning("No articles found in RSS.")
        return
        
    crawled_data = None
    for article_meta in articles:
        logger.info(f"Crawling article: {article_meta['url']}")
        crawled_data = spider.crawl_article(article_meta)
        if crawled_data:
            break
            
    if not crawled_data:
        logger.warning("Failed to extract content or all articles filtered out.")
        return
        
    logger.info("Content extracted successfully. Running NLP analysis...")
    analysis_result = nlp.process(crawled_data)
    
    logger.info("NLP Analysis completed. Formatting output...")
    
    output_file = "pipeline_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Pipeline finished! Check {output_file} for results.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run()
