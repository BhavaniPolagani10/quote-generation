from openai import AzureOpenAI, OpenAI
from typing import Dict, List
from src.config import Config

class AIEmailProcessor:
    """AI-powered email processor using OpenAI/Azure OpenAI"""
    
    def __init__(self):
        """Initialize AI client"""
        if Config.AZURE_OPENAI_API_KEY:
            # Use Azure OpenAI
            self.client = AzureOpenAI(
                api_key=Config.AZURE_OPENAI_API_KEY,
                api_version=Config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
            )
            self.model = Config.AZURE_OPENAI_DEPLOYMENT
            self.use_azure = True
        else:
            # Use OpenAI
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model = Config.OPENAI_MODEL
            self.use_azure = False
    
    def classify_email_thread(self, thread: Dict) -> str:
        """Classify if thread is requirement or general using AI"""
        
        # Prepare email content
        emails_text = "\n\n".join([
            f"From: {email.get('from')}\nTo: {email.get('to')}\nSubject: {email.get('subject')}\nBody: {email.get('body')}"
            for email in thread['emails']
        ])
        
        prompt = f"""Analyze the following email thread and classify it as either 'requirement' or 'general'.

A 'requirement' thread contains:
- Technical requirements
- Feature requests
- System specifications
- Project scope discussions
- Business needs

A 'general' thread contains:
- Casual conversations
- Meeting follow-ups without requirements
- Administrative messages
- Holiday schedules
- Thank you notes

Email Thread:
{emails_text}

Response format: Just respond with either 'requirement' or 'general'."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an email classification expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            classification = response.choices[0].message.content.strip().lower()
            return classification if classification in ['requirement', 'general'] else 'general'
        
        except Exception as e:
            print(f"❌ AI classification failed: {e}")
            return 'general'
    
    def extract_requirements(self, thread: Dict) -> List[Dict]:
        """Extract structured requirements using AI"""
        
        emails_text = "\n\n".join([
            f"From: {email.get('from')}\nDate: {email.get('date')}\nBody: {email.get('body')}"
            for email in thread['emails']
        ])
        
        prompt = f"""Extract all technical requirements from this email thread.

For each requirement, provide:
1. Requirement text (clear and concise)
2. Category (e.g., functionality, performance, integration, security, deployment)
3. Priority (high, medium, low)

Email Thread:
{emails_text}

Format your response as a numbered list with categories."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a requirements extraction expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            extracted_text = response.choices[0].message.content.strip()
            
            return [{
                'extracted_requirements': extracted_text,
                'extraction_method': 'AI',
                'model_used': self.model
            }]
        
        except Exception as e:
            print(f"❌ AI extraction failed: {e}")
            return []
