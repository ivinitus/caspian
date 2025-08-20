from typing import List, Dict
from datetime import datetime
import tiktoken

class ShortTermMemory:
    def __init__(self, max_tokens: int = 2000):
        self.memory: List[Dict] = []
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def add(self, message: Dict):
        """Add a message to short term memory"""
        self.memory.append({
            **message,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_memory()
    
    def get_context(self, k: int = 5) -> List[Dict]:
        """Get last k messages"""
        return self.memory[-k:]
    
    def _trim_memory(self):
        """Trim memory if it exceeds max tokens"""
        current_tokens = 0
        messages_to_keep = []
        
        for message in reversed(self.memory):
            message_tokens = len(self.encoding.encode(str(message)))
            if current_tokens + message_tokens <= self.max_tokens:
                messages_to_keep.insert(0, message)
                current_tokens += message_tokens
            else:
                break
        
        self.memory = messages_to_keep
