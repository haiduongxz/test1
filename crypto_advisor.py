import feedparser
import os
import json
import requests
from datetime import datetime
import csv
from dotenv import load_dotenv

# === LOAD ENV ===
load_dotenv()
OPENROUTER_API_KEY = (
    "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"
)

# === MODEL CẦN DÙNG ===
MODEL = "mistralai/mistral-7b-instruct"  # Bạn có thể thử: meta-llama/llama-3-8b-instruct, openchat/openchat-3.5


# === GỌI GPT QUA OPENROUTER ===
def ask_gpt(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "CryptoBot",
    }

    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Bạn là chuyên gia phân tích tài chính crypto.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 3000,
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(
            f"❌ Lỗi gọi API: {response.status_code} {response.text if response else str(e)}"
        )
        return "Không thể phân tích do lỗi API."


def save_articles_to_json(articles, filename="articles.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    today_str = datetime.now().strftime("%Y-%m-%d")
    for title in articles:
        data.append({"date": today_str, "title": title})

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu {len(articles)} bài vào {filename}.")


def save_articles_to_csv(articles, filename="articles.csv"):
    today_str = datetime.now().strftime("%Y-%m-%d")
    rows = [{"date": today_str, "title": title} for title in articles]

    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "title"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    print(f"Đã lưu {len(articles)} bài vào {filename}.")


def get_rss_articles(rss_url, max_articles=25, headers=None):
    feed = feedparser.parse(rss_url, request_headers=headers)
    print(f"Số bài trong feed: {len(feed.entries)}")
    for entry in feed.entries[:max_articles]:
        print(entry.title)
    return [entry.title for entry in feed.entries[:max_articles]]


def load_saved_articles(filename="articles.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def build_prompt(all_articles):
    limited_articles = all_articles[-20:]
    news_summary = "\n".join(
        f"- [{item['date']}] {item['title']}" for item in limited_articles
    )
    prompt = f"""
Bạn là chuyên gia phân tích thị trường crypto.

Dưới đây là tổng hợp các tin tức crypto trong thời gian gần đây:

{news_summary}

Hãy phân tích xu hướng thị trường crypto dựa trên những tin tức này và đưa ra khuyến nghị đầu tư nên mua cái nào và bán cái nào. Giải thích ngắn gọn, rõ ràng.
"""
    return prompt


def main():
    rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    new_articles = get_rss_articles(rss_url, headers=headers)
    print(f"Lấy được {len(new_articles)} bài mới hôm nay.")

    saved_articles = load_saved_articles()
    saved_titles = {item["title"] for item in saved_articles}

    combined_articles = saved_articles.copy()
    added_count = 0
    for title in new_articles:
        if title not in saved_titles:
            combined_articles.append(
                {"date": datetime.now().strftime("%Y-%m-%d"), "title": title}
            )
            added_count += 1

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(combined_articles, f, ensure_ascii=False, indent=2)
    print(f"Tổng cộng {len(combined_articles)} bài đã lưu ({added_count} bài mới).")

    if not combined_articles:
        print("Không có bài mới để phân tích, kết thúc.")
        return

    prompt = build_prompt(combined_articles)
    result = ask_gpt(prompt)

    print("===== KẾT QUẢ PHÂN TÍCH TỪ GPT (OpenRouter) =====")
    print(result)


if __name__ == "__main__":
    main()
