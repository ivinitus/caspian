import asyncio
from datetime import datetime, timedelta
from app.db.models import Reminder, SessionLocal, User
from app.core.time_utils import get_current_time, get_current_time_utc, convert_to_naive_utc
from sqlalchemy import select

async def test_timezone_handling():
    """Test script to verify timezone handling in reminders."""
    print("===== Testing Timezone Handling in Reminders =====")
    
    # 1. Get current time in different formats
    now_utc = get_current_time_utc()
    now_ist = get_current_time("Asia/Kolkata")
    now_naive_utc = convert_to_naive_utc(now_utc)
    
    print(f"Current time UTC (aware): {now_utc}")
    print(f"Current time IST (aware): {now_ist}")
    print(f"Current time UTC (naive): {now_naive_utc}")
    
    # 2. Create a test reminder for 5 minutes from now
    test_time = now_utc + timedelta(minutes=5)
    test_time_naive = convert_to_naive_utc(test_time)
    
    print(f"\nCreating test reminder for: {test_time}")
    print(f"Test time naive UTC: {test_time_naive}")
    
    # 3. Save the reminder to the database
    async with SessionLocal() as db:
        try:
            # Find user ID 1 or create it
            user = await db.get(User, 1)
            if not user:
                user = User(id=1, username="testuser", preferences={})
                db.add(user)
                await db.commit()
                await db.refresh(user)
            
            # Create test reminder
            test_reminder = Reminder(
                user_id=1,
                content="Test reminder for timezone handling",
                remind_at=test_time_naive,  # Storing naive UTC time
                is_sent=False
            )
            db.add(test_reminder)
            await db.commit()
            print(f"Reminder created with ID: {test_reminder.id}")
            
            # 4. Read back the reminder
            result = await db.execute(
                select(Reminder).where(Reminder.id == test_reminder.id)
            )
            stored_reminder = result.scalar_one()
            
            print(f"\nStored reminder time (DB format): {stored_reminder.remind_at}")
            print(f"Stored reminder tzinfo: {stored_reminder.remind_at.tzinfo}")
            
            # 5. Test query with timezone-aware time
            # This should fail if we don't handle timezone properly
            result = await db.execute(
                select(Reminder).where(
                    Reminder.remind_at <= now_utc,
                    Reminder.is_sent == False
                )
            )
            should_fail_reminders = result.scalars().all()
            print(f"\nQuery with timezone-aware time (should fail): {len(should_fail_reminders)} reminders found")
            
            # 6. Test query with naive time
            # This should work correctly
            result = await db.execute(
                select(Reminder).where(
                    Reminder.remind_at <= now_naive_utc,
                    Reminder.is_sent == False
                )
            )
            naive_query_reminders = result.scalars().all()
            print(f"Query with naive time: {len(naive_query_reminders)} reminders found")
            
            # 7. Clean up test reminder
            await db.delete(test_reminder)
            await db.commit()
            print("\nTest reminder deleted successfully")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_timezone_handling())
