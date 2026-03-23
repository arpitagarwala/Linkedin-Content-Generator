import json
import re
import google.generativeai as genai
from src.config import Config

class InsightFilter:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def score_articles_batch(self, articles):
        """Use LLM to score all articles in a single API call to save free-tier quota."""
        if not articles:
            return []
            
        # We will prepare a block of text
        articles_text = ""
        for idx, art in enumerate(articles):
            articles_text += f"\n[ID: {idx}] Title: {art['title']}\nSummary: {art['summary']}\n---"
            
        prompt = f"""
        You are a senior finance content strategist for a LinkedIn channel targeting GenZ, Chartered Accountants (CAs), and finance students.
        
        Evaluate the following list of news articles and pick the TOP 5 most relevant articles for our audience.
        
        Scoring Criteria (0-10 for each, total 30):
        1. Relevance: Impact on CAs, GenZ, or personal finance.
        2. Novelty: Is it a new perspective or structural change?
        3. Audience Value: Actionability and shareability factor.
        
        CRITICAL NEGATIVE FILTERS (Instantly score 0 if true):
        - STRICTLY AVOID any articles about daily Gold/Silver prices, crude oil variations, or commodities.
        - STRICTLY AVOID any day-trading, pure speculation, or generic stock price movements.
        
        Only pick articles that truly stand out (aim for 24+ score out of 30).
        
        Articles:
        {articles_text}
        
        Respond ONLY with a valid JSON array of objects in this exact format. Do not use markdown formatting or backticks:
        [
            {{"id": 0, "relevance": 9, "novelty": 8, "audience_value": 8, "reasoning": "brief 1-sentence explanation"}},
            {{"id": 5, "relevance": 8, "novelty": 9, "audience_value": 9, "reasoning": "..."}}
        ]
        """
        
        # Initialize default results for ALL articles
        results_map = {}
        for idx, art in enumerate(articles):
            results_map[idx] = {
                "article": art,
                "score": 0,
                "reasoning": "Rejected by bulk filtering to save API quota or scored below threshold."
            }
            
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Robust JSON array extraction
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if not match:
                raise ValueError("No JSON array found parsing AI response")
                
            top_analyses = json.loads(match.group(0))
            
            for item in top_analyses:
                idx = int(item['id'])
                if idx in results_map:
                    score = int(item.get('relevance', 0)) + int(item.get('novelty', 0)) + int(item.get('audience_value', 0))
                    results_map[idx]['score'] = score
                    results_map[idx]['reasoning'] = item.get('reasoning', '')
                    
        except Exception as e:
            print(f"Error bulk scoring articles: {e}")
            for idx in results_map:
                results_map[idx]['reasoning'] = f"API Quota Error: {str(e)}"
                
        return list(results_map.values())
