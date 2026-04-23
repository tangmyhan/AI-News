import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'AI-News')))

from shared.config import config
from elasticsearch import Elasticsearch

class ESClient:
    def __init__(self):
        es_url = config.ELASTICSEARCH_URL
        self.es = Elasticsearch([es_url])
        self.index_name = "articles_index"

    def create_index_if_not_exists(self):
        """Tạo index nếu chưa có, dùng để config mapping cho tìm kiếm"""
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "sapo": {"type": "text"},
                        "content": {"type": "text"},
                        "summary": {"type": "text"},
                        # Date type để sort/lọc
                        "published_date": {
                            "type": "date", 
                            "format": "strict_date_optional_time||epoch_millis"
                        }
                    }
                }
            }
            self.es.indices.create(index=self.index_name, body=mapping)
            print(f"[Elasticsearch] Đã tạo index: {self.index_name}")

    def index_article(self, article_id: str, document: dict):
        """Lưu (Index) một bài viết vào Elasticsearch để Full-text/Vector Search"""
        try:
            self.es.index(index=self.index_name, id=article_id, document=document)
            return True
        except Exception as e:
            print(f"[Elasticsearch] Lỗi khi index: {e}")
            return False

es_client = ESClient()
