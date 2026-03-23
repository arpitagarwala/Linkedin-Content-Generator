import google.generativeai as genai
from src.config import Config

class ContentGenerator:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def generate_post(self, scored_article):
        """Generate a LinkedIn post using 80% English and 20% Hinglish."""
        
        article = scored_article['article']
            
        system_prompt = f"""
        You are a young, sharp Chartered Accountant (CA) content creator. You explain complex finance topics perfectly to peers, GenZ, and students on LinkedIn.
        
        TASK: Write a LinkedIn post based on the following article:
        Title: {article['title']}
        Summary: {article['summary']}
        
        CONSTRAINTS:
        1. Tone: Friendly but bold, highly educational.
        2. Language: Strictly ~80% English and ~20% Hinglish. 
           - Use Hinglish for emphasis, relatable frustrations, or conversational transitions (e.g., 'Sach batau toh...', 'Ye move directly impact karega...', 'Boss, this is huge.').
           - Do NOT use Hinglish for technical financial terms. Keep them in English.
        3. Structure:
           [Topic Title]
           ---
           [Hook]: 1-2 lines. Stop the scroll with a bold claim, a relatable pain point, or a shocking fact.
           ---
           [Main Content]: Short paragraphs (1-3 sentences max). Bold key metrics. Use storytelling arc (Problem -> Change -> Impact).
           ---
           [Key Takeaways]: 3 bullet points.
           ---
           [CTA]: Conclude by politely asking for the reader's views or thoughts on the topic (do not ask for an aggressive debate/argument). Use a friendly, conversational tone like: "Aapne to seekh liya, ab apne dosto ko bhi sikha do, taki wo bhi aapko finance ka guru bulana shuru krde... What are your thoughts on this?"
           [Hashtags]: 3-5 relevant functional tags.
        
        CRITICAL FORMATTING RULES FOR LINKEDIN:
        - DO NOT USE markdown formatting like **bold**, *italics*, or --- lines. LinkedIn does not process markdown and treats it as plain text. 
        - DO NOT use hashes (#) for headings.
        - Only use standard plain text, paragraph line breaks, and unicode emojis to structure and separate your points.
        
        Output the final post text directly. No meta-commentary.
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating post: {e}")
            return None
