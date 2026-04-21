import feedparser
import requests
from bs4 import BeautifulSoup
import json


rss_url = "https://tuoitre.vn/rss/tin-moi-nhat.rss"
feed = feedparser.parse(rss_url)

for entry in feed.entries:
    if entry.link == 'https://tuoitre.vn/lebanon-noi-dam-phan-voi-israel-tach-biet-khoi-xung-dot-o-iran-20260420191846879.htm':
        url = entry.link
        title = entry.title
        published = entry.published
        break

# url = 'https://tuoitre.vn/doc-nhanh-20-4-gia-dau-tang-manh-2-lanh-dao-cao-cap-cong-ty-cp-dap-vinachem-xin-tu-nhiem-20260420083808292.htm'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.content, 'html.parser')

# Lấy danh mục - category
detail_cate_div = soup.find('div', class_='detail-cate')
cate_list = [a.get_text(strip=True) for a in detail_cate_div.find_all('a')] if detail_cate_div else []

# Lấy sapo
sapo_tag = soup.find('h2', class_='detail-sapo')
sapo = sapo_tag.text.strip() if sapo_tag else None

# def get_sapo(soup):
#     tag = soup.select_one('h2[data-role="sapo"], h2.detail-sapo')
#     return tag.get_text(strip=True) if tag else None

content_div = soup.find('div', {'id': 'main-detail-body'})


def get_article_content(soup):
    content_div = soup.select_one('div.detail-content[data-role="content"]')
    if not content_div:
        return None

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


content, entities = get_article_content(soup)


topics = []
for a in soup.select('div.detail-tab a.item'):
    topics.append({
        "name": a.get_text(strip=True),
        "url": a['href']
    })

# Đóng gói dữ liệu và lưu ra file JSON
article_data = {
    "url": url,
    "title": title,
    "published": published,
    "category": cate_list,
    "sapo": sapo,
    "content": content,
    "entities": entities,
    "topics": topics
}

with open("article.json", "w", encoding="utf-8") as f:
    json.dump(article_data, f, ensure_ascii=False, indent=4)

print("Đã lưu kết quả vào file article.json")