import redis
from typing import List

class DeduplicationFilter:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.set_key = "ainews:crawled_urls"

    def is_new(self, url: str) -> bool:
        """Kiểm tra URL mới. Thêm vào Redis nếu là mới và trả về True. Nếu đã tồn tại trả về False."""
        # sadd trả về 1 nếu item được thêm mới, 0 nếu đã tồn tại trong set
        result = self.redis_client.sadd(self.set_key, url)
        return result == 1

    def filter_new_articles(self, articles: List[dict]) -> List[dict]:
        """Lọc ra danh sách các bài báo chưa từng crawl."""
        new_articles = []
        for article in articles:
            url = article.get("url")
            if url and self.is_new(url):
                new_articles.append(article)
            else:
                print(f"Skipping duplicate: {url}")
        return new_articles
