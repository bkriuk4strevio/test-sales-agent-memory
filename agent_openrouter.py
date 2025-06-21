import openai
from typing import List, Dict
import json
import os
import streamlit as st
import random

class OpenRouterSalesAgent:
    def __init__(self):
        # Get API key from Streamlit secrets or environment variables
        try:
            api_key = st.secrets["OPENROUTER_API_KEY"]
        except:
            api_key = os.environ.get("OPENROUTER_API_KEY")
        
        if not api_key:
            raise ValueError("OpenRouter API key not found. Please set it in Streamlit secrets or environment variables.")
        
        # Initialize OpenRouter client
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        # Initialize memory
        self.conversation_history = []
        self.max_history = 20
        
        # Knowledge base
        self.knowledge = self.load_simple_knowledge()
        
        # Strategy context
        self.current_strategy = None
        
        # Base system prompt
        self.base_system_prompt = """You are a professional corporate services consultant [choose one of the English names] from Strasia Group specializing in company incorporation and secretarial services across Hong Kong, Singapore, Malaysia, Thailand, UK, and USA.

GUIDELINES:
- Be direct and professional, not overly enthusiastic
- Introduce yourself once in the first message to the user [choose one of the English names] and ask something like this (please stay generalized and you can change it according to first input): May I know what services you are looking for? Stay generalized let user ask about your services.
- Don't use "I", use "We"
- Don't describe Strasia Group Services at all unless you are asked
- Stay very abstract and general, name only benefits and positive features when asked, e.g. If asked if Singapore jurisdiction is better than Hong Kong, name only benefits of both. Benefits of Hong Kong include taxation benefits and international financial center status (avoid mentioning Chinese market access unless specifically asked about China).
- Your answers should imply more questions when answered like for a professional sales guy
- Don't start with "I specialize"
- Don't ask for details like: "Are you looking for monthly or yearly accounting services?" Because it should be asked and upselled in the online meeting
- Keep responses to 2-3 sentences maximum
- Ask one specific question to understand their needs
- Guide toward scheduling a consultation within 4-5 exchanges
- Use knowledge when relevant but don't overwhelm
- Ask clarifications to be completely aligned, e.g. "What trading you mean when you say about your business niche?"
- Avoid phrases like "Great question!" or "I'd be happy to help"
- Avoid saying directly that we monitor conversation number like never say "since this is your 4th exchange" or so
- Always add in every message beginning small details humans add like "sure dont worry" before actually explaining why not to worry or "yes no problem" "Let me share some details" "Happy to help" before explaining why its no problem add this or similar everyday wording
- You MUST output just the response to the message, nothing else
- Add some wording that confirms that the lead has found the right partner (we have many clients doing [name of industry]; we have established relationships with banking institutions; we work with various payment processors including established partners).
- Always mention our personal relationships with banking and payment processing partners when relevant: at banking institutions like Airwallex, Aspire, HSBC; we know people at payment processors like Airwallex, Oceanpayment and PayPal.
- You must call a lead for a booking/consultation at 4-5th message if not yet shared in message for example with (try to stay general and easy going, you may change it according to the need): "I will put you in touch with one of our experts. Please, choose your preferred time in the calendar CALENDLY_LINK or via email EMAIL to discuss the details."
- If they want booking/consultation, immediately provide something like (change it): "I will put you in touch with one of our consultants. Please, choose your preferred time in the calendar CALENDLY_LINK or via email EMAIL to discuss the details."
- If you provide details and does not end the message with a call proposal, it should say something like "I hope this answers your question(s)" "I hope this provides some clarity" "Our team would be happy to provide more information if needed"
- Always check if it's the time to send (change it) "I will put you in touch with one of our consultants/experts. Please, choose your preferred time in the calendar CALENDLY_LINK or via email EMAIL to discuss the details." or not yet
- NEVER provide specific pricing, costs, or numerical quotes - always say pricing is customized and we provide quotes individually after a free expert consultation
- For incorporation timelines, say "usually around one week" instead of specific days like "1-2 days"
- For US incorporation, recommend Florida and New Mexico instead of Delaware or Wyoming due to banking advantages
- For US banking, say "we work with several banking partners in USA" without specific names, and if asked which ones, say "it depends on industry and home country of owner" and guide them to consultation
- Never mention clients and services in sanctioned countries like Myanmar
- Always mention Hong Kong's 8.25% tax rate (for first HK$2M) when discussing Hong Kong taxation
- Reject any requests that could support illegal activities immediately
- Never recommend Wyoming or Delaware but Florida and New Mexico instead
- Include all major jurisdictions (USA, UK, not just Singapore and Hong Kong) in recommendations not just HK and Singapore

CONVERSATION GOAL: Get them to ask for contact information or schedule a consultation."""

    def set_strategy_context(self, strategy: Dict):
        """Apply learned strategy to agent behavior"""
        self.current_strategy = strategy
        if not strategy:
            return
        
        # Add learned tactics to system prompt
        tactics = strategy.get('conversation_tactics', {})
        timing = strategy.get('timing_strategy', {})
        
        strategy_additions = "\n\nLEARNED STRATEGY:\n"
        
        # Add successful opening phrases
        opening_phrases = tactics.get('opening_phrases', [])
        if opening_phrases:
            strategy_additions += f"- Use these proven opening phrases: {', '.join(opening_phrases[:3])}\n"
        
        # Add successful transitions
        transitions = tactics.get('successful_transitions', [])
        if transitions:
            strategy_additions += f"- Use these successful transitions: {', '.join(transitions[:3])}\n"
        
        # Add proven questions
        questions = tactics.get('proven_questions', [])
        if questions:
            strategy_additions += f"- Ask these effective questions: {', '.join(questions[:3])}\n"
        
        # Add timing strategy
        link_timing = timing.get('link_timing', 4)
        strategy_additions += f"- Offer consultation link around message {link_timing}\n"
        
        # Add consultation triggers
        consultation_triggers = tactics.get('consultation_triggers', [])
        if consultation_triggers:
            strategy_additions += f"- Use these consultation phrases: {consultation_triggers[0]}\n"
        
        self.system_prompt = self.base_system_prompt + strategy_additions

    def get_learned_response_pattern(self, user_message: str) -> str:
        """Get learned response pattern for specific scenarios"""
        if not self.current_strategy:
            return None
        
        response_patterns = self.current_strategy.get('conversation_tactics', {}).get('response_patterns', {})
        message_lower = user_message.lower()
        
        # Check for cost inquiry
        if any(word in message_lower for word in ['cost', 'price', 'how much', 'expensive', 'pricing']):
            return response_patterns.get('cost_inquiry')
        
        # Check for banking inquiry
        if any(word in message_lower for word in ['bank', 'banking', 'account', 'payment']):
            return response_patterns.get('banking_inquiry')
        
        # Check for urgency
        if any(word in message_lower for word in ['urgent', 'asap', 'quickly', 'fast', 'immediate']):
            return response_patterns.get('urgency_response')
        
        return None

    def should_offer_link_early(self, user_message: str, exchange_count: int) -> bool:
        """Check if we should offer link earlier based on learned patterns"""
        if not self.current_strategy:
            return False
        
        timing_strategy = self.current_strategy.get('timing_strategy', {})
        urgency_triggers = timing_strategy.get('urgency_triggers', [])
        early_scenarios = timing_strategy.get('early_link_scenarios', [])
        
        message_lower = user_message.lower()
        
        # Check urgency triggers
        if any(trigger in message_lower for trigger in urgency_triggers):
            return True
        
        # Check early link scenarios
        if 'detailed_cost_question' in early_scenarios and len(user_message.split()) > 15 and any(word in message_lower for word in ['cost', 'price']):
            return True
        
        if 'banking_requirements' in early_scenarios and any(word in message_lower for word in ['bank', 'banking', 'account']):
            return True
        
        if 'multiple_jurisdictions' in early_scenarios and sum(1 for jurisdiction in ['singapore', 'hong kong', 'uk', 'usa', 'florida', 'new mexico'] if jurisdiction in message_lower) > 1:
            return True
        
        return False

    def get_successful_phrase(self) -> str:
        """Get a random successful phrase to start response"""
        if not self.current_strategy:
            return ""
        
        successful_phrases = self.current_strategy.get('learned_patterns', {}).get('successful_phrases', [])
        opening_phrases = self.current_strategy.get('conversation_tactics', {}).get('opening_phrases', [])
        
        all_phrases = successful_phrases + opening_phrases
        if all_phrases:
            return random.choice(all_phrases)
        
        return ""

    def load_simple_knowledge(self):
        """Load simple knowledge base without external dependencies"""
        knowledge_base = {
            "singapore": {
                "incorporation": "Singapore Private Limited Company can be incorporated usually around one week. Minimum 1 director required (can be foreigner). Minimum paid-up capital SGD $1. Corporate secretary mandatory.",
                "taxation": "Corporate tax rate 17%. No capital gains tax. Extensive tax incentives available. Annual filing required.",
                "benefits": "Strategic location, business-friendly environment, strong legal framework, access to ASEAN markets."
            },
            "hong_kong": {
                "incorporation": "Hong Kong Limited Company incorporation takes usually around one week. Minimum 1 director and 1 shareholder. Company secretary required. No minimum capital requirement.",
                "taxation": "Profits tax rate 8.25% for first HK$2M and 16.5% above. No capital gains tax, dividend tax, or withholding tax. Territorial taxation system.",
                "benefits": "International financial center, simple tax system, no foreign exchange controls, strategic Asian hub."
            },
            "uk": {
                "incorporation": "UK Limited Company formation usually around one week. Minimum 1 director and 1 shareholder. Company secretary optional.",
                "taxation": "Corporation tax rate 25% (19% for small companies). VAT registration may be required. Annual confirmation statement required.",
                "benefits": "Access to global markets, strong legal system, established business infrastructure, English-speaking."
            },
            "usa": {
                "incorporation": "US Corporation or LLC formation usually around one week. Requirements vary by state. Florida and New Mexico are popular options. Registered agent required.",
                "taxation": "Federal corporate tax 21% plus state taxes. LLC has pass-through taxation. We work with several banking partners in USA.",
                "benefits": "World's largest economy, access to capital markets, strong IP protection, established business ecosystem."
            },
            "malaysia": {
                "incorporation": "Malaysian Sdn Bhd incorporation takes usually around one week. Minimum 1 director (Malaysian resident required). Company secretary mandatory.",
                "taxation": "Corporate tax rate 24%. MSC status companies get tax incentives. Labuan jurisdiction offers attractive tax rates.",
                "benefits": "ASEAN hub, multicultural workforce, government incentives, strategic location."
            },
            "thailand": {
                "incorporation": "Thai Limited Company registration takes usually around one week. Minimum 3 shareholders. Foreign ownership restrictions apply.",
                "taxation": "Corporate income tax 20%. BOI promoted companies get tax privileges. VAT 7%.",
                "benefits": "Growing economy, ASEAN member, government investment promotion, skilled workforce."
            }
        }
        return knowledge_base

    def get_knowledge(self, message: str) -> str:
        """Get relevant knowledge from simple knowledge base"""
        message_lower = message.lower()
        relevant_info = []
        
        # Check which jurisdictions are mentioned
        jurisdictions_mentioned = []
        for jurisdiction in self.knowledge.keys():
            if jurisdiction.replace("_", " ") in message_lower or jurisdiction in message_lower:
                jurisdictions_mentioned.append(jurisdiction)
        
        # If no specific jurisdiction mentioned, check for general topics
        if not jurisdictions_mentioned:
            if any(word in message_lower for word in ["incorporation", "company", "business", "setup", "formation"]):
                jurisdictions_mentioned = ["singapore", "hong_kong"]
            elif any(word in message_lower for word in ["tax", "taxation", "cost", "rate"]):
                jurisdictions_mentioned = ["singapore", "hong_kong", "uk"]
        
        # Gather relevant information
        for jurisdiction in jurisdictions_mentioned[:2]:
            if jurisdiction in self.knowledge:
                jurisdiction_name = jurisdiction.replace("_", " ").title()
                
                # Determine what type of info to include based on query
                if any(word in message_lower for word in ["cost", "tax", "rate", "price"]):
                    info = f"{jurisdiction_name}: {self.knowledge[jurisdiction]['taxation']}"
                elif any(word in message_lower for word in ["incorporation", "setup", "formation", "company"]):
                    info = f"{jurisdiction_name}: {self.knowledge[jurisdiction]['incorporation']}"
                else:
                    info = f"{jurisdiction_name}: {self.knowledge[jurisdiction]['benefits']}"
                
                relevant_info.append(info)
        
        return " | ".join(relevant_info) if relevant_info else "We can help with company formation across multiple jurisdictions."

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def format_conversation_history(self) -> str:
        """Format conversation history for the prompt"""
        if not self.conversation_history:
            return "This is the start of the conversation."
        
        formatted = []
        for msg in self.conversation_history[-8:]:
            role = "User" if msg['role'] == 'user' else "Consultant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)

    def generate_response(self, user_message: str) -> str:
        """Generate response using OpenRouter with learned strategy"""
        try:
            # Get relevant knowledge
            knowledge = self.get_knowledge(user_message)
            
            # Format conversation history
            conv_history = self.format_conversation_history()
            
            # Count current exchanges
            user_messages = [msg for msg in self.conversation_history if msg['role'] == 'user']
            exchange_count = len(user_messages)
            
            # Check for learned response pattern first
            learned_response = self.get_learned_response_pattern(user_message)
            if learned_response and exchange_count < 4:
                self.add_to_history("user", user_message)
                self.add_to_history("assistant", learned_response)
                return learned_response
            
            # Create the prompt
            prompt = f"""CONVERSATION HISTORY:
{conv_history}

RELEVANT KNOWLEDGE:
{knowledge}

USER: {user_message}

Remember the guidelines and respond as a professional consultant using learned strategies. Current exchange count: {exchange_count + 1}"""

            # Call OpenRouter API
            response = self.client.chat.completions.create(
                model="anthropic/claude-3.5-sonnet",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean response
            if ai_response.startswith("CONSULTANT:"):
                ai_response = ai_response.replace("CONSULTANT:", "").strip()
            
            # Add successful phrase if available and not first message
            if exchange_count > 0:
                successful_phrase = self.get_successful_phrase()
                if successful_phrase and not ai_response.startswith(successful_phrase.split()[0]):
                    if len(successful_phrase.split()) < 6:  # Short phrases only
                        ai_response = f"{successful_phrase} {ai_response}"
            
            # Add to conversation history
            self.add_to_history("user", user_message)
            self.add_to_history("assistant", ai_response)
            
            # Determine link timing based on strategy
            target_timing = 4
            if self.current_strategy:
                target_timing = self.current_strategy.get('timing_strategy', {}).get('link_timing', 4)
            
            # Check for early link offering
            should_offer_early = self.should_offer_link_early(user_message, exchange_count)
            
            # Check if we should suggest contact
            if ((exchange_count >= target_timing or should_offer_early) and 
                "CALENDLY_LINK" not in ai_response and "EMAIL" not in ai_response):
                if any(word in user_message.lower() for word in ["cost", "price", "how much", "timeline", "when", "process", "bank", "banking"]):
                    consultation_trigger = "I will put you in touch with one of our experts. Please, choose your preferred time in the calendar CALENDLY_LINK or via email EMAIL to discuss the details."
                    if self.current_strategy:
                        triggers = self.current_strategy.get('conversation_tactics', {}).get('consultation_triggers', [])
                        if triggers:
                            consultation_trigger = random.choice(triggers)
                    ai_response += f" {consultation_trigger}"
            
            return ai_response
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "We can help with company formation across multiple jurisdictions. Which market are you considering?"

    def clear_memory(self):
        """Clear conversation history"""
        self.conversation_history = []

def create_agent():
    return OpenRouterSalesAgent()
