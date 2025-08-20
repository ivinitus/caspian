"""
Handles user identification and loyalty settings.
"""
from typing import Optional

CREATOR_ID = 1  # Vinitus's user ID
CREATOR_DISCORD_ID = 1093918301035429938  # Vinitus's Discord ID

def is_creator(user_id: int, platform: str = "api") -> bool:
    """Check if the user is Vinitus."""
    if platform == "discord":
        return user_id == CREATOR_DISCORD_ID
    return user_id == CREATOR_ID

def get_loyalty_level(user_id: int, platform: str = "api") -> str:
    """Determine loyalty level for user interactions."""
    if is_creator(user_id, platform):
        return "creator"
    return "standard"

def get_user_title(user_id: int, username: Optional[str] = None, platform: str = "api") -> str:
    """Get the appropriate title for addressing the user."""
    if is_creator(user_id, platform):
        return "Sir"
    if username:
        return f"Mr./Ms. {username}"
    return "Sir/Madam"
