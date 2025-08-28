import asyncio

# --- Helper: Detect reminder intent ---
async def detect_reminder_intent(message_text):
    from app.core.nl_reminder_parser import NaturalLanguageReminderParser
    reminder_phrases = [
        "remind me", "set a reminder", "create a reminder", "don't forget", "make sure to",
        "remind me to", "set an alarm", "create an alarm", "remind", "remember to", "i need to",
        "schedule", "remember that",
    ]
    time_phrases = [
        "today", "tomorrow", "next week", "next month", "in an hour", "in a minute", "in a day",
        "at", "on", "this evening", "this morning", "this afternoon", "tonight", "am", "pm",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "january", "february", "march", "april", "may", "june", "july", "august", "september",
        "october", "november", "december", "1st", "2nd", "3rd", "4th", "5th", "10th", "15th", "30th",
        ":00", ":15", ":30", ":45", "o'clock"
    ]
    lower_text = message_text.lower()
    has_reminder_phrase = any(phrase in lower_text for phrase in reminder_phrases)
    has_time_reference = any(phrase in lower_text for phrase in time_phrases)
    try:
        parser = NaturalLanguageReminderParser()
        content, remind_at, recurrence, _ = parser.parse(message_text)
        if content and remind_at:
            return True, 0.9
    except Exception:
        pass
    if has_reminder_phrase and has_time_reference:
        return True, 0.8
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
        import re, json
        json_match = re.search(r'({.*})', response_text.replace('\n', ' '), re.DOTALL)
        if json_match:
            json_response_str = json_match.group(1)
            llm_analysis = json.loads(json_response_str)
            if llm_analysis.get("is_reminder") and llm_analysis.get("confidence", 0) > 0.85:
                return True, llm_analysis.get("confidence", 0.85)
    except Exception:
        pass
    return False, 0.0

# --- Helper: Handle reminder command ---
async def handle_reminder_command(bot, message):
    from app.core.llm_reminder_parser import LLMEnhancedReminderParser
    from app.core.time_utils import get_current_time, get_current_time_utc, format_time, parse_time, convert_to_naive_utc
    from app.db.models import SessionLocal, User, Reminder
    now_ist = get_current_time(timezone="Asia/Kolkata")
    parser = LLMEnhancedReminderParser()
    try:
        content, remind_at, recurrence, recurrence_rule = await parser.parse(message.content)
        if not content or not remind_at or len(content) < 3:
            return ("I'm sorry, I couldn't extract the reminder details. Please clarify what and when you want to be reminded?")
        content, remind_at = await parser.validate_and_refine(content, remind_at, message.content)
        formatted_time = format_time(remind_at, include_timezone=False)
        confirmation_message = (
            f"Just to confirm: Should I remind you to '{content}' at {formatted_time}? "
            f"{'This will repeat ' + recurrence if recurrence else 'This will be a one-time alert.'} "
            "Reply 'yes' to confirm or provide corrections.")
        await message.channel.send(confirmation_message)
        def check(m):
            return m.author == message.author and m.channel == message.channel
        try:
            reply = await bot.wait_for('message', timeout=30.0, check=check)
        except Exception:
            return "No response received. Reminder not set. Please try again."
        if reply.content.strip().lower() not in ["yes", "y", "confirm", "ok"]:
            return "Okay. Reminder not set."
        remind_at_utc = convert_to_naive_utc(remind_at)
        async with SessionLocal() as db:
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
        return f"⏰ Reminder set! I'll remind you to {content} at {formatted_time}."
    except Exception:
        return "Sorry, I couldn't set the reminder. Please try again."

# --- Helper: Process and get chat reply ---
async def process_and_get_reply(bot, message):
    from app.db.models import SessionLocal, User, Conversation, Message
    from app.rag import rag_system
    from app.core.personality import get_chat_prompt
    from app.core.llm import ask_llm as summarize_llm, ask_llm
    import json
    try:
        async with SessionLocal() as db:
            user_id = 1
            conversation_id = 1
            username = "Vinitus"
            user = await db.get(User, user_id)
            if not user:
                user = User(id=user_id, username=username, preferences={})
                db.add(user)
                await db.commit()
                await db.refresh(user)
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
                Message.__table__.select().where(Message.conversation_id == conversation.id).order_by(Message.timestamp.asc())
            )
            history = history_result.fetchall()
            messages_for_llm = [
                {"role": "system", "content": get_chat_prompt(
                    user_id=message.author.id,
                    username=str(message.author),
                    platform="discord"
                )},
                *[{"role": "user", "content": msg.content} for msg in history]
            ]
            response_text = await ask_llm(messages_for_llm)
            final_reply = response_text.strip()
            bot_message = Message(
                conversation_id=conversation_id, sender="caspian", content=final_reply
            )
            db.add(bot_message)
            await db.commit()
            return final_reply
    except Exception:
        return None

# --- Helper: Owner/admin commands ---
async def handle_owner_commands(bot, message):
    OWNER_ID = 1093918301035429938
    if message.content.strip().lower() == "!logoff" and message.author.id == OWNER_ID:
        await message.channel.send("Logging off the computer now...")
        import os
        os.system("shutdown /l")
        return True
    if message.content.strip().lower() == "!lock" and message.author.id == OWNER_ID:
        await message.channel.send("Locking the computer now...")
        import os
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True
    if message.content.strip().lower().startswith("!cmd ") and message.author.id == OWNER_ID:
        import subprocess
        cmd = message.content.strip()[5:]
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
            output = result.stdout.strip() or result.stderr.strip() or "(No output)"
            if len(output) > 1900:
                output = output[:1900] + "... (truncated)"
            await message.channel.send(f"Command output:\n```{output}```")
        except Exception as e:
            await message.channel.send(f"Error running command: {e}")
        return True
    return False

# --- Helper: DM automation commands ---
async def handle_dm_automation(bot, message):
    if message.content.startswith('!open '):
        arg = message.content[len('!open '):].strip()
        from app.plugins.manager import plugin_manager
        result = plugin_manager.call('automation', 'open', arg)
        await message.channel.send(result)
        return True
    elif message.content.startswith('!run '):
        arg = message.content[len('!run '):].strip()
        from app.plugins.manager import plugin_manager
        result = plugin_manager.call('automation', 'run', arg)
        await message.channel.send(result)
        return True
    elif message.content.startswith('!cmd '):
        arg = message.content[len('!cmd '):].strip()
        from app.plugins.manager import plugin_manager
        result = plugin_manager.call('automation', 'command', arg)
        await message.channel.send(result)
        return True
    elif message.content.startswith('!dmtest'):
        DISCORD_USER_ID = 1093918301035429938
        user = await bot.fetch_user(DISCORD_USER_ID)
        if user:
            try:
                await user.send(f"This is a DM test from CaspianBot. If you receive this, DMs are working! Your user ID: {user.id}")
                await message.channel.send(f"DM sent to user ID {user.id}.")
            except Exception as e:
                await message.channel.send(f"Failed to DM user ID {user.id}: {e}")
        else:
            await message.channel.send(f"Could not fetch user with ID {DISCORD_USER_ID}.")
        return True
    return False
