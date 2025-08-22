import asyncio
import discord
import re
from sqlalchemy import select
from app.core.config import settings
from app.db.models import SessionLocal, User, Conversation, Message, Reminder
from app.rag import rag_system
from datetime import datetime
from app.core.personality import get_chat_prompt
import json
from app.api.auth import get_password_hash
import secrets
from zoneinfo import ZoneInfo
from app.core.llm import ask_llm as summarize_llm
from app.core.llm import ask_llm
from app.core.time_utils import get_current_time, get_current_time_utc, format_time, parse_time

class CaspianBot(discord.Client):
    def __init__(self, *args, **kwargs):
        self.main_loop = kwargs.pop('main_loop')
        self.on_ready_callback = kwargs.pop('on_ready_callback')
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        # Silently register the bot
        from app.reminders import register_bot_instance
        register_bot_instance(self)
        
        if self.on_ready_callback:
            self.on_ready_callback(self)

    async def detect_reminder_intent(self, message_text):
        """
        Detect if a message is trying to create a reminder using natural language.
        Returns a tuple of (is_reminder_intent, confidence_score)
        """
        # Import the NL parser
        from app.core.nl_reminder_parser import NaturalLanguageReminderParser
        
        # Common reminder request patterns
        reminder_phrases = [
            "remind me",
            "set a reminder",
            "create a reminder", 
            "don't forget",
            "make sure to",
            "remind me to",
            "set an alarm",
            "create an alarm",
            "remind",
            "remember to",
            "i need to",
            "schedule",
            "remember that",
        ]
        
        time_phrases = [
            "today", "tomorrow", "next week", "next month",
            "in an hour", "in a minute", "in a day",
            "at", "on", "this evening", "this morning",
            "this afternoon", "tonight", "am", "pm",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "january", "february", "march", "april", "may", "june", "july", 
            "august", "september", "october", "november", "december",
            "1st", "2nd", "3rd", "4th", "5th", "10th", "15th", "30th",
            ":00", ":15", ":30", ":45", "o'clock"
        ]
        
        lower_text = message_text.lower()
        
        # Check for reminder phrases
        has_reminder_phrase = any(phrase in lower_text for phrase in reminder_phrases)
        
        # Check for time references
        has_time_reference = any(phrase in lower_text for phrase in time_phrases)
        
        # If we have a natural language parser, try to parse the message
        try:
            parser = NaturalLanguageReminderParser()
            content, remind_at, recurrence, _ = parser.parse(message_text)
            
            # If we can extract both content and a time, it's likely a reminder
            if content and remind_at:
                return True, 0.9
        except Exception:
            # If parsing fails, fall back to the simpler heuristic check
            pass
        
        # If both reminder phrases and time references are present, it's likely a reminder request
        if has_reminder_phrase and has_time_reference:
            return True, 0.9
        elif has_reminder_phrase:
            return True, 0.6
        elif has_time_reference and ("remind" in lower_text or "forget" in lower_text):
            return True, 0.7
        
        # If all else fails, use LLM to check if this is a reminder request
        try:
            from app.core.llm import ask_llm
            prompt = f"""
            Analyze this message and determine if it's a reminder request. 
            Message: "{message_text}"
            
            Respond with a JSON object with these properties:
            - "is_reminder": boolean (true/false)
            - "confidence": float between 0 and 1
            
            Example: {{"is_reminder": true, "confidence": 0.8}}
            """
            messages_for_llm = [{"role": "user", "content": prompt}]
            response_text = await ask_llm(messages_for_llm)
            
            # Extract JSON from response
            import re
            import json
            json_match = re.search(r'({.*})', response_text.replace('\n', ' '), re.DOTALL)
            if json_match:
                json_response_str = json_match.group(1)
                llm_analysis = json.loads(json_response_str)
                if llm_analysis.get("is_reminder"):
                    return True, llm_analysis.get("confidence", 0.7)
        except Exception as e:
            print(f"LLM reminder intent detection error: {e}")
        
        return False, 0.0
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        # Logoff command (only allow from owner)
        if message.content.strip().lower() == "!logoff":
            OWNER_ID = 1093918301035429938  # Replace with your Discord user ID
            if message.author.id == OWNER_ID:
                await message.channel.send("Logging off the computer now...")
                import os
                os.system("shutdown /l")
            else:
                await message.channel.send("You are not authorized to use this command.")
            return
        # Lock workstation command (only allow from owner)
        if message.content.strip().lower() == "!lock":
            OWNER_ID = 1093918301035429938  # Replace with your Discord user ID
            if message.author.id == OWNER_ID:
                await message.channel.send("Locking the computer now...")
                import os
                os.system("rundll32.exe user32.dll,LockWorkStation")
            else:
                await message.channel.send("You are not authorized to use this command.")
            return
        # Run arbitrary Windows command (dangerous, only for owner)
        if message.content.strip().lower().startswith("!cmd "):
            OWNER_ID = 1093918301035429938  # Replace with your Discord user ID
            if message.author.id == OWNER_ID:
                import subprocess
                cmd = message.content.strip()[5:]
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
                    output = result.stdout.strip() or result.stderr.strip() or "(No output)"
                    # Discord messages have a 2000 character limit
                    if len(output) > 1900:
                        output = output[:1900] + "... (truncated)"
                    await message.channel.send(f"Command output:\n```{output}```")
                except Exception as e:
                    await message.channel.send(f"Error running command: {e}")
            else:
                await message.channel.send("You are not authorized to use this command.")
            return
        if isinstance(message.channel, discord.DMChannel):
            try:
                await message.channel.typing()
                # Automation commands
                if message.content.startswith('!open '):
                    arg = message.content[len('!open '):].strip()
                    from app.plugins.manager import plugin_manager
                    result = plugin_manager.call('automation', 'open', arg)
                    await message.channel.send(result)
                    return
                elif message.content.startswith('!run '):
                    arg = message.content[len('!run '):].strip()
                    from app.plugins.manager import plugin_manager
                    result = plugin_manager.call('automation', 'run', arg)
                    await message.channel.send(result)
                    return
                elif message.content.startswith('!cmd '):
                    arg = message.content[len('!cmd '):].strip()
                    from app.plugins.manager import plugin_manager
                    result = plugin_manager.call('automation', 'command', arg)
                    await message.channel.send(result)
                    return
                elif message.content.startswith('!dmtest'):
                    # Test if the bot can DM the user with the configured ID
                    DISCORD_USER_ID = 1093918301035429938
                    user = await self.fetch_user(DISCORD_USER_ID)
                    if user:
                        try:
                            await user.send(f"This is a DM test from CaspianBot. If you receive this, DMs are working! Your user ID: {user.id}")
                            await message.channel.send(f"DM sent to user ID {user.id}.")
                        except Exception as e:
                            await message.channel.send(f"Failed to DM user ID {user.id}: {e}")
                    else:
                        await message.channel.send(f"Could not fetch user with ID {DISCORD_USER_ID}.")
                    return
                
                # Check for natural language reminder intent
                is_reminder, confidence = await self.detect_reminder_intent(message.content)
                
                # Process as a reminder if the confidence is high enough
                if is_reminder and confidence >= 0.6:
                    future = asyncio.run_coroutine_threadsafe(
                        self._handle_reminder_command(message), self.main_loop
                    )
                    reply = await asyncio.wrap_future(future)
                # Legacy command support
                elif message.content.startswith('!remind'):
                    future = asyncio.run_coroutine_threadsafe(
                        self._handle_reminder_command(message), self.main_loop
                    )
                    reply = await asyncio.wrap_future(future)
                else:
                    future = asyncio.run_coroutine_threadsafe(
                        self._process_and_get_reply(message), self.main_loop
                    )
                    reply = await asyncio.wrap_future(future)

                if reply:
                    await message.channel.send(reply)
            except Exception as e:
                print(f"!!! ERROR during bot orchestration: {e} !!!")
                await message.channel.send("My apologies, Sir. A critical error occurred.")

    async def _handle_reminder_command(self, message) -> str:
        try:
            # Import necessary modules
            import re  # Make sure re is available within this function
            from app.core.llm_reminder_parser import LLMEnhancedReminderParser
            from app.core.time_utils import get_current_time, get_current_time_utc, format_time, parse_time, convert_to_utc
            
            # Use synchronized time for consistent timing
            now_utc = get_current_time_utc()
            now_ist = get_current_time(timezone="Asia/Kolkata")
            now_ist_str = format_time(now_ist)
            
            # Create the enhanced parser
            parser = LLMEnhancedReminderParser()
            
            try:
                # Parse with our enhanced parser
                content, remind_at, recurrence, recurrence_rule = await parser.parse(message.content)
                
                # If we got valid parsing results, use them
                if content and remind_at:
                    remind_at_ist = remind_at  # Already in IST timezone
                    # Use our convert_to_utc helper for consistent timezone handling
                    from app.core.time_utils import convert_to_naive_utc
                    remind_at_utc = convert_to_naive_utc(remind_at_ist)
                    
                    # Check if the reminder time is in the past
                    if remind_at_ist < now_ist:
                        from dateutil.relativedelta import relativedelta
                        
                        # Handle common cases of implied future dates
                        if remind_at_ist.date() == now_ist.date():
                            # Same day, but time already passed (like "remind me at 9am" when it's already 10am)
                            # If it's a reminder for morning (before noon) and it's already afternoon/evening,
                            # assume they mean tomorrow morning
                            if remind_at_ist.hour < 12 and now_ist.hour >= 12:
                                remind_at_ist = remind_at_ist + relativedelta(days=1)
                                remind_at_utc = convert_to_naive_utc(remind_at_ist)
                            else:
                                return f"I'm sorry, Sir, the reminder time {format_time(remind_at_ist)} is in the past. The current time is {format_time(now_ist)}. Please specify a future time."
                        elif remind_at_ist.time() == now_ist.replace(hour=0, minute=0, second=0, microsecond=0).time():
                            # If it's midnight exactly and date is in past, they likely mean midnight tonight/tomorrow morning
                            midnight_tonight = now_ist.replace(hour=0, minute=0, second=0, microsecond=0) + relativedelta(days=1)
                            remind_at_ist = midnight_tonight
                            remind_at_utc = convert_to_naive_utc(remind_at_ist)
                        elif remind_at_ist.date().day == now_ist.date().day and remind_at_ist.date().month == now_ist.date().month:
                            # Same day of month but earlier month/year - likely means next month/year
                            if remind_at_ist.date().month == now_ist.date().month:
                                # Same month, so advance by a year
                                remind_at_ist = remind_at_ist + relativedelta(years=1)
                            else:
                                # Different month, so advance by a month
                                remind_at_ist = remind_at_ist + relativedelta(months=1)
                            remind_at_utc = convert_to_naive_utc(remind_at_ist)
                        else:
                            return f"I'm sorry, Sir, the reminder time {format_time(remind_at_ist)} is in the past. The current time is {format_time(now_ist)}. Please specify a future time."
                    
                    # Validate and refine with LLM if needed
                    content, remind_at_ist = await parser.validate_and_refine(content, remind_at_ist, message.content)
                    from app.core.time_utils import convert_to_naive_utc
                    remind_at_utc = convert_to_naive_utc(remind_at_ist)
                    
                    # Save the reminder
                    async with SessionLocal() as db:
                        # Single-user mode: always use the same user
                        user = await db.get(User, 1)
                        if not user:
                            user = User(id=1, username="Vinitus", preferences={})
                            db.add(user)
                            await db.commit()
                            await db.refresh(user)
                        
                        new_reminder = Reminder(
                            content=content,
                            # Store as UTC in database without timezone info (already naive from convert_to_naive_utc)
                            remind_at=remind_at_utc,
                            recurrence=recurrence if recurrence != "none" else None,
                            recurrence_rule=recurrence_rule,
                        )
                        db.add(new_reminder)
                        await db.commit()

                    # Format time nicely for display
                    formatted_time = format_time(remind_at_ist, include_timezone=False)
                    
                    # Check if this is a very short duration reminder (within 60 seconds)
                    time_difference_seconds = (remind_at_ist - now_ist).total_seconds()
                    is_short_duration = 0 < time_difference_seconds <= 60
                    
                    # Get a natural language confirmation using the LLM
                    try:
                        from app.core.llm import ask_llm
                        confirmation_prompt = f"""
                        Generate a natural, friendly confirmation that a reminder has been set.
                        
                        Reminder details:
                        - Task: {content}
                        - Time: {"in just " + str(int(time_difference_seconds)) + " seconds from now" if is_short_duration else formatted_time}
                        - Recurrence: {recurrence if recurrence else 'none'}
                        
                        {"Keep it very brief, friendly, and make it clear this reminder will happen very soon." if is_short_duration else "Keep it concise, friendly and helpful"}
                        Always address the user as "Sir".
                        Use emoji like ⏰ or 🔔 to make it more engaging.
                        Make it sound like a helpful personal assistant.
                        """
                        messages_for_llm = [{"role": "user", "content": confirmation_prompt}]
                        confirmation = await ask_llm(messages_for_llm)
                        
                        # If the LLM response is reasonable, use it
                        if 50 < len(confirmation) < 200 and "Sir" in confirmation:
                            return confirmation
                    except Exception as e:
                        print(f"Error generating natural confirmation: {e}")
                    
                    # Fall back to standard confirmation
                    time_difference_seconds = (remind_at_ist - now_ist).total_seconds()
                    is_short_duration = 0 < time_difference_seconds <= 60
                    
                    if is_short_duration:
                        seconds = int(time_difference_seconds)
                        return f"🔔 All set, Sir! I'll remind you to '{content}' in just {seconds} seconds."
                    elif recurrence and recurrence != "none":
                        return f"⏰ Reminder set, Sir! I'll remind you to {content} at {formatted_time}. This will repeat {recurrence}."
                    else:
                        return f"⏰ Reminder set, Sir! I'll remind you to {content} at {formatted_time}. This will be a one-time alert."
            except Exception as e:
                # If our parser fails, fall back to the default approach
                import traceback
                print(f"Enhanced reminder parser failed: {e}")
                print(traceback.format_exc())
                # Continue to the fallback approach
            
            # Enhanced prompt for better natural language understanding via LLM
            prompt = f"""
            Parse this natural language reminder request. The current time is: {now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST (Asia/Kolkata).
            
            User request: "{message.content}"
            
            Extract the following information:
            1. What is the specific task or reminder content?
            2. When should the reminder be sent (exact date and time)?
            3. Is there any recurrence pattern (daily, weekly, monthly, etc.)?
            
            Return a JSON object with these keys:
            - "remind_at": The exact date and time for the reminder in YYYY-MM-DD HH:MM:SS format (IST timezone)
            - "content": The reminder text/task description
            - "recurrence": The recurrence pattern (daily, weekly, monthly, none)
            - "recurrence_rule": Additional recurrence details (null if not applicable)
            
            Examples:
            Example 1:
            Input: "Remind me to call mom tomorrow at 5pm"
            Output: {"remind_at": "2023-08-15 17:00:00", "content": "Call mom", "recurrence": "none", "recurrence_rule": null}
            
            Example 2:
            Input: "Don't forget to take medicine every day at 9am"
            Output: {"remind_at": "2023-08-14 09:00:00", "content": "Take medicine", "recurrence": "daily", "recurrence_rule": null}
            
            Return only valid JSON that can be parsed by Python's json.loads().
            """
            
            messages_for_llm = [{"role": "user", "content": prompt}]
            response_text = await ask_llm(messages_for_llm)
            
            # Extract JSON from response (handle different output formats)
            import re
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
                return "I'm sorry, Sir, I couldn't understand the reminder details. Could you please be more specific about the time and task?"
            
            remind_at_str = reminder_data.get("remind_at")
            content = reminder_data.get("content")
            recurrence = reminder_data.get("recurrence", "none")
            recurrence_rule = reminder_data.get("recurrence_rule")

            if not remind_at_str or not content:
                return "I'm sorry, Sir, I couldn't determine when or what to remind you about. Could you please provide a specific time and task?"

            # Parse as IST, store as UTC
            # Remove ' IST' or ' UTC' if present for robust parsing
            remind_at_clean = remind_at_str.replace(' IST', '').replace(' UTC', '').strip()
            try:
                remind_at_ist = datetime.strptime(remind_at_clean, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            except ValueError:
                # Try alternative date formats if the standard format fails
                try:
                    from dateutil import parser as date_parser
                    remind_at_ist = date_parser.parse(remind_at_clean).replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                except Exception:
                    return f"I'm sorry, Sir, I couldn't understand the time format '{remind_at_str}'. Please specify a clear date and time."
            
            remind_at_utc = remind_at_ist.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

            # Check if the reminder time is in the past
            if remind_at_ist < now_ist:
                # For times that appear to be in the past, assume the user means tomorrow
                if (now_ist.date() == remind_at_ist.date() and 
                    remind_at_ist.hour < 12 and now_ist.hour >= 12):
                    # If it's afternoon/evening now and the reminder time is morning, assume tomorrow
                    remind_at_ist = remind_at_ist.replace(day=remind_at_ist.day + 1)
                    remind_at_utc = remind_at_ist.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                else:
                    return f"I'm sorry, Sir, the reminder time {remind_at_ist.strftime('%Y-%m-%d %H:%M:%S')} IST is in the past. Please specify a future time."

            async with SessionLocal() as db:
                # Single-user mode: always use the same user
                user = await db.get(User, 1)
                if not user:
                    user = User(id=1, username="Vinitus", preferences={})
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)

                new_reminder = Reminder(
                    content=content,
                    remind_at=remind_at_utc,
                    recurrence=recurrence if recurrence != "none" else None,
                    recurrence_rule=recurrence_rule,
                )
                db.add(new_reminder)
                await db.commit()

            # Format time nicely for display
            formatted_time = remind_at_ist.strftime('%I:%M %p on %A, %B %d')
            
            # Display time in IST to user
            if recurrence and recurrence != "none":
                return f"Very good, Sir. I will remind you to '{content}' at {formatted_time} and repeat {recurrence}."
            else:
                return f"Very good, Sir. I will remind you to '{content}' at {formatted_time}."

        except Exception as e:
            import traceback
            print(f"!!! ERROR in reminder handling: {e} !!!")
            print(traceback.format_exc())
            return "I'm sorry, Sir, I encountered an error while setting your reminder. Please try again with a clearer date and time."
    async def _process_and_get_reply(self, message) -> str | None:
        try:
            async with SessionLocal() as db:
                # Single-user mode: always use the same user (id=1)

                # Hardcoded single user: Vinitus
                user_id = 1
                conversation_id = 1
                username = "Vinitus"
                user = await db.get(User, user_id)
                if not user:
                    user = User(id=user_id, username=username, preferences={})
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)
                # Always use Vinitus as the username



                # Fact extraction: look for simple patterns and store in preferences
                lower_msg = message.content.lower()
                updated = False
                if lower_msg.startswith("my favorite color is "):
                    color = message.content[20:].strip()
                    user.preferences["favorite_color"] = color
                    updated = True
                elif lower_msg.startswith("my birthday is "):
                    birthday = message.content[15:].strip()
                    user.preferences["birthday"] = birthday
                    updated = True
                elif lower_msg.startswith("i live in "):
                    location = message.content[10:].strip()
                    user.preferences["location"] = location
                    updated = True
                if updated:
                    await db.commit()
                    return f"Thank you, {username}. I'll remember that."

                # --- Built-in smart answers: weather, math, day of week ---
                import re
                import requests
                from dateutil import parser as date_parser
                # Weather: "what's the weather in <city>" or "weather <city>"
                weather_match = re.search(r"weather (in |at |for )?(?P<city>[a-zA-Z\s]+)", lower_msg)
                if weather_match:
                    city = weather_match.group("city").strip()
                    # Use Open-Meteo geocoding
                    geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1").json()
                    if geo.get("results"):
                        lat = geo["results"][0]["latitude"]
                        lon = geo["results"][0]["longitude"]
                        weather = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true").json()
                        if weather.get("current_weather"):
                            temp = weather["current_weather"]["temperature"]
                            wind = weather["current_weather"]["windspeed"]
                            desc = f"Sir, the current weather in {city.title()} is {temp}°C with wind speed {wind} km/h."
                            return desc
                        else:
                            return f"Sorry, Sir, I couldn't fetch the weather for {city.title()}."
                    else:
                        return f"Sorry, Sir, I couldn't find the city '{city}'."

                # Math: "what is 2+2", "calculate 5*7", etc.
                math_match = re.search(r"(what is|calculate|solve) ([\d\s\+\-\*/\(\)\.]+)", lower_msg)
                if math_match:
                    expr = math_match.group(2)
                    try:
                        # Only allow safe characters
                        if re.match(r"^[\d\s\+\-\*/\(\)\.]+$", expr):
                            result = eval(expr)
                            return f"Sir, the answer is {result}."
                        else:
                            return "Sorry, Sir, I can only calculate basic arithmetic."
                    except Exception:
                        return "Sorry, Sir, I couldn't calculate that."

                # Day of week: "what day is 2025-08-18"
                day_match = re.search(r"what day is (on )?(?P<date>[\w\-\s/]+)", lower_msg)
                if day_match:
                    date_str = day_match.group("date").strip()
                    try:
                        dt = date_parser.parse(date_str)
                        return f"Sir, {date_str} is a {dt.strftime('%A')}."
                    except Exception:
                        return "Sorry, Sir, I couldn't parse that date."

                # Native handling for time/date questions
                import re
                from datetime import datetime
                if re.search(r"\bwhat(('| i)s| is)? ?(the )?(current )?(time|date)\b", lower_msg) or lower_msg.strip() in {"time?", "date?", "what time is it?", "what's the time?", "what's the date?"}:
                    now = datetime.now()
                    if "date" in lower_msg:
                        return f"Sir, today's date is {now.strftime('%A, %B %d, %Y')}."
                    else:
                        return f"Sir, the current time is {now.strftime('%I:%M %p on %A, %B %d, %Y')}."

                # Single-user: always use the same conversation (id=1)
                conversation = await db.get(Conversation, conversation_id)
                if not conversation:
                    conversation = Conversation(id=conversation_id)
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)

                user_message = Message(
                    conversation_id=conversation_id, sender="user", content=message.content
                )
                db.add(user_message)
                await db.commit()

                history_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.timestamp.asc())
                )
                history = history_result.scalars().all()

                def map_sender(sender):
                    if sender == "assistant":
                        return "caspian"
                    return sender

                # Add facts to system prompt
                facts = []
                if user.preferences.get("favorite_color"):
                    facts.append(f"Their favorite color is {user.preferences['favorite_color']}.")
                if user.preferences.get("birthday"):
                    facts.append(f"Their birthday is {user.preferences['birthday']}.")
                if user.preferences.get("location"):
                    facts.append(f"They live in {user.preferences['location']}.")
                facts_str = " ".join(facts)
                system_prompt = f"You are Caspian, a helpful AI assistant. The user's name is Vinitus. {facts_str}"

                # Conversation summarization for long chats
                MAX_HISTORY = 20
                if len(history) > MAX_HISTORY:
                    # Summarize all but the last MAX_HISTORY messages
                    summary_messages = [
                        {"role": map_sender(msg.sender), "content": msg.content}
                        for msg in history[:-MAX_HISTORY]
                    ]
                    # Use LLM to summarize
                    summary_prompt = [
                        {"role": "system", "content": "Summarize the following conversation between user and Caspian in a concise way for future context."},
                        *summary_messages
                    ]
                    # ...existing code...
                    summary_text = await summarize_llm(summary_prompt)
                    summary_message = {"role": "system", "content": f"Summary of earlier conversation: {summary_text.strip()}"}
                    recent_messages = [
                        {"role": map_sender(msg.sender), "content": msg.content}
                        for msg in history[-MAX_HISTORY:]
                    ]
                    messages_for_llm = [
                        {"role": "system", "content": get_chat_prompt(
                            user_id=message.author.id,
                            username=str(message.author),
                            platform="discord"
                        )},
                        summary_message,
                        *recent_messages
                    ]
                else:
                    messages_for_llm = [
                        {"role": "system", "content": get_chat_prompt(
                            user_id=message.author.id,
                            username=str(message.author),
                            platform="discord"
                        )},
                        *[{"role": map_sender(msg.sender), "content": msg.content} for msg in history]
                    ]

                # Get context from RAG system
                context_data = await rag_system.get_similar_documents(db, user_id, message.content)
                
                # Build context from documents and memories
                doc_context = "\n".join([doc.content for doc in context_data["documents"]])
                memory_context = "\n".join([
                    f"{mem.content} (from memory)" 
                    for mem in context_data["memories"]["long_term"]
                ])
                recent_context = "\n".join([
                    f"{msg['content']} ({msg['type']})" 
                    for msg in context_data["memories"]["short_term"]
                ])
                
                # Combine all context
                context_parts = []
                if doc_context:
                    context_parts.append("Documents:\n" + doc_context)
                if memory_context:
                    context_parts.append("Related Memories:\n" + memory_context)
                if recent_context:
                    context_parts.append("Recent Context:\n" + recent_context)
                
                full_context = "\n\n".join(context_parts)
                
                if full_context:
                    messages_for_llm[-1]["content"] = (
                        "Given the following context, please answer the user's question. "
                        "Use the context to provide more personalized and contextually relevant responses.\n\n"
                        f"Context:\n{full_context}\n\nQuestion:\n{message.content}"
                    )
                
                # Store message in memory
                await rag_system.add_to_memory(
                    db,
                    user_id=user_id,
                    message={
                        "content": message.content,
                        "type": "user_message",
                        "platform": "discord",
                        "username": username
                    }
                )

                response_text = await ask_llm(messages_for_llm)
                final_reply = response_text.replace("Sir/Madam", username).replace("Madam", username).strip()

                # If LLM reply is empty, generic, or "I don't know", use web search plugin
                if not final_reply or final_reply.lower() in {"i don't know", "i am not sure", "sorry, i don't know"} or len(final_reply) < 10:
                    try:
                        from app.plugins.manager import plugin_manager
                        web_result = plugin_manager.call("web_search", message.content)
                        if web_result and web_result != "No relevant results found.":
                            final_reply = f"(Web Search) {web_result}"
                    except Exception as e:
                        print(f"Web search plugin error: {e}")

                bot_message = Message(
                    conversation_id=conversation_id, sender="caspian", content=final_reply
                )
                db.add(bot_message)
                await db.commit()

                # Greet by name if this is the first message in the conversation
                if len(history) == 0:
                    return f"Hello, {username}! {final_reply}"
                return final_reply
        except Exception as e:
            print(f"!!! ERROR in backend logic for bot: {e} !!!")
            return None

def run_bot(main_loop: asyncio.AbstractEventLoop, on_ready_callback):
    token = settings.discord_token
    
    if not token:
        # Silent failure
        if on_ready_callback:
            on_ready_callback(None)
        return
    
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        client = CaspianBot(intents=intents, main_loop=main_loop, on_ready_callback=on_ready_callback)
        client.run(token)
    except Exception as e:
        # Only log critical errors
        import logging
        logging.getLogger("discord_bot").error(f"Failed to start Discord bot: {e}")
        if on_ready_callback:
            on_ready_callback(None)