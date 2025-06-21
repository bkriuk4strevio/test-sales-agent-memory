import json
import os
from datetime import datetime
from typing import Dict, List

class StrategyManager:
    def __init__(self):
        self.strategy_file = "conversation_strategies.json"
        self.strategies = self.load_strategies()
        
    def load_strategies(self) -> Dict:
        if os.path.exists(self.strategy_file):
            try:
                with open(self.strategy_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return self.get_default_strategies()
    
    def get_default_strategies(self) -> Dict:
        return {
            "conversation_tactics": {
                "opening_phrases": [
                    "Sure, no problem.",
                    "Happy to help.",
                    "Let me share some details.",
                    "Yes, no problem."
                ],
                "successful_transitions": [
                    "We have many clients in that industry",
                    "We work with established banking partners",
                    "Our team has extensive experience"
                ],
                "response_patterns": {
                    "cost_inquiry": "Sure, no problem. Pricing is customized based on your specific requirements and we provide quotes individually after a free expert consultation. What's your timeline looking like?",
                    "jurisdiction_comparison": "Happy to help. Both have excellent benefits and the best choice depends on your specific business needs. What's your main priority?",
                    "banking_inquiry": "Let me share some details. We work with several banking partners and the best option depends on your industry and home country. Would you like to discuss this in detail?",
                    "urgency_response": "Yes, no problem. We can definitely help with urgent setups and usually complete incorporations around one week. Our team would be happy to provide more information if needed."
                },
                "proven_questions": [
                    "What's your main priority for the setup?",
                    "What industry are you in?",
                    "What's driving your decision to expand there?"
                ],
                "consultation_triggers": [
                    "I will put you in touch with one of our experts. Please, choose your preferred time in the calendar CALENDLY_LINK or via email EMAIL to discuss the details."
                ],
            },
            "timing_strategy": {
                "link_timing": 4,
                "urgency_triggers": ["urgent", "asap", "quickly", "timeline", "when", "fast", "immediate"],
                "early_link_scenarios": ["detailed_cost_question", "specific_timeline", "multiple_jurisdictions", "banking_requirements"],
                "engagement_signals": ["long_responses", "multiple_questions", "industry_specific"]
            },
            "learned_patterns": {
                "successful_conversations": [],
                "failed_conversations": [],
                "successful_phrases": [],
                "high_conversion_topics": []
            },
            "success_metrics": {
                "link_shared": 0,
                "consultations_requested": 0,
                "conversations_completed": 0,
                "conversion_rate": 0.0
            }
        }
    
    def analyze_conversation_success(self, messages: List[Dict], link_shared: bool, consultation_requested: bool):
        """Analyze conversation and learn from it"""
        # Extract conversation patterns
        conversation_analysis = {
            "timestamp": datetime.now().isoformat(),
            "message_count": len([m for m in messages if m["role"] == "user"]),
            "link_shared": link_shared,
            "consultation_requested": consultation_requested,
            "user_engagement": self.calculate_engagement(messages),
            "topics_discussed": self.extract_topics(messages),
            "successful_phrases": self.extract_phrases(messages, link_shared),
            "conversation_flow": self.analyze_flow(messages),
            "user_response_style": self.analyze_user_style(messages)
        }
        
        # Learn from conversations
        if link_shared:
            self.strategies['learned_patterns']['successful_conversations'].append(conversation_analysis)
            
            # Add successful phrases to strategy
            for phrase in conversation_analysis['successful_phrases']:
                if phrase not in self.strategies['learned_patterns']['successful_phrases']:
                    self.strategies['learned_patterns']['successful_phrases'].append(phrase)
            
            # Track high conversion topics
            for topic in conversation_analysis['topics_discussed']:
                if topic not in self.strategies['learned_patterns']['high_conversion_topics']:
                    self.strategies['learned_patterns']['high_conversion_topics'].append(topic)
            
            # Update response patterns based on what worked
            self.update_response_patterns(conversation_analysis)
        else:
            self.strategies['learned_patterns']['failed_conversations'].append(conversation_analysis)
        
        # Update metrics
        self.update_metrics(link_shared, consultation_requested)
        
        # Optimize strategy
        self.optimize_strategy()
        
        # Save locally
        self.save_strategies()
        return True
    
    def extract_topics(self, messages: List[Dict]) -> List[str]:
        topics = set()
        for msg in messages:
            content = msg["content"].lower()
            if "singapore" in content: topics.add("singapore")
            if "hong kong" in content or "hk" in content: topics.add("hong_kong")
            if "usa" in content or "america" in content or "florida" in content or "new mexico" in content: topics.add("usa")
            if "uk" in content or "britain" in content: topics.add("uk")
            if "malaysia" in content: topics.add("malaysia")
            if "thailand" in content: topics.add("thailand")
            if "cost" in content or "price" in content: topics.add("pricing")
            if "timeline" in content or "urgent" in content: topics.add("urgency")
            if "bank" in content: topics.add("banking")
            if "tax" in content: topics.add("taxation")
        return list(topics)
    
    def extract_phrases(self, messages: List[Dict], was_successful: bool) -> List[str]:
        if not was_successful:
            return []
        
        phrases = []
        for msg in messages:
            if msg["role"] == "assistant":
                content = msg["content"]
                # Extract opening phrases that worked
                sentences = content.split('. ')
                for sentence in sentences:
                    if any(start in sentence for start in ["Sure", "Yes", "Happy to help", "Let me share", "No problem"]):
                        phrase = sentence.strip().split('.')[0][:50]
                        if phrase:
                            phrases.append(phrase)
        return phrases
    
    def analyze_flow(self, messages: List[Dict]) -> List[str]:
        flow = []
        for msg in messages:
            if msg["role"] == "assistant":
                content = msg["content"].lower()
                if "?" in content: flow.append("question_asked")
                if "calendly" in content or "email" in content: flow.append("consultation_offered")
                if "banking" in content or "payment" in content: flow.append("banking_discussed")
                if "tax" in content: flow.append("taxation_discussed")
                if "timeline" in content or "week" in content: flow.append("timeline_discussed")
        return flow
    
    def analyze_user_style(self, messages: List[Dict]) -> str:
        user_messages = [m for m in messages if m["role"] == "user"]
        if not user_messages:
            return "unknown"
        
        avg_length = sum(len(m["content"].split()) for m in user_messages) / len(user_messages)
        question_count = sum(1 for m in user_messages if "?" in m["content"])
        
        if avg_length < 5:
            return "brief"
        elif avg_length > 20:
            return "detailed"
        elif question_count > 2:
            return "inquisitive"
        else:
            return "standard"
    
    def update_response_patterns(self, analysis: Dict):
        topics = analysis.get('topics_discussed', [])
        successful_phrases = analysis.get('successful_phrases', [])
        
        if successful_phrases and topics:
            best_phrase = successful_phrases[0] if successful_phrases else "Happy to help"
            
            # Update patterns based on successful topics
            if 'pricing' in topics:
                self.strategies['conversation_tactics']['response_patterns']['cost_inquiry'] = f"{best_phrase}. Pricing is customized based on your specific requirements and we provide quotes individually after a free expert consultation. What's your timeline looking like?"
            
            if 'banking' in topics:
                self.strategies['conversation_tactics']['response_patterns']['banking_inquiry'] = f"{best_phrase}. We work with several banking partners and the best option depends on your industry and home country. Would you like to discuss this in detail?"
    
    def calculate_engagement(self, messages: List[Dict]) -> float:
        user_messages = [m for m in messages if m["role"] == "user"]
        if not user_messages:
            return 0.0
        
        avg_length = sum(len(m["content"].split()) for m in user_messages) / len(user_messages)
        return min(avg_length / 15, 1.0)
    
    def update_metrics(self, link_shared: bool, consultation_requested: bool):
        self.strategies["success_metrics"]["conversations_completed"] += 1
        if link_shared:
            self.strategies["success_metrics"]["link_shared"] += 1
        if consultation_requested:
            self.strategies["success_metrics"]["consultations_requested"] += 1
        
        # Calculate conversion rate
        total_conversations = self.strategies["success_metrics"]["conversations_completed"]
        if total_conversations > 0:
            self.strategies["success_metrics"]["conversion_rate"] = (
                self.strategies["success_metrics"]["link_shared"] / total_conversations
            ) * 100
    
    def optimize_strategy(self):
        successful_conversations = self.strategies['learned_patterns']['successful_conversations']
        
        if len(successful_conversations) < 3:
            return
        
        # Optimize timing based on successful conversations
        recent_successes = successful_conversations[-10:]
        if recent_successes:
            avg_timing = sum(conv['message_count'] for conv in recent_successes) / len(recent_successes)
            new_timing = max(3, min(6, int(avg_timing)))
            self.strategies['timing_strategy']['link_timing'] = new_timing
        
        # Update successful transitions based on high conversion topics
        if self.strategies['learned_patterns']['high_conversion_topics']:
            for topic in self.strategies['learned_patterns']['high_conversion_topics'][-5:]:
                if topic == 'banking':
                    transition = "We have established relationships with banking institutions"
                    if transition not in self.strategies['conversation_tactics']['successful_transitions']:
                        self.strategies['conversation_tactics']['successful_transitions'].append(transition)
    
    def get_current_strategy(self) -> Dict:
        return self.strategies
    
    def save_strategies(self):
        try:
            with open(self.strategy_file, 'w') as f:
                json.dump(self.strategies, f, indent=2)
            return True
        except Exception:
            return False
