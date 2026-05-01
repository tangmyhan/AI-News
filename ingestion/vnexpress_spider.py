import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import json

class VNExpressSpider:
    def __init__(self):
        self.rss_url = "https://vnexpress.net/rss/kinh-doanh.rss"
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.categories_filter = ['kinh doanh', 'chứng khoán', 'bất động sản', 'doanh nghiệp', 'vĩ mô']

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

    def crawl_article(self, article_meta: Dict[str, str]) -> Optional[Dict[str, Any]]:
        url = article_meta['url']
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Lấy Category
            ul_breadcrumb = soup.find('ul', class_='breadcrumb')
            cate_list = [a.get_text(strip=True) for a in ul_breadcrumb.find_all('a')] if ul_breadcrumb else []

            # Kiểm tra lọc categories
            # if cate_list and not any(c.lower() in self.categories_filter for c in cate_list):
            #     return None

            # Lấy Sapo
            sapo_tag = soup.find('p', class_='description')
            sapo = sapo_tag.get_text(strip=True) if sapo_tag else None

            # Lấy Content
            content_div = soup.find('article', class_='fck_detail')
            content = None
            if content_div:
                texts = [p.get_text(strip=True) for p in content_div.find_all('p', class_='Normal')]
                content = "\n\n".join(texts)

            # Lấy Entities (Tags)
            meta_tag = soup.find('meta', {'name': 'its_tag'})
            entities = [tag.strip() for tag in meta_tag['content'].split(',')] if meta_tag and 'content' in meta_tag.attrs else []

            # Lấy Topics
            topics = []
            tags_wrapper = soup.find('div', class_='tags')
            if tags_wrapper:
                for tag in tags_wrapper.find_all('a'):
                    topics.append({"name": tag.get_text(strip=True), "url": tag.get('href', '')})
                    
            if not topics and entities:
                 # Backup for topics
                 topics = [{"name": e, "url": f"/tag/{e}"} for e in entities[:3]]

            return {
                "title": article_meta['title'],
                "url": url,
                "published": article_meta['published'],
                "categories": cate_list or None,
                "sapo": sapo,
                "content": content,
                "entities": entities or None,
                "topics": topics or None
            }
        except Exception as e:
            print(f"Lỗi khi crawl {url}: {e}")
            return None

    def save_to_json(self, data: Any, filename: str = "vnexpress_articles.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"\nĐã lưu {len(data)} bài viết vào {filename}")

if __name__ == "__main__":
    spider = VNExpressSpider()
    
    print("RSS...")
    news_entries = spider.get_latest_news_entries()
    
    saved_articles = []
    print(f"Crawl và Lọc {len(news_entries)} tin tức...")

    for entry in news_entries[:10]: # test 10 bài đầu
        article_data = spider.crawl_article(entry)
        
        if article_data:
            saved_articles.append(article_data)
            categories_str = ", ".join(article_data['categories']) if article_data['categories'] else 'N/A'
            print(f"  + OK: {article_data['title'][:50]}... ({categories_str})")
        
    print(f"Hoàn tất thu thập.")
    if saved_articles:
        spider.save_to_json(saved_articles)
    else:
        print("Không có tin nào phù hợp với bộ lọc danh mục.")