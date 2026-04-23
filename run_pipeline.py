import json
from ingestion.tuoitre_spider import TuoiTreSpider
from processing.nlp_service import NLPService
from shared.logger import get_logger

logger = get_logger("Pipeline")

def run():
    logger.info("Initializing spider and NLP service...")
    spider = TuoiTreSpider()
    nlp = NLPService()
    
    logger.info("Fetching latest URLs from Tuoi Tre RSS...")
    articles = spider.get_latest_urls()
    
    if not articles:
        logger.warning("No articles found in RSS.")
        return
        
    first_article = articles[0]
    logger.info(f"Crawling article: {first_article['url']}")
    
    crawled_data = spider.crawl_article(first_article['url'])
    
    if not crawled_data.get('content'):
        logger.warning("Failed to extract content.")
        return
        
    logger.info("Content extracted successfully. Running NLP analysis...")
    analysis_result = nlp.analyze_article(
        title=crawled_data.get('title') or first_article['title'],
        content=crawled_data['content'][:1500]
    )
    
    logger.info("NLP Analysis completed. Formatting output...")
    final_output = {
        "source_data": crawled_data,
        "ai_analysis": analysis_result
    }
    
    output_file = "pipeline_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Pipeline finished! Check {output_file} for results.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run()
