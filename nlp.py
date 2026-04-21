from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

BUSINESS_CONTEXT = """
Doanh nghiệp chúng ta là một tập đoàn chuyên về Logistics và Đầu tư hạ tầng năng lượng tại Việt Nam. 
Hội đồng quản trị quan tâm đến: Chi phí đầu vào (xăng dầu), chính sách nhà nước, và các rủi ro vĩ mô.
"""

template = """
{business_context}

Dựa trên bài báo dưới đây, hãy thực hiện các nhiệm vụ sau:
1. Tóm tắt bài báo trong tối đa 3 gạch đầu dòng.
2. Đánh giá tác động đối với doanh nghiệp (Sắc thái): 
   - Label: [Tích cực / Tiêu cực / Trung lập]
   - Điểm số: (từ -1.0 đến 1.0)
   - Lý do: Giải thích tại sao có lợi hoặc hại.
3. Trích xuất các thực thể quan trọng (Tên riêng, Tổ chức, Con số).

Bài báo:
Tiêu đề: {title}
Nội dung: {content}

Kết quả trả về định dạng JSON:
"""

prompt = PromptTemplate(
    input_variables=["business_context", "title", "content"],
    template=template
)


# Khởi tạo LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,  # 0 = output logic, không sáng tạo
    api_key=os.getenv("OPENAI_API_KEY")
)

# Tạo Chain
chain = LLMChain(llm=llm, prompt=prompt)

# Chạy phân tích
result = chain.run(
    business_context=BUSINESS_CONTEXT,
    title=data["title"],
    content=data["content"]
)

print(result)
