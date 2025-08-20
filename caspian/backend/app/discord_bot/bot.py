import asyncio
import discord
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

class CaspianBot(discord.Client):
    async def on_ready(self):
        print(f"Caspian Discord Bot connected as {self.user}")
        self.loop.create_task(self.check_reminders_periodically())
        if self.on_ready_callback:
            self.on_ready_callback(self)

    async def check_reminders_periodically(self):
        from zoneinfo import ZoneInfo
        from dateutil.relativedelta import relativedelta
        while True:
            try:
                now = datetime.utcnow()
                print(f"[ReminderChecker] Checking reminders at {now} UTC")
                async with SessionLocal() as db:
                    # Log all reminders for debugging
                    all_reminders_result = await db.execute(select(Reminder))
                    all_reminders = all_reminders_result.scalars().all()
                    print("[ReminderChecker] All reminders in DB:")
                    for r in all_reminders:
                        print(f"  ID: {r.id}, remind_at: {r.remind_at}, is_sent: {r.is_sent}, content: {r.content}")

                    result = await db.execute(
                        select(Reminder).where(
                            Reminder.remind_at <= now,
                            Reminder.is_sent == False
                        )
                    )
                    due_reminders = result.scalars().all()
                    print(f"[ReminderChecker] Found {len(due_reminders)} due reminders.")

                    for reminder in due_reminders:
                        try:
                            print(f"[ReminderChecker] Processing reminder ID {reminder.id} for content: {reminder.content}")
                            DISCORD_USER_ID = 1093918301035429938
                            print(f"[ReminderChecker] Fetching user {DISCORD_USER_ID}")
                            discord_user = await self.fetch_user(DISCORD_USER_ID)
                            print(f"[ReminderChecker] discord_user: {discord_user}")
                            if discord_user:
                                remind_at = reminder.remind_at
                                if remind_at.tzinfo is None:
                                    remind_at = remind_at.replace(tzinfo=ZoneInfo("UTC"))
                                else:
                                    remind_at = remind_at.astimezone(ZoneInfo("UTC"))
                                remind_at_ist = remind_at.astimezone(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                                print(f"[ReminderChecker] Sending DM: {reminder.content} at {remind_at_ist} IST")
                                await discord_user.send(f"Sir, a reminder for you: {reminder.content}\nTime: {remind_at_ist} IST")
                            else:
                                print(f"[ReminderChecker] Could not fetch Discord user {DISCORD_USER_ID}")
                            # Handle recurrence
                            if reminder.recurrence and reminder.recurrence != "none":
                                next_time = None
                                if reminder.recurrence == "daily":
                                    next_time = reminder.remind_at + relativedelta(days=1)
                                elif reminder.recurrence == "weekly":
                                    next_time = reminder.remind_at + relativedelta(weeks=1)
                                elif reminder.recurrence == "monthly":
                                    next_time = reminder.remind_at + relativedelta(months=1)
                                elif reminder.recurrence_rule:
                                    pass
                                if next_time:
                                    reminder.remind_at = next_time
                                    reminder.is_sent = False
                                    await db.commit()
                                    print(f"[ReminderChecker] Rescheduled recurring reminder {reminder.id}")
                                else:
                                    reminder.is_sent = True
                                    await db.commit()
                                    print(f"[ReminderChecker] Marked reminder {reminder.id} as sent (no next recurrence)")
                            else:
                                reminder.is_sent = True
                                await db.commit()
                                print(f"[ReminderChecker] Sent reminder {reminder.id}")
                        except Exception as e:
                            print(f"[ReminderChecker] Error sending reminder {reminder.id}: {e}")
            except Exception as e:
                print(f"[ReminderChecker] An error occurred in the reminder checking loop: {e}")
            await asyncio.sleep(5)
    async def on_ready(self):
        print(f"Caspian Discord Bot connected as {self.user}")
        # Start background reminder checker
        self.loop.create_task(self.check_reminders_periodically())
        if self.on_ready_callback:
            self.on_ready_callback(self)

    async def check_reminders_periodically(self):
        from zoneinfo import ZoneInfo
        from dateutil.relativedelta import relativedelta
        while True:
            try:
                now = datetime.utcnow()
                print(f"[ReminderChecker] Checking reminders at {now} UTC")
                async with SessionLocal() as db:
                    # Log all reminders for debugging
                    all_reminders_result = await db.execute(select(Reminder))
                    all_reminders = all_reminders_result.scalars().all()
                    print("[ReminderChecker] All reminders in DB:")
                    for r in all_reminders:
                        print(f"  ID: {r.id}, remind_at: {r.remind_at}, is_sent: {r.is_sent}, content: {r.content}")

                    result = await db.execute(
                        select(Reminder).where(
                            Reminder.remind_at <= now,
                            Reminder.is_sent == False
                        )
                    )
                    due_reminders = result.scalars().all()
                    print(f"[ReminderChecker] Found {len(due_reminders)} due reminders.")

                    for reminder in due_reminders:
                        try:
                            print(f"[ReminderChecker] Processing reminder ID {reminder.id} for content: {reminder.content}")
                            DISCORD_USER_ID = 1093918301035429938
                            print(f"[ReminderChecker] Fetching user {DISCORD_USER_ID}")
                            discord_user = await self.fetch_user(DISCORD_USER_ID)
                            print(f"[ReminderChecker] discord_user: {discord_user}")
                            if discord_user:
                                remind_at = reminder.remind_at
                                if remind_at.tzinfo is None:
                                    remind_at = remind_at.replace(tzinfo=ZoneInfo("UTC"))
                                else:
                                    remind_at = remind_at.astimezone(ZoneInfo("UTC"))
                                remind_at_ist = remind_at.astimezone(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
                                print(f"[ReminderChecker] Sending DM: {reminder.content} at {remind_at_ist} IST")
                                await discord_user.send(f"Sir, a reminder for you: {reminder.content}\nTime: {remind_at_ist} IST")
                            else:
                                print(f"[ReminderChecker] Could not fetch Discord user {DISCORD_USER_ID}")
                            # Handle recurrence
                            if reminder.recurrence and reminder.recurrence != "none":
                                next_time = None
                                if reminder.recurrence == "daily":
                                    next_time = reminder.remind_at + relativedelta(days=1)
                                elif reminder.recurrence == "weekly":
                                    next_time = reminder.remind_at + relativedelta(weeks=1)
                                elif reminder.recurrence == "monthly":
                                    next_time = reminder.remind_at + relativedelta(months=1)
                                elif reminder.recurrence_rule:
                                    pass
                                if next_time:
                                    reminder.remind_at = next_time
                                    reminder.is_sent = False
                                    await db.commit()
                                    print(f"[ReminderChecker] Rescheduled recurring reminder {reminder.id}")
                                else:
                                    reminder.is_sent = True
                                    await db.commit()
                                    print(f"[ReminderChecker] Marked reminder {reminder.id} as sent (no next recurrence)")
                            else:
                                reminder.is_sent = True
                                await db.commit()
                                print(f"[ReminderChecker] Sent reminder {reminder.id}")
                        except Exception as e:
                            print(f"[ReminderChecker] Error sending reminder {reminder.id}: {e}")
            except Exception as e:
                print(f"[ReminderChecker] An error occurred in the reminder checking loop: {e}")
            await asyncio.sleep(5)
    def __init__(self, *args, **kwargs):
        self.main_loop = kwargs.pop('main_loop')
        self.on_ready_callback = kwargs.pop('on_ready_callback')
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f"Caspian Discord Bot connected as {self.user}")
        if self.on_ready_callback:
            self.on_ready_callback(self)

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
                # Existing commands
                if message.content.startswith('!remind'):
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
            now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            prompt = f"""
            Given the user's reminder request and the current UTC time, extract the reminder content, the exact time for the first reminder, and any recurrence pattern (e.g., daily, weekly, monthly, or a cron/rrule string if custom).
            The current time is: {now_utc} UTC.
            User request: "{message.content}"
            Please return a JSON object with keys: "remind_at" (in YYYY-MM-DD HH:MM:SS format, UTC), "content", "recurrence" (e.g., daily/weekly/monthly/none), and "recurrence_rule" (null or a JSON object for custom recurrence).
            """
            messages_for_llm = [{"role": "user", "content": prompt}]
            response_text = await ask_llm(messages_for_llm)
            
            json_response_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
            reminder_data = json.loads(json_response_str)

            remind_at_str = reminder_data.get("remind_at")
            content = reminder_data.get("content")
            recurrence = reminder_data.get("recurrence")
            recurrence_rule = reminder_data.get("recurrence_rule")

            if not remind_at_str or not content:
                return "I'm sorry, Sir, I could not understand the reminder. Please try again."
                
            # Remove ' UTC' if present for robust parsing
            remind_at_clean = remind_at_str.replace(' UTC', '').strip()
            remind_at = datetime.strptime(remind_at_clean, '%Y-%m-%d %H:%M:%S')
            # Always make reminder time UTC-aware before saving
            from zoneinfo import ZoneInfo
            # Store as naive UTC for DB compatibility
            remind_at = remind_at.replace(tzinfo=None)


            # Check if the reminder time is in the past
            now_utc = datetime.now(ZoneInfo("UTC"))
            # If remind_at is naive, treat as UTC
            if remind_at.tzinfo is None:
                remind_at_utc = remind_at.replace(tzinfo=ZoneInfo("UTC"))
            else:
                remind_at_utc = remind_at.astimezone(ZoneInfo("UTC"))
            if remind_at_utc < now_utc:
                return f"I'm sorry, Sir, the reminder time {remind_at_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC is in the past. Please specify a future time."

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
                    remind_at=remind_at.replace(tzinfo=None),
                    recurrence=recurrence,
                    recurrence_rule=recurrence_rule,
                )
                db.add(new_reminder)
                await db.commit()

            remind_at_ist = remind_at_utc.astimezone(ZoneInfo("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
            if recurrence and recurrence != "none":
                return f"Very good, Sir. I will remind you about '{content}' at {remind_at_ist} IST and repeat {recurrence}."
            else:
                return f"Very good, Sir. I will remind you about '{content}' at {remind_at_ist} IST."

        except Exception as e:
            print(f"!!! ERROR in reminder handling: {e} !!!")
            return "I'm sorry, Sir, I encountered an error while setting your reminder."


    # ...existing code...
    # ...existing code...
        try:
            now_utc = datetime.utcnow()
            now_ist = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Kolkata"))
            now_ist_str = now_ist.strftime('%Y-%m-%d %H:%M:%S')
            prompt = f"""
            Given the user's reminder request and the current IST time, extract the reminder content, the exact time for the first reminder, and any recurrence pattern (e.g., daily, weekly, monthly, or a cron/rrule string if custom).
            The current time is: {now_ist_str} IST (Asia/Kolkata).
            User request: "{message.content}"
            Please return a JSON object with keys: "remind_at" (in YYYY-MM-DD HH:MM:SS format, IST), "content", "recurrence" (e.g., daily/weekly/monthly/none), and "recurrence_rule" (null or a JSON object for custom recurrence).
            """
            messages_for_llm = [{"role": "user", "content": prompt}]
            response_text = await ask_llm(messages_for_llm)
            
            json_response_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
            reminder_data = json.loads(json_response_str)

            remind_at_str = reminder_data.get("remind_at")
            content = reminder_data.get("content")
            recurrence = reminder_data.get("recurrence")
            recurrence_rule = reminder_data.get("recurrence_rule")

            if not remind_at_str or not content:
                return "I'm sorry, Sir, I could not understand the reminder. Please try again."

            # Parse as IST, store as UTC
            # Remove ' IST' or ' UTC' if present for robust parsing
            remind_at_clean = remind_at_str.replace(' IST', '').replace(' UTC', '').strip()
            remind_at_ist = datetime.strptime(remind_at_clean, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            remind_at_utc = remind_at_ist.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

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
                    recurrence=recurrence,
                    recurrence_rule=recurrence_rule,
                )
                db.add(new_reminder)
                await db.commit()

            # Display time in IST to user
            if recurrence and recurrence != "none":
                return f"Very good, Sir. I will remind you about '{content}' at {remind_at_str} IST and repeat {recurrence}."
            else:
                return f"Very good, Sir. I will remind you about '{content}' at {remind_at_str} IST."

        except Exception as e:
            print(f"!!! ERROR in reminder handling: {e} !!!")
            return "I'm sorry, Sir, I encountered an error while setting your reminder."
    async def _process_and_get_reply(self, message) -> str | None:
    # ...existing code...
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
        print("DISCORD_TOKEN not set; Discord bot will not start.")
        return
    intents = discord.Intents.default()
    intents.message_content = True
    client = CaspianBot(intents=intents, main_loop=main_loop, on_ready_callback=on_ready_callback)
    client.run(token)