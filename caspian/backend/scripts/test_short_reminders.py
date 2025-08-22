"""
Test script to verify short duration reminder parsing.
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add the parent directory to sys.path to allow imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.core.time_utils import get_current_time, parse_time
from app.core.nl_reminder_parser import NaturalLanguageReminderParser
from app.core.llm_reminder_parser import LLMEnhancedReminderParser

async def test_parsing():
    """
    Test different reminder parsing scenarios with short durations.
    """
    timezone = "Asia/Kolkata"  # Or use your preferred timezone
    nl_parser = NaturalLanguageReminderParser(timezone=timezone)
    llm_parser = LLMEnhancedReminderParser(timezone=timezone)
    
    # Test cases
    test_cases = [
        "remind me to take a nap in 10 seconds",
        "remind me to call John in 30 seconds",
        "remind me to check email in 1 minute",
        "remind me to stretch in 5 minutes",
        "remind me to drink water in 1 hour",
        "remind me to go for a walk tomorrow",
    ]
    
    # Test time_utils.parse_time function
    print("Testing time_utils.parse_time:")
    for test_case in test_cases:
        now = get_current_time(timezone)
        parsed_time = parse_time(test_case, default_time=now, timezone=timezone)
        delta = parsed_time - now
        print(f"Input: '{test_case}'")
        print(f"  Parsed time: {parsed_time}")
        print(f"  Time delta: {delta}")
        print()
    
    # Test NaturalLanguageReminderParser
    print("\nTesting NaturalLanguageReminderParser:")
    for test_case in test_cases:
        content, remind_at, recurrence, recurrence_rule = nl_parser.parse(test_case)
        now = get_current_time(timezone)
        delta = remind_at - now
        print(f"Input: '{test_case}'")
        print(f"  Content: '{content}'")
        print(f"  Remind at: {remind_at}")
        print(f"  Time delta: {delta}")
        print(f"  Recurrence: {recurrence}")
        print()
    
    # Test LLMEnhancedReminderParser
    print("\nTesting LLMEnhancedReminderParser:")
    for test_case in test_cases:
        content, remind_at, recurrence, recurrence_rule = await llm_parser.parse(test_case)
        now = get_current_time(timezone)
        delta = remind_at - now
        print(f"Input: '{test_case}'")
        print(f"  Content: '{content}'")
        print(f"  Remind at: {remind_at}")
        print(f"  Time delta: {delta}")
        print(f"  Recurrence: {recurrence}")
        print()

if __name__ == "__main__":
    asyncio.run(test_parsing())
