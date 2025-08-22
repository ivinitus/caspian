import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo
from app.core.time_utils import get_current_time, format_time, parse_time

class NaturalLanguageReminderParser:
    """
    A class to parse natural language for reminder details.
    This is used to extract reminder information from user messages.
    """
    
    def __init__(self, timezone="Asia/Kolkata"):
        self.timezone = timezone
        self.time_zone = ZoneInfo(timezone)
        
        # Common time keywords and patterns
        self.time_patterns = {
            "today": self._today,
            "tomorrow": self._tomorrow,
            "in an hour": self._in_hours(1),
            "in a minute": self._in_minutes(1),
            "in a second": self._in_seconds(1),
            "tonight": self._tonight,
            "this evening": self._evening,
            "this morning": self._morning,
            "this afternoon": self._afternoon,
            "next week": self._next_week,
            "next month": self._next_month,
            "next year": self._next_year,
        }
        
        # Day of week patterns (e.g., "on Monday")
        self.weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }
        
        # Month patterns (e.g., "in January")
        self.months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        # Recurrence patterns
        self.recurrence_patterns = {
            "daily": "daily",
            "every day": "daily",
            "each day": "daily",
            "weekly": "weekly", 
            "every week": "weekly",
            "each week": "weekly",
            "monthly": "monthly",
            "every month": "monthly",
            "each month": "monthly",
            "yearly": "yearly",
            "every year": "yearly",
            "each year": "yearly",
            "weekday": {"type": "weekday"},
            "weekdays": {"type": "weekday"},
            "every weekday": {"type": "weekday"},
            "weekend": {"type": "weekend"},
            "weekends": {"type": "weekend"},
            "every weekend": {"type": "weekend"}
        }
    
    def _now(self):
        """Get current time in the specified timezone using synchronized time"""
        return get_current_time(self.timezone)
    
    def _today(self):
        """Get today with default time (8 AM)"""
        now = self._now()
        return now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    def _tomorrow(self):
        """Get tomorrow with default time (8 AM)"""
        return self._today() + timedelta(days=1)
    
    def _in_hours(self, hours):
        """Get time N hours from now"""
        def _time():
            return self._now() + timedelta(hours=hours)
        return _time
    
    def _in_minutes(self, minutes):
        """Get time N minutes from now"""
        def _time():
            return self._now() + timedelta(minutes=minutes)
        return _time
    
    def _in_seconds(self, seconds):
        """Get time N seconds from now"""
        def _time():
            return self._now() + timedelta(seconds=seconds)
        return _time
    
    def _tonight(self):
        """Get tonight (8 PM today)"""
        now = self._now()
        return now.replace(hour=20, minute=0, second=0, microsecond=0)
    
    def _evening(self):
        """Get this evening (6 PM today)"""
        now = self._now()
        return now.replace(hour=18, minute=0, second=0, microsecond=0)
    
    def _morning(self):
        """Get this morning (8 AM today)"""
        now = self._now()
        if now.hour >= 12:  # If it's already past noon, use tomorrow morning
            return now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    def _afternoon(self):
        """Get this afternoon (2 PM today)"""
        now = self._now()
        if now.hour >= 14:  # If it's already past 2 PM, use tomorrow afternoon
            return now.replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return now.replace(hour=14, minute=0, second=0, microsecond=0)
    
    def _next_week(self):
        """Get the same day next week"""
        return self._now() + timedelta(days=7)
    
    def _next_month(self):
        """Get the same day next month"""
        return self._now() + relativedelta(months=1)
    
    def _next_year(self):
        """Get the same day next year"""
        return self._now() + relativedelta(years=1)
    
    def extract_content(self, message):
        """
        Extract the reminder content from the message.
        """
        # Try to find the content based on reminder keywords
        reminder_keywords = [
            "remind me to", "remind me about", "reminder for", 
            "remind me", "set a reminder to", "create a reminder to",
            "don't forget to", "make sure to"
        ]
        
        # Extract content based on reminder keywords
        for keyword in reminder_keywords:
            if keyword in message.lower():
                content = message[message.lower().find(keyword) + len(keyword):].strip()
                # Try to find time indicators to remove them from content
                time_indicators = [" at ", " on ", " by ", " in ", " today", " tomorrow", " tonight"]
                for indicator in time_indicators:
                    if indicator in content.lower():
                        content = content[:content.lower().find(indicator)].strip()
                return content
        
        # Fallback: just return the message without time-related words
        # Remove common time-related phrases
        time_phrases = [
            "today", "tomorrow", "next week", "next month",
            "in an hour", "in a minute", "in a day",
            "at", "on", "this evening", "this morning",
            "this afternoon", "tonight", "am", "pm",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "january", "february", "march", "april", "may", "june", "july", 
            "august", "september", "october", "november", "december"
        ]
        
        # Create a copy of the message to modify
        content = message
        
        # Remove time-related words/phrases
        for phrase in time_phrases:
            pattern = r'\b' + re.escape(phrase) + r'\b'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Remove numbers and time patterns
        content = re.sub(r'\b\d+:\d+\b', '', content)  # Remove times like "3:30"
        content = re.sub(r'\b\d+(st|nd|rd|th)\b', '', content)  # Remove "1st", "2nd", etc.
        content = re.sub(r'\b\d+\s*(am|pm)\b', '', content, flags=re.IGNORECASE)  # Remove "3 pm", etc.
        
        # Clean up extra spaces and punctuation
        content = re.sub(r'\s+', ' ', content).strip()
        content = re.sub(r'^[,:;.\s]+', '', content).strip()  # Remove leading punctuation
        
        return content
    
    def extract_time(self, message):
        """
        Extract the reminder time from the message.
        Returns a datetime object or None if no time could be extracted.
        """
        message_lower = message.lower()
        
        # Try explicit time patterns first
        for pattern, time_func in self.time_patterns.items():
            if pattern in message_lower:
                return time_func()
        
        # Check for patterns like "in X seconds/minutes/hours/days"
        seconds_match = re.search(r'in\s+(\d+)\s+seconds?', message_lower)
        if seconds_match:
            seconds = int(seconds_match.group(1))
            now = self._now()
            return now + timedelta(seconds=seconds)
            
        minutes_match = re.search(r'in\s+(\d+)\s+minutes?', message_lower)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            now = self._now()
            return now + timedelta(minutes=minutes)
            
        hours_match = re.search(r'in\s+(\d+)\s+hours?', message_lower)
        if hours_match:
            hours = int(hours_match.group(1))
            now = self._now()
            return now + timedelta(hours=hours)
            
        days_match = re.search(r'in\s+(\d+)\s+days?', message_lower)
        if days_match:
            days = int(days_match.group(1))
            now = self._now()
            return now + timedelta(days=days)
        
        # Try to find times like "3:30 pm" or "15:30"
        time_matches = re.findall(r'(\d{1,2}):(\d{2})(?:\s*(am|pm))?', message_lower)
        if time_matches:
            hour, minute, ampm = time_matches[0]
            hour = int(hour)
            minute = int(minute)
            if ampm and ampm.lower() == 'pm' and hour < 12:
                hour += 12
            elif ampm and ampm.lower() == 'am' and hour == 12:
                hour = 0
                
            now = self._now()
            reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the time is in the past, assume it's for tomorrow
            if reminder_time < now:
                reminder_time += timedelta(days=1)
                
            return reminder_time
        
        # Try to find times like "3 pm" or "3pm"
        time_matches = re.findall(r'(\d{1,2})\s*(am|pm)', message_lower)
        if time_matches:
            hour, ampm = time_matches[0]
            hour = int(hour)
            if ampm.lower() == 'pm' and hour < 12:
                hour += 12
            elif ampm.lower() == 'am' and hour == 12:
                hour = 0
                
            now = self._now()
            reminder_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # If the time is in the past, assume it's for tomorrow
            if reminder_time < now:
                reminder_time += timedelta(days=1)
                
            return reminder_time
        
        # Try to find day of week, like "on Monday"
        for day, day_index in self.weekdays.items():
            if f" {day}" in message_lower:
                now = self._now()
                current_day = now.weekday()
                days_until = (day_index - current_day) % 7
                if days_until == 0:  # If it's today, check if we need to use next week
                    if now.hour >= 8:  # If it's already past 8 AM, use next week
                        days_until = 7
                target_date = now + timedelta(days=days_until)
                return target_date.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Try to find months, like "in January"
        for month, month_index in self.months.items():
            if f" {month}" in message_lower:
                now = self._now()
                current_month = now.month
                current_year = now.year
                
                # If the month is earlier in the year than the current month,
                # assume it's for next year
                if month_index < current_month:
                    target_year = current_year + 1
                else:
                    target_year = current_year
                
                # Default to the 1st day of the month at 8 AM
                return datetime(target_year, month_index, 1, 8, 0, 0, tzinfo=self.time_zone)
        
        # Try date parser as a last resort
        try:
            # Look for date-like patterns in the text
            date_matches = re.findall(r'\b\d{1,2}(/|-)\d{1,2}(/|-)\d{2,4}\b', message)
            if date_matches:
                # Parse the first date found
                parsed_date = date_parser.parse(date_matches[0], fuzzy=True)
                # Set a default time if only date was provided
                if parsed_date.hour == 0 and parsed_date.minute == 0:
                    parsed_date = parsed_date.replace(hour=8)
                return parsed_date.replace(tzinfo=self.time_zone)
            
            # Try parsing with dateutil's fuzzy parsing
            return date_parser.parse(message, fuzzy=True).replace(tzinfo=self.time_zone)
        except:
            # If all else fails, default to tomorrow morning
            return self._tomorrow()
    
    def extract_recurrence(self, message):
        """
        Extract the recurrence pattern from the message.
        Returns a string like "daily", "weekly", "monthly", or None.
        """
        message_lower = message.lower()
        
        # Check for recurrence patterns
        for pattern, recurrence in self.recurrence_patterns.items():
            if pattern in message_lower:
                return recurrence
        
        # Check for patterns like "every 2 days" or "every 3 weeks"
        recurrence_match = re.search(r'every\s+(\d+)\s+(day|week|month|year)s?', message_lower)
        if recurrence_match:
            interval = int(recurrence_match.group(1))
            unit = recurrence_match.group(2) + "s"  # Convert to plural for consistency
            return {"type": "custom", "interval": interval, "unit": unit}
        
        return None
    
    def parse(self, message):
        """
        Parse a natural language message for reminder details.
        Returns a tuple of (content, remind_at, recurrence, recurrence_rule).
        """
        content = self.extract_content(message)
        remind_at = self.extract_time(message)
        recurrence_data = self.extract_recurrence(message)
        
        if isinstance(recurrence_data, dict):
            recurrence = "custom"
            recurrence_rule = recurrence_data
        else:
            recurrence = recurrence_data
            recurrence_rule = None
        
        return content, remind_at, recurrence, recurrence_rule
