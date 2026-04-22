import json
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# Schema cho Database
# Relevance Classification
class RelevanceResult(BaseModel):
    is_relevant: bool = Field(description="Bài báo có liên quan đến business, ngành Logistics/Năng lượng hay không")
    relevance_score: float = Field(description="Độ liên quan từ 0.0 đến 1.0")
    reason: str = Field(description="Giải thích ngắn gọn")

class ArticleAnalysis(BaseModel):
    summary: List[str] = Field(description="Tóm tắt bài báo trong 3 gạch đầu dòng ngắn gọn")
    impact_label: str = Field(description="Phân loại tác động: Tích cực, Tiêu cực, hoặc Trung lập")
    impact_score: float = Field(description="Điểm tác động từ -1.0 (Rất xấu) đến 1.0 (Rất tốt)")
    impact_reason: str = Field(description="Giải thích lý do tại sao đánh giá như vậy dựa trên lợi ích doanh nghiệp")

class NLPProcessor:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
        
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

        Ngữ cảnh:
        {business_context}

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
        3. Giải thích ngắn gọn

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

        Ngữ cảnh:
        {business_context}

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

        # Skip nếu không liên quan
        if (not relevance["is_relevant"]) or (relevance["relevance_score"] < 0.5):
            return {
                "metadata": {
                    "url": article_data.get("url"),
                    "categories": article_data.get("categories")
                },
                "relevance": relevance,
                "analysis": None
            }
        
        # analysis
        analysis = self.analysis_chain.invoke({
            "business_context": self.business_context,
            "title": article_data.get("title"),
            "sapo": article_data.get("sapo"),
            "content": article_data.get("content")[:1500],  # truncate tránh tốn token
            "format_instructions": self.analysis_parser.get_format_instructions()
        })

        return {
            "metadata": {
                "url": article_data.get("url"),
                "categories": article_data.get("categories")
            },
            "relevance": relevance,
            "analysis": analysis
        }

def main():
    with open('article.json', 'r', encoding='utf-8') as f:
        article_data = json.load(f)

    processor = NLPProcessor()
    print(f"--- Processing: {article_data['title']} ---")
    
    try:
        result = processor.process(article_data)

        print(json.dumps(result, indent=4, ensure_ascii=False))

        with open("processed_article.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    main()