from typing import TypedDict, Any, List, Dict, Optional

class Message(TypedDict):
    role: str       # "user", "assistant", "system", "tool"
    content: str

class AgentState(TypedDict):
    session_id: str
    user_id: str
    user_name: Optional[str]
    input_text: str
    conversation: List[Message]
    retrieved_memories: List[str]
    
    intent: Optional[str]               # e.g., "create_calendar_event", "set_reminder", "search_web"
    entities: Dict[str, Any]             # attendee, date, time, duration, query, text
    missing_slots: List[str]             # e.g., ["time", "attendee"]
    
    requires_confirmation: bool          # True if side-effecting action needs user confirmation
    pending_confirmation: bool           # True if waiting for user yes/no
    confirmation_given: Optional[bool]   # True = confirmed, False = rejected
    
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    
    final_response: Optional[str]
    is_interrupted: bool
    error: Optional[str]
