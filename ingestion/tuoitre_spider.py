import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

class TuoiTreSpider:
    def __init__(self):
        self.rss_url = "https://tuoitre.vn/rss/tin-moi-nhat.rss"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    def get_latest_urls(self) -> List[Dict[str, str]]:
        """Fetch latest news URLs from Tuoi Tre RSS feed."""
        feed = feedparser.parse(self.rss_url)
        results = []
        for entry in feed.entries:
            results.append({
                "title": entry.title,
                "url": entry.link,
                "published": entry.published
            })
        return results

    def extract_content(self, html: bytes) -> tuple[Optional[str], List[str]]:
        """Extract main content and entities from article HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        content_div = soup.select_one('div.detail-content[data-role="content"]')
        if not content_div:
            return None, []

        # Remove redundant elements
        for tag in content_div.select(
            'script, style, iframe, .adbro, .InreadPc, '
            '.kbwscwl-relatedbox, .OneNewsTitle, '
            '.readmore-body-box, .VCSortableInPreviewMode[type="RelatedNewsBox"], '
            '[type="RelatedOneNews"]'
        ):
            tag.decompose()

        texts = []
        for el in content_div.find_all(['p', 'h2', 'h3', 'blockquote', 'figcaption']):
            text = el.get_text(strip=True)
            if text:
                texts.append(text)

        entities = []
        for a in content_div.select('a.VCCTagItemInNews'):
            entities.append(a.get_text(strip=True))

        return "\n\n".join(texts), entities

    def crawl_article(self, url: str) -> Dict[str, Any]:
        """Crawl a specific Tuoi Tre article by URL."""
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            return {}

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Category
        detail_cate_div = soup.find('div', class_='detail-cate')
        cate_list = [a.get_text(strip=True) for a in detail_cate_div.find_all('a')] if detail_cate_div else []

        # Sapo (Summary)
        sapo_tag = soup.find('h2', class_='detail-sapo')
        sapo = sapo_tag.text.strip() if sapo_tag else None

        # Title from HTML if needed, but usually passed via RSS
        title_tag = soup.find('h1', class_='detail-title')
        title = title_tag.text.strip() if title_tag else None

        # Content & Entities
        content, entities = self.extract_content(response.content)

        # Topics
        topics = []
        for a in soup.select('div.detail-tab a.item'):
            topics.append({
                "name": a.get_text(strip=True),
                "url": a['href']
            })

        return {
            "title": title,
            "url": url,
            "categories": cate_list,
            "sapo": sapo,
            "content": content,
            "entities": entities,
            "topics": topics
        }

    def save_to_json(self, data: Dict[str, Any], filename: str = "article.json"):
        """Save article data to JSON file."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Đã lưu kết quả vào file {filename}")

    def save_to_db(self, data: Dict[str, Any]):
        """Save article data to database."""
        pass

if __name__ == "__main__":
    spider = TuoiTreSpider()
    print("Fetching RSS...")
    latest = spider.get_latest_urls()
    print(f"Found {len(latest)} articles in RSS.")
    if latest:
        print(f"Crawling first article: {latest[0]['title']}")
        article_data = spider.crawl_article(latest[0]['url'])
        print("\nCrawled Data:")
        import json
        print(json.dumps(article_data, ensure_ascii=False, indent=2))
        spider.save_to_json(article_data)
