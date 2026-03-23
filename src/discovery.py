import feedparser
import chromadb
from datetime import datetime
import hashlib
from src.config import Config

class DiscoveryEngine:
    def __init__(self):
        # Initialize local ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DB_DIR)
        
        # Create or get collection for articles
        self.collection = self.chroma_client.get_or_create_collection(
            name="finance_articles",
            metadata={"hnsw:space": "cosine"}
        )
        
    def generate_id(self, text: str) -> str:
        """Generate a stable hash for an article ID"""
        return hashlib.md5(text.encode()).hexdigest()

    def fetch_rss_feeds(self):
        """Fetch and parse all configured RSS feeds"""
        articles = []
        for url in Config.FINANCE_RSS_FEEDS:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    # Some feeds use 'summary', some use 'description'
                    summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
                    title = getattr(entry, 'title', '')
                    link = getattr(entry, 'link', '')
                    published = getattr(entry, 'published', str(datetime.now()))
                    
                    if title and link:
                        articles.append({
                            "title": title,
                            "summary": summary,
                            "link": link,
                            "published": published,
                            "content_text": f"{title}. {summary}"
                        })
            except Exception as e:
                print(f"Error fetching feed {url}: {e}")
                
        return articles

    def filter_duplicates(self, articles):
        """Filter out articles that are too similar to previously processed ones"""
        novel_articles = []
        
        for article in articles:
            article_id = self.generate_id(article['link'])
            
            # Check if exactly this article exists
            existing = self.collection.get(ids=[article_id])
            if existing and existing['ids']:
                continue 
                
            # Check for semantic similarity
            try:
                results = self.collection.query(
                    query_texts=[article["content_text"]],
                    n_results=1
                )
                
                is_duplicate = False
                if results and results['distances'] and len(results['distances'][0]) > 0:
                    distance = results['distances'][0][0]
                    if distance < (1.0 - Config.SIMILARITY_THRESHOLD):
                        is_duplicate = True
                        
                if not is_duplicate:
                    novel_articles.append(article)
                    # Add to DB so we don't process it again next hour
                    self.collection.add(
                        documents=[article["content_text"]],
                        metadatas=[{"title": article["title"], "link": article["link"]}],
                        ids=[article_id]
                    )
            except Exception as e:
                print(f"Error checking similarity for {article['title']}: {e}")
                novel_articles.append(article)
                
        return novel_articles

    def run(self):
        """Run the discovery pipeline"""
        print(f"Fetching articles from {len(Config.FINANCE_RSS_FEEDS)} feeds...")
        raw_articles = self.fetch_rss_feeds()
        print(f"Fetched {len(raw_articles)} total articles.")
        
        print("Filtering duplicates using ChromaDB...")
        novel_articles = self.filter_duplicates(raw_articles)
        print(f"Found {len(novel_articles)} novel articles.")
        
        return novel_articles
