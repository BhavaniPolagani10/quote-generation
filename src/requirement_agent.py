import re
from datetime import datetime
from pymongo import MongoClient
from typing import List, Dict
from src.config import Config
from src.ai_processor import AIEmailProcessor

class RequirementAgent:
    """Agent to process and store requirement-related email conversations"""
    
    def __init__(self, use_ai=True):
        """Initialize MongoDB connection and AI processor"""
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DB]
        self.requirements_collection = self.db['requirement_emails']
        self.use_ai = use_ai
        
        if use_ai:
            try:
                self.ai_processor = AIEmailProcessor()
                print("✅ AI Processor initialized")
            except Exception as e:
                print(f"⚠️  AI initialization failed: {e}")
                print("   Falling back to keyword-based classification")
                self.use_ai = False
    
    def parse_email_file(self, file_path: str) -> List[Dict]:
        """Parse the email conversations file into threads"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        threads = []
        thread_blocks = content.split('THREAD_ID: ')[1:]
        
        for block in thread_blocks:
            lines = block.strip().split('\n')
            thread_id = lines[0].strip()
            
            emails = []
            email_parts = block.split('---\n')[1:]
            
            for part in email_parts:
                if not part.strip():
                    continue
                
                email_data = self._parse_single_email(part)
                if email_data:
                    emails.append(email_data)
            
            if emails:
                threads.append({
                    'thread_id': thread_id,
                    'emails': emails
                })
        
        return threads
    
    def _parse_single_email(self, email_text: str) -> Dict:
        """Parse a single email from text"""
        lines = [line for line in email_text.split('\n') if line.strip()]
        
        email_data = {}
        body_lines = []
        parsing_body = False
        
        for line in lines:
            if line.startswith('From:'):
                email_data['from'] = line.replace('From:', '').strip()
            elif line.startswith('To:'):
                email_data['to'] = line.replace('To:', '').strip()
            elif line.startswith('Date:'):
                email_data['date'] = line.replace('Date:', '').strip()
            elif line.startswith('Subject:'):
                email_data['subject'] = line.replace('Subject:', '').strip()
                parsing_body = True
            elif parsing_body and line.strip() != '---':
                body_lines.append(line.strip())
        
        email_data['body'] = '\n'.join(body_lines)
        return email_data
    
    def is_requirement_thread_keyword(self, thread: Dict) -> bool:
        """Detect if thread contains requirements using keyword matching"""
        requirement_keywords = [
            'requirement', 'need', 'feature', 'functionality',
            'system', 'integration', 'users', 'deployment',
            'timeline', 'alert', 'notification', 'access',
            'permission', 'tracking', 'audit', 'compliance',
            'dashboard', 'report', 'api', 'database',
            'authentication', 'security', 'performance',
            'scalability', 'interface', 'workflow'
        ]
        
        # Check subject and body of all emails
        for email in thread['emails']:
            text = (email.get('subject', '') + ' ' + email.get('body', '')).lower()
            
            if any(keyword in text for keyword in requirement_keywords):
                return True
        
        return False
    
    def classify_thread(self, thread: Dict) -> str:
        """Classify thread as requirement or general"""
        if self.use_ai:
            try:
                category = self.ai_processor.classify_email_thread(thread)
                return category
            except Exception as e:
                print(f"⚠️  AI classification failed for {thread['thread_id']}: {e}")
                print("   Using keyword-based classification")
                return 'requirement' if self.is_requirement_thread_keyword(thread) else 'general'
        else:
            return 'requirement' if self.is_requirement_thread_keyword(thread) else 'general'
    
    def extract_requirements(self, thread: Dict) -> List[Dict]:
        """Extract requirements from thread"""
        if self.use_ai:
            try:
                return self.ai_processor.extract_requirements(thread)
            except Exception as e:
                print(f"⚠️  AI extraction failed: {e}")
                return self._extract_requirements_basic(thread)
        else:
            return self._extract_requirements_basic(thread)
    
    def _extract_requirements_basic(self, thread: Dict) -> List[str]:
        """Basic requirement extraction without AI"""
        requirements = []
        
        for email in thread['emails']:
            body = email.get('body', '')
            
            if any(keyword in body.lower() for keyword in ['need', 'require', 'should', 'must']):
                requirements.append({
                    'text': body,
                    'from': email.get('from'),
                    'date': email.get('date'),
                    'extraction_method': 'keyword'
                })
        
        return requirements
    
    def store_requirement_thread(self, thread: Dict):
        """Store requirement thread in MongoDB"""
        category = self.classify_thread(thread)
        
        if category != 'requirement':
            print(f"⏭️  Skipping {thread['thread_id']} - classified as {category}")
            return False
        
        # Extract requirements
        requirements = self.extract_requirements(thread)
        
        # Prepare document
        document = {
            'thread_id': thread['thread_id'],
            'category': 'requirement',
            'emails': thread['emails'],
            'email_count': len(thread['emails']),
            'requirements': requirements,
            'metadata': {
                'client': thread['emails'][0].get('from') if thread['emails'] else None,
                'subject': thread['emails'][0].get('subject') if thread['emails'] else None,
                'first_date': thread['emails'][0].get('date') if thread['emails'] else None,
                'last_date': thread['emails'][-1].get('date') if thread['emails'] else None,
            },
            'created_at': datetime.now(),
            'classification_method': 'AI' if self.use_ai else 'keyword'
        }
        
        # Store in MongoDB
        result = self.requirements_collection.update_one(
            {'thread_id': thread['thread_id']},
            {'$set': document},
            upsert=True
        )
        
        if result.upserted_id:
            print(f"✅ STORED: {thread['thread_id']} - {len(requirements)} requirements extracted")
        else:
            print(f"🔄 UPDATED: {thread['thread_id']}")
        
        return True
    
    def process_all_requirements(self, file_path: str):
        """Process all conversations and store only requirements"""
        print("="*60)
        print("🤖 REQUIREMENT AGENT STARTED")
        print("="*60)
        print(f"📁 Reading conversations from: {file_path}")
        
        threads = self.parse_email_file(file_path)
        print(f"📊 Found {len(threads)} total threads\n")
        
        requirement_count = 0
        
        for i, thread in enumerate(threads, 1):
            print(f"\n[{i}/{len(threads)}] Processing {thread['thread_id']}...")
            
            if self.store_requirement_thread(thread):
                requirement_count += 1
        
        print("\n" + "="*60)
        print("✅ PROCESSING COMPLETE")
        print("="*60)
        print(f"📊 Total threads processed: {len(threads)}")
        print(f"✅ Requirement threads stored: {requirement_count}")
        print(f"⏭️  Non-requirement threads skipped: {len(threads) - requirement_count}")
        print(f"💾 MongoDB Collection: {self.requirements_collection.name}")
        print("="*60)
    
    def get_all_requirements(self):
        """Retrieve all stored requirement threads"""
        return list(self.requirements_collection.find())
    
    def get_requirements_summary(self):
        """Get summary of stored requirements"""
        total = self.requirements_collection.count_documents({})
        
        print("\n" + "="*60)
        print("📋 REQUIREMENTS SUMMARY")
        print("="*60)
        print(f"Total requirement threads: {total}\n")
        
        if total > 0:
            requirements = self.get_all_requirements()
            
            for req in requirements:
                print(f"🔹 {req['thread_id']}")
                print(f"   Subject: {req['metadata']['subject']}")
                print(f"   Client: {req['metadata']['client']}")
                print(f"   Emails: {req['email_count']}")
                print(f"   Requirements: {len(req.get('requirements', []))}")
                print(f"   Method: {req.get('classification_method', 'N/A')}")
                print()
        
        print("="*60)
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()
