# import feedparser

# rss_url = "https://tuoitre.vn/rss/tin-moi-nhat.rss"
# feed = feedparser.parse(rss_url)

# for entry in feed.entries:
#     print(entry.title)
#     print(entry.link)
#     print(entry.published)
#     print("-" * 50)



import feedparser
import requests
from bs4 import BeautifulSoup

url = 'https://tuoitre.vn/hut-nguon-luc-xay-kho-du-tru-xang-dau-20260420075229198.htm'
response = requests.get(url, timeout=10)
soup = BeautifulSoup(response.content, 'html.parser')

# ===============================
# CATEGORY
# ===============================
detail_cate_div = soup.find('div', class_='detail-cate')
cate_list = [a.get_text(strip=True) for a in detail_cate_div.find_all('a')] if detail_cate_div else []
print("Category:", cate_list)

# ===============================
# SAPO
# ===============================
sapo_tag = soup.find('h2', class_='detail-sapo')
sapo = sapo_tag.get_text(strip=True) if sapo_tag else None
print("Sapo:", sapo)

# ===============================
# MAIN CONTENT
# ===============================
content_div = soup.find('div', class_='detail-content afcbc-body')

if content_div:
    # 1️⃣ Remove iframe (video, embed, quảng cáo)
    for tag in content_div.find_all(['iframe', 'script']):
        tag.decompose()

    # 2️⃣ Remove related news / box liên quan
    # for related in content_div.select(
    #     '.VCSortableInPreviewMode, .news-relation, .box-related, .related-news'
    # ):
    #     related.decompose()

    # 3️⃣ Remove quảng cáo
    for ads in content_div.select(
        '.ads, .ads-box, [class*="qc"], [id*="adm"], [id*="ads"]'
    ):
        ads.decompose()

    # ===============================
    # OUTPUT
    # ===============================
    content_text = '\n'.join(
        p.get_text(strip=True)
        for p in content_div.find_all(['p', 'h2', 'h3', 'blockquote', 'figcaption'])
        if p.get_text(strip=True)
    )

    entities = []
    for a in content_div.select('a.VCCTagItemInNews'):
        entities.append(a.get_text(strip=True))

    print("============ ENTITIES ============")
    print(entities)

    content_html = content_div.decode_contents()

    print("============ CONTENT TEXT ============")
    print(content_text)

else:
    print("❌ Không tìm thấy detail-content afcbc-body")
