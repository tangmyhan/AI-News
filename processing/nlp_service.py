import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

DEFAULT_BUSINESS_CONTEXT = """
Doanh nghiệp chúng ta là một tập đoàn chuyên về Logistics và Đầu tư hạ tầng năng lượng tại Việt Nam. 
Hội đồng quản trị quan tâm đến: Chi phí đầu vào (xăng dầu), chính sách nhà nước, và các rủi ro vĩ mô.
"""

class NLPService:
    def __init__(self, model_name="gpt-4o-mini", temperature=0):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
        )
        
        template = """
{business_context}

Dựa trên bài báo dưới đây, hãy thực hiện các nhiệm vụ sau:
1. Tóm tắt bài báo trong tối đa 3 gạch đầu dòng (summary).
2. Đánh giá tác động đối với doanh nghiệp (Sắc thái): 
   - Label: [Tích cực / Tiêu cực / Trung lập] (impact_label)
   - Điểm số: (từ -1.0 đến 1.0) (impact_score)
   - Lý do: Giải thích tại sao có lợi hoặc hại. (impact_reason)
3. Trích xuất các thực thể quan trọng (Tên riêng, Tổ chức, Con số). (entities)

Bài báo:
Tiêu đề: {title}
Nội dung: {content}

Kết quả trả về định dạng JSON thuần túy theo format sau (Không kèm markdown json):
{{
    "summary": ["gạch đầu dòng 1", "gạch đầu dòng 2"],
    "impact_label": "Tích cực",
    "impact_score": 0.5,
    "impact_reason": "lý do...",
    "entities": ["thực thể 1", "thực thể 2"]
}}
"""
        self.prompt = PromptTemplate(
            input_variables=["business_context", "title", "content"],
            template=template
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def analyze_article(self, title: str, content: str, business_context: str = DEFAULT_BUSINESS_CONTEXT) -> dict:
        """Runs the LLM chain to analyze an article and returns the JSON result."""
        result_text = self.chain.run(
            business_context=business_context,
            title=title,
            content=content
        )
        
        try:
            # Clean markdown formatting if present
            cleaned_text = result_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_text)
        except Exception as e:
            print(f"Error parsing JSON from LLM: {e}")
            print(f"Raw Output: {result_text}")
            return {"error": "Failed to parse JSON", "raw_output": result_text}

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test service with sample data
    sample_title = "Giá xăng dầu dự kiến sẽ giảm trong kỳ điều hành tới"
    sample_content = "Các chuyên gia dự báo giá xăng E5 RON 92 trong nước có thể giảm khoảng 500 đồng/lít trong tuần sau do ảnh hưởng từ thị trường thế giới."
    
    service = NLPService()
    print("Testing NLP Service...")
    res = service.analyze_article(sample_title, sample_content)
    print(json.dumps(res, indent=2, ensure_ascii=False))
