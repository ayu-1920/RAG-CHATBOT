from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

class ConversationMemory:
    """
    Manages conversation context for multi-turn dialogues.
    Stores recent messages and provides context for retrieval.
    """
    
    def __init__(self, max_messages: int = 10, max_age_minutes: int = 30):
        self.max_messages = max_messages
        self.max_age = timedelta(minutes=max_age_minutes)
        self.conversations: Dict[str, List[Dict]] = {}
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        
        self.conversations[session_id].append(message)
        self._cleanup_old_messages(session_id)
    
    def get_recent_context(self, session_id: str, max_context: int = 3) -> str:
        """
        Get recent conversation context as a formatted string.
        This helps maintain context across multiple turns.
        """
        if session_id not in self.conversations:
            return ""
        
        recent_messages = self.conversations[session_id][-max_context:]
        if not recent_messages:
            return ""
        
        context_parts = []
        for msg in recent_messages:
            if msg["role"] == "user":
                context_parts.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                context_parts.append(f"Assistant: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get full conversation history for a session."""
        return self.conversations.get(session_id, [])
    
    def _cleanup_old_messages(self, session_id: str):
        """Remove old messages to prevent memory bloat."""
        if session_id not in self.conversations:
            return
        
        now = datetime.now()
        # Remove messages older than max_age
        self.conversations[session_id] = [
            msg for msg in self.conversations[session_id]
            if now - msg["timestamp"] < self.max_age
        ]
        
        # Keep only the most recent max_messages
        if len(self.conversations[session_id]) > self.max_messages:
            self.conversations[session_id] = self.conversations[session_id][-self.max_messages:]
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs."""
        return list(self.conversations.keys())


# Global conversation memory instance
conversation_memory = ConversationMemory()