import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from shared.config import config

class RelevanceResult(BaseModel):
    is_relevant: bool = Field(description="Bài báo có liên quan đến business, ngành Logistics/Năng lượng hay không")
    relevance_score: float = Field(description="Độ liên quan từ 0.0 đến 1.0")

class ArticleAnalysis(BaseModel):
    summary: List[str] = Field(description="Tóm tắt bài báo trong 3 gạch đầu dòng ngắn gọn")
    impact_label: str = Field(description="Phân loại tác động: Tích cực, Tiêu cực, hoặc Trung lập")
    impact_score: float = Field(description="Điểm tác động từ -1.0 (Rất xấu) đến 1.0 (Rất tốt)")
    impact_reason: str = Field(description="Giải thích lý do tại sao đánh giá như vậy dựa trên lợi ích doanh nghiệp")

class NLPProcessor:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY)
        
        # Parsers
        self.relevance_parser = JsonOutputParser(pydantic_object=RelevanceResult)
        self.analysis_parser = JsonOutputParser(pydantic_object=ArticleAnalysis)

        # Business Context
        self.business_context = (
            "Doanh nghiệp là một tập đoàn chuyên về Logistics và Đầu tư hạ tầng năng lượng tại Việt Nam, quan tâm sát sao đến "
            "biến động chính trị thế giới, giá năng lượng và các chính sách ngoại giao "
            "có thể ảnh hưởng đến chuỗi cung ứng toàn cầu."
        )

        # Build chains
        self._build_relevance_chain()
        self._build_analysis_chain()
    
    # relevance chain
    def _build_relevance_chain(self):
        template = """
        Bạn là chuyên gia đánh giá mức độ liên quan của tin tức với doanh nghiệp.

        Ngữ cảnh: {business_context}

        Bài báo được coi là LIÊN QUAN nếu có yếu tố:
        - Logistics / vận tải / xuất nhập khẩu
        - Năng lượng / xăng dầu / giá dầu / điện
        - Chuỗi cung ứng / thương mại quốc tế
        - Chính sách kinh tế ảnh hưởng doanh nghiệp

        KHÔNG liên quan nếu chỉ là:
        - Tội phạm đơn lẻ
        - Đời sống xã hội
        - Tin tức cá nhân

        Nhiệm vụ:
        1. Đánh giá is_relevant (true/false)
        2. Cho điểm relevance_score (từ 0.0 đến 1.0)

        Tiêu đề: {title}
        Sapo: {sapo}

        {format_instructions}
        """
        prompt = ChatPromptTemplate.from_template(template)
        self.relevance_chain = (
            prompt
            | self.llm
            | self.relevance_parser
        )

    # 4. analysis chain
    def _build_analysis_chain(self):
        template = """
        Bạn là chuyên gia phân tích rủi ro cho Hội đồng quản trị.

        Ngữ cảnh: {business_context}

        Nhiệm vụ:
        1. Tóm tắt bài báo thành 3 ý ngắn
        2. Đánh giá tác động đến doanh nghiệp:
        - Tích cực / Tiêu cực / Trung lập
        3. Cho điểm impact_score (từ -1 đến 1)
        4. Giải thích lý do

        Tiêu đề: {title}
        Sapo: {sapo}
        Nội dung: {content}

        {format_instructions}
        """
        prompt = ChatPromptTemplate.from_template(template)
        self.analysis_chain = (
            prompt
            | self.llm
            | self.analysis_parser
        )

    def process(self, article_data: dict):
        relevance = self.relevance_chain.invoke({
            "business_context": self.business_context,
            "title": article_data.get("title"),
            "sapo": article_data.get("sapo"),
            "format_instructions": self.relevance_parser.get_format_instructions()
        })

        metadata = {
            "title": article_data.get("title"),
            "url": article_data.get("url"),
            "published": article_data.get("published"),
            "categories": article_data.get("categories"),
            "sapo": article_data.get("sapo"),
            "content": article_data.get("content"),
            "entities": article_data.get("entities"),
            "topics": article_data.get("topics")
        }

        # Skip nếu không liên quan
        if (not relevance.get("is_relevant")) or (relevance.get("relevance_score") < 0.5):
            return None
        
        # analysis
        analysis = self.analysis_chain.invoke({
            "business_context": self.business_context,
            "title": article_data.get("title"),
            "sapo": article_data.get("sapo"),
            "content": (article_data.get("content") or "")[:1500], 
            "format_instructions": self.analysis_parser.get_format_instructions()
        })

        return {
            "metadata": metadata,
            "relevance": relevance,
            "analysis": analysis
        }

def main():
    with open('article.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)

    if not articles:
        print("Không có bài báo nào để xử lý.")
        return

    processor = NLPProcessor()
    processed_results = []

    for article_data in articles:
        print(f"\nĐang xử lý: {article_data.get('title')}")
        
        try:
            result = processor.process(article_data)
            if result is None:
                print("Status: Bài báo không liên quan -> Bỏ qua")
                continue
                
            processed_results.append(result)
            print("Status: Bài báo liên quan -> Đã xử lý")

        except Exception as e:
            print(f"Lỗi khi xử lý bài '{article_data.get('title')}': {e}")

    with open("processed_articles.json", "w", encoding="utf-8") as f:
        json.dump(processed_results, f, ensure_ascii=False, indent=4)
    
    print(f"\nĐã xử lý xong {len(processed_results)} bài báo.")

if __name__ == "__main__":
    main()