import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import json

class TuoiTreSpider:
    def __init__(self):
        self.rss_url = "https://tuoitre.vn/rss/tin-moi-nhat.rss"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.categories_filter = [
            'kinh doanh', 'thế giới', 'chứng khoán', 'tin tức thị trường', 
            'phân tích - nhận định', 'doanh nghiệp niêm yết', 
            'hướng dẫn đầu tư', 'doanh nghiệp', 'cùng luận bàn'
        ]

    def get_latest_news_entries(self) -> List[Dict[str, str]]:
        feed = feedparser.parse(self.rss_url)
        return [
            {
                "title": entry.title,
                "url": entry.link,
                "published": entry.published
            }
            for entry in feed.entries
        ]

    def extract_content(self, html: bytes) -> tuple[Optional[str], List[str]]:
        soup = BeautifulSoup(html, 'html.parser')
        content_div = soup.select_one('div.detail-content[data-role="content"]')
        if not content_div:
            return None, []

        # Dọn rác HTML
        for tag in content_div.select(
            'script, style, iframe, .adbro, .InreadPc, .kbwscwl-relatedbox, '
            '.OneNewsTitle, .readmore-body-box, .VCSortableInPreviewMode, [type="RelatedOneNews"]'
        ):
            tag.decompose()

        texts = [el.get_text(strip=True) for el in content_div.find_all(['p', 'h2', 'h3', 'blockquote', 'figcaption']) if el.get_text(strip=True)]
        entities = [a.get_text(strip=True) for a in content_div.select('a.VCCTagItemInNews')]

        return "\n\n".join(texts), entities

    def crawl_article(self, article_meta: Dict[str, str]) -> Optional[Dict[str, Any]]:
        url = article_meta['url']
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Lấy Category
            detail_cate_div = soup.find('div', class_='detail-cate')
            cate_list = [a.get_text(strip=True) for a in detail_cate_div.find_all('a')] if detail_cate_div else []

            # Kiểm tra lọc categories
            if not any(c.lower() in self.categories_filter for c in cate_list):
                return None

            # Lấy Sapo
            sapo_tag = soup.find('h2', class_='detail-sapo')
            sapo = sapo_tag.get_text(strip=True) if sapo_tag else None

            # Lấy Content & Entities
            content, entities = self.extract_content(response.content)

            # Lấy Topics/Tags
            topics = [{"name": a.get_text(strip=True), "url": a['href']} for a in soup.select('div.detail-tab a.item')]

            return {
                "title": article_meta['title'],
                "url": url,
                "published": article_meta['published'],
                "categories": cate_list,
                "sapo": sapo,
                "content": content,
                "entities": entities,
                "topics": topics
            }
        except Exception as e:
            print(f"Lỗi khi crawl {url}: {e}")
            return None

    def save_to_json(self, data: Any, filename: str = "articles_filtered.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\nĐã lưu {len(data)} bài viết vào {filename}")

if __name__ == "__main__":
    spider = TuoiTreSpider()
    
    print("RSS...")
    news_entries = spider.get_latest_news_entries()
    
    saved_articles = []
    print(f"Crawl và Lọc {len(news_entries)} tin tức...")

    for entry in news_entries:
        article_data = spider.crawl_article(entry)
        
        if article_data:
            saved_articles.append(article_data)
            print(f"  + OK: {article_data['title'][:50]}... ({article_data['categories'][0]})")
        
    print(f"Hoàn tất thu thập.")
    if saved_articles:
        spider.save_to_json(saved_articles)
    else:
        print("Không có tin nào phù hợp với bộ lọc danh mục.")