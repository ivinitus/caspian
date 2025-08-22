"""
Test script for date parsing enhancements
This script tests various date/time inputs to verify our improved parsing logic
"""

import asyncio
from datetime import datetime, timedelta
from app.core.time_utils import get_current_time, parse_time, format_time
from app.core.llm_reminder_parser import LLMEnhancedReminderParser
from dateutil.relativedelta import relativedelta

async def test_date_parsing():
    """Test improved date parsing with various inputs"""
    print("===== Testing Date Parsing =====")
    
    # Get current time for reference
    now = get_current_time("Asia/Kolkata")
    print(f"Current time: {format_time(now)}")
    print("\nTesting time edge cases:")
    
    # Test cases
    test_cases = [
        "12:00 AM",          # Midnight - should be next day
        "today at 3pm",      # Today at specific time - past time should be tomorrow
        "thursday 5pm",      # Day of week - if passed should be next week
        "friday midnight",   # Midnight on a specific day
        "august 21",         # Current date - should be next year if already passed today
        "august 21 midnight" # Current date with midnight - should be early morning tomorrow
    ]
    
    for test_input in test_cases:
        try:
            # Parse using our improved parser
            result = parse_time(test_input, default_time=now)
            
            # Check if the result is in the future
            is_future = result > now
            
            print(f"\nInput: '{test_input}'")
            print(f"Parsed: {format_time(result)}")
            print(f"Is future: {is_future}")
            print(f"Days from now: {(result - now).total_seconds() / 86400:.1f} days")
            
        except Exception as e:
            print(f"Error parsing '{test_input}': {e}")
    
    print("\n===== Testing LLM Parser =====")
    # Create the enhanced parser
    parser = LLMEnhancedReminderParser()
    
    # Test LLM parsing with problematic cases
    llm_test_cases = [
        "remind me at midnight",
        "remind me on Thursday at noon",
        "set a reminder for August 21 at midnight"
    ]
    
    for test_input in llm_test_cases:
        try:
            content, remind_at, recurrence, _ = await parser.parse(test_input)
            
            # Check if the result is in the future
            is_future = remind_at > now
            
            print(f"\nInput: '{test_input}'")
            print(f"Content: {content}")
            print(f"Remind at: {format_time(remind_at)}")
            print(f"Is future: {is_future}")
            print(f"Days from now: {(remind_at - now).total_seconds() / 86400:.1f} days")
            
        except Exception as e:
            print(f"Error with LLM parsing '{test_input}': {e}")

if __name__ == "__main__":
    asyncio.run(test_date_parsing())
