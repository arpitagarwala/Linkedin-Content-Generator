import smtplib
from email.mime.text import MIMEText
import requests
import google.generativeai as genai
from src.config import Config

class QualityControl:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.editor_model = genai.GenerativeModel('gemini-2.5-flash')
        
    def ai_review(self, draft_post: str) -> bool:
        """
        Secondary LLM node to review the generated content against strict constraints.
        Returns True if passed, False if rejected.
        """
        prompt = f"""
        You are an AI Editor for a premium finance content page.
        Review the following LinkedIn post draft.
        
        Constraints to check:
        1. Generic Summary Check: Does it sound like a boring Wikipedia article?
        2. Language Balance: Is the Hinglish cringy or clearly exceeding 30%?
        
        Draft Post:
        {draft_post}
        
        Is this post high-quality and safe to proceed to human approval?
        Answer with ONLY 'PASS' or 'REJECT'.
        """
        try:
            response = self.editor_model.generate_content(prompt)
            decision = response.text.strip().upper()
            return 'PASS' in decision
        except Exception as e:
            print(f"AI Review error: {e}")
            return False

    def notify_telegram(self, message: str):
        """Send notification via Telegram Bot"""
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            print("Telegram credentials missing, skipping Telegram notification.")
            return
            
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": Config.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")

    def notify_email(self, message: str, is_html: bool = False):
        if not Config.EMAIL_SENDER or not Config.EMAIL_PASSWORD or not Config.EMAIL_RECEIVER:
            print("Email credentials missing. Skipping notification.")
            return

        try:
            msg = MIMEText(message, 'html' if is_html else 'plain')
            msg['Subject'] = '🚨 AI Agent: New LinkedIn Draft Ready!'
            msg['From'] = Config.EMAIL_SENDER
            msg['To'] = Config.EMAIL_RECEIVER

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
                server.send_message(msg)
            print("Email notification sent successfully.")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def request_human_approval(self, draft_post: str, article_title: str):
        """Triggers the human-in-the-loop notifications."""
        
        formatted_draft = draft_post.replace('\n', '<br>')
        
        email_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #0077b5;">✨ New LinkedIn Draft Ready</h2>
                <p><strong>Topic:</strong> {article_title}</p>
                <hr>
                <div style="background-color: #f3f2ef; padding: 15px; border-radius: 5px; font-size: 15px;">
                    {formatted_draft}
                </div>
                <br><br>
                <a href="https://www.linkedin.com/feed/" style="background-color: #0077b5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                    Post to LinkedIn
                </a>
            </body>
        </html>
        """
        print("Sending draft for human approval via HTML Email...")
        self.notify_email(email_html, is_html=True)
