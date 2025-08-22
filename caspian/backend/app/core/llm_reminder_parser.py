from datetime import datetime, timedelta
import json
import re
from typing import Tuple, Dict, Any, Optional, Union
import asyncio
from dateutil import parser as date_parser

from app.core.nl_reminder_parser import NaturalLanguageReminderParser
from app.core.llm import ask_llm
from app.core.time_utils import get_current_time, format_time, parse_time
from zoneinfo import ZoneInfo

class LLMEnhancedReminderParser:
    """
    A class that combines rule-based parsing with LLM assistance
    for more accurate natural language reminder processing.
    """
    
    def __init__(self, timezone="Asia/Kolkata"):
        self.timezone = timezone
        self.time_zone = ZoneInfo(timezone)
        self.rule_parser = NaturalLanguageReminderParser(timezone=timezone)
    
    async def parse(self, message_text: str) -> Tuple[str, datetime, Optional[str], Optional[Dict[str, Any]]]:
        """
        Parse a natural language message for reminder details using both 
        rule-based parsing and LLM assistance when needed.
        
        Returns a tuple of (content, remind_at, recurrence, recurrence_rule).
        """
        # First try rule-based parsing
        try:
            content, remind_at, recurrence, recurrence_rule = self.rule_parser.parse(message_text)
            
            # If we have clear results, use them
            if content and remind_at and len(content) > 2:
                # Check if this seems like a high-confidence parse
                if self._is_high_confidence_parse(content, message_text):
                    return content, remind_at, recurrence, recurrence_rule
        except Exception as e:
            print(f"Rule-based parser error: {e}")
            # Continue to LLM parsing
        
        # Fall back to LLM parsing for ambiguous or complex cases
        return await self._parse_with_llm(message_text)
    
    def _is_high_confidence_parse(self, content: str, message_text: str) -> bool:
        """
        Determine if the rule-based parse is high confidence.
        """
        # If content is very short or very long relative to the message, it might be inaccurate
        message_words = len(message_text.split())
        content_words = len(content.split())
        
        # If content is less than 20% or more than 80% of the message, it might be inaccurate
        ratio = content_words / message_words if message_words > 0 else 0
        if ratio < 0.2 or ratio > 0.8:
            return False
        
        # If content seems to contain time references, it might be inaccurate
        time_phrases = [
            "today", "tomorrow", "next week", "next month",
            "hour", "minute", "morning", "evening", "afternoon", 
            "night", "tonight", "am", "pm", "at", "on"
        ]
        if any(phrase in content.lower() for phrase in time_phrases):
            return False
        
        return True
    
    async def _parse_with_llm(self, message_text: str) -> Tuple[str, datetime, Optional[str], Optional[Dict[str, Any]]]:
        """
        Use LLM to parse the reminder details from the message.
        """
        # Get synchronized current time
        now_ist = get_current_time(self.timezone)
        now_ist_str = format_time(now_ist)
        
        prompt = f"""
        Parse this natural language reminder request. The current time is: {now_ist_str}.
        
        User request: "{message_text}"
        
        Extract the following information:
        1. What is the specific task or reminder content?
        2. When should the reminder be sent (exact date and time)?
        3. Is there any recurrence pattern (daily, weekly, monthly, etc.)?
        
        Important date handling rules:
        - If a time is mentioned without a date (e.g., "3pm"), and it's already past that time today, assume TOMORROW.
        - "Midnight" always means 00:00 of the NEXT day (so "midnight tonight" = 00:00 tomorrow).
        - If a date appears to be in the past and wasn't explicitly mentioned as past, assume the future date.
        - For month names without a year, if that month has already passed this year, assume NEXT YEAR.
        - For days of the week, if that day has already passed this week, assume NEXT WEEK.
        - For short duration reminders like "in 10 seconds" or "in 2 minutes", calculate the exact time from now.
        
        Return a JSON object with these keys:
        - "remind_at": The exact date and time for the reminder in YYYY-MM-DD HH:MM:SS format ({self.timezone} timezone)
        - "content": The reminder text/task description
        - "recurrence": The recurrence pattern (daily, weekly, monthly, none)
        - "recurrence_rule": Additional recurrence details (null if not applicable)
        
        Return only valid JSON that can be parsed by Python's json.loads().
        """
        
        messages_for_llm = [{"role": "user", "content": prompt}]
        response_text = await ask_llm(messages_for_llm)
        
        # Extract JSON from response (handle different output formats)
        json_match = re.search(r'({.*})', response_text.replace('\n', ' '), re.DOTALL)
        if json_match:
            json_response_str = json_match.group(1)
        else:
            json_response_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
        
        # Clean up the JSON string for more robust parsing
        json_response_str = json_response_str.replace("'", '"')
        
        try:
            reminder_data = json.loads(json_response_str)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}\nResponse text: {response_text}")
            # Fall back to rule-based parsing as last resort
            return self.rule_parser.parse(message_text)
        
        remind_at_str = reminder_data.get("remind_at")
        content = reminder_data.get("content")
        recurrence = reminder_data.get("recurrence", "none")
        recurrence_rule = reminder_data.get("recurrence_rule")
        
        if not remind_at_str or not content:
            # Fall back to rule-based parsing if LLM didn't extract both pieces
            return self.rule_parser.parse(message_text)
        
        # Parse the datetime
        try:
            # Use our enhanced time parsing utility with better disambiguation
            remind_at = parse_time(remind_at_str, default_time=now_ist, timezone=self.timezone)
            
            # Final validation to ensure the time is in the future
            if remind_at < now_ist and not message_text.lower().startswith(("when did", "when was")):
                # Get the most likely future date based on the pattern
                from dateutil.relativedelta import relativedelta
                
                # If time is same day but earlier, shift to tomorrow
                if remind_at.date() == now_ist.date():
                    remind_at += timedelta(days=1)
                # If it's the same day of month but earlier month, shift to next month
                elif remind_at.day == now_ist.day and (remind_at.month < now_ist.month or 
                                                     (remind_at.month == now_ist.month and remind_at.year < now_ist.year)):
                    remind_at += relativedelta(months=1)
                # If it's just earlier in general, shift to next year
                elif remind_at < now_ist:
                    remind_at += relativedelta(years=1)
        except ValueError:
            # Fall back to rule-based parser's time extraction
            _, remind_at, _, _ = self.rule_parser.parse(message_text)
        
        # If recurrence is not "none", but is empty or null, set it to None
        if recurrence in ["none", "", "null", None]:
            recurrence = None
        
        return content, remind_at, recurrence, recurrence_rule

    async def validate_and_refine(self, content: str, remind_at: datetime, 
                                 message_text: str) -> Tuple[str, datetime]:
        """
        Use LLM to validate and refine the parsed reminder details.
        Particularly useful for ambiguous cases or when the rule-based parser
        produces low-confidence results.
        """
        remind_at_str = remind_at.strftime('%Y-%m-%d %H:%M:%S')
        
        prompt = f"""
        Validate and refine these reminder details extracted from a natural language request.
        
        Original request: "{message_text}"
        
        Extracted reminder details:
        - Task/Content: {content}
        - Time: {remind_at_str}
        
        Are these details correct? If not, provide the correct details in this JSON format:
        {{
            "content": "The correct task description",
            "remind_at": "YYYY-MM-DD HH:MM:SS"
        }}
        
        If the details are correct, respond with:
        {{
            "content": "{content}",
            "remind_at": "{remind_at_str}"
        }}
        
        Return only valid JSON that can be parsed by Python's json.loads().
        """
        
        messages_for_llm = [{"role": "user", "content": prompt}]
        response_text = await ask_llm(messages_for_llm)
        
        # Extract JSON from response
        json_match = re.search(r'({.*})', response_text.replace('\n', ' '), re.DOTALL)
        if json_match:
            json_response_str = json_match.group(1)
        else:
            json_response_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
        
        # Clean up the JSON string
        json_response_str = json_response_str.replace("'", '"')
        
        try:
            refined_data = json.loads(json_response_str)
            refined_content = refined_data.get("content", content)
            refined_remind_at_str = refined_data.get("remind_at", remind_at_str)
            
            # Parse the refined datetime
            try:
                refined_remind_at = datetime.strptime(refined_remind_at_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=self.time_zone)
            except ValueError:
                # Try alternative date formats
                try:
                    refined_remind_at = date_parser.parse(refined_remind_at_str).replace(tzinfo=self.time_zone)
                except Exception:
                    # Keep the original if parsing fails
                    refined_remind_at = remind_at
            
            return refined_content, refined_remind_at
        except Exception:
            # Return the original values if refinement fails
            return content, remind_at
