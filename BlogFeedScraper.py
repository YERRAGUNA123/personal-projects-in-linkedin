import feedparser
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

RSS_FEEDS = {
    "DEV.to (Python)": "https://dev.to/feed/tag/python",
    "Hacker News": "https://hnrss.org/frontpage",
    "Medium (Technology)": "https://medium.com/feed/tag/technology"
}

def post_exists(link):
    res = supabase.table("company_feeds").select("id").eq("link", link).execute()
    return bool(res.data)

def insert_post(title, summary, link, source, published):
    if not post_exists(link):
        try:
            supabase.table("company_feeds").insert({
                "title": title,
                "summary": summary,
                "link": link,
                "source": source,
                "posted_at": published,
            }).execute()
            print(f"✅ Inserted: {title} ({source})")
        except Exception as e:
            print(f"❌ Insert failed for {source}: {e}")
    else:
        print(f"⏩ Skipped duplicate: {title} ({source})")

def scrape_feed(source_name, url):
    print(f"🌐 Scraping {source_name} …")
    feed = feedparser.parse(url)
    print(f"📄 {len(feed.entries)} posts found from {source_name}")
    for entry in feed.entries:
        title = entry.title
        summary = entry.get("summary", "")
        link = entry.link
        published = getattr(entry, "published", None)
        insert_post(title, summary, link, source_name, published)

def main():
    for name, url in RSS_FEEDS.items():
        scrape_feed(name, url)

if __name__ == "__main__":
    main()
