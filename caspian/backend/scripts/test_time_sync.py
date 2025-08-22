import asyncio
from app.core.time_utils import (
    get_current_time, 
    get_current_time_utc, 
    format_time, 
    sync_time,
    is_time_synced,
    get_time_offset,
    get_time_drift_rate,
    force_time_sync
)
import time
from datetime import datetime, timezone

async def test_time_sync():
    """Test the time synchronization functions."""
    # Check if time is already synced
    print(f"Time synced: {is_time_synced()}")
    
    # Get current system time
    system_time = datetime.now().astimezone(timezone.utc)
    print(f"System time (UTC): {system_time}")
    
    # Force a time synchronization
    print("Forcing time sync...")
    sync_success = await force_time_sync()
    print(f"Sync success: {sync_success}")
    
    # Get synchronized time
    sync_time_utc = get_current_time_utc()
    print(f"Synchronized time (UTC): {sync_time_utc}")
    
    # Calculate the difference
    time_offset = get_time_offset()
    print(f"Time offset: {time_offset:.3f} seconds")
    
    # Get drift rate
    drift_rate = get_time_drift_rate()
    print(f"Estimated drift rate: {drift_rate:.6f} seconds per hour")
    
    # Get current time in different timezones
    ist_time = get_current_time("Asia/Kolkata")
    print(f"Current time (IST): {format_time(ist_time)}")
    
    jst_time = get_current_time("Asia/Tokyo")
    print(f"Current time (JST): {format_time(jst_time)}")
    
    # Wait for a short time and check again to see the drift compensation
    print("\nWaiting 5 seconds to test drift compensation...")
    await asyncio.sleep(5)
    
    # Get updated time
    new_sync_time = get_current_time_utc()
    print(f"Updated time (UTC): {new_sync_time}")
    print(f"Time elapsed: {(new_sync_time - sync_time_utc).total_seconds():.3f} seconds")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_time_sync())
