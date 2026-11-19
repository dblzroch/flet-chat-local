"""Domain models for flet-chat-local."""

from dataclasses import dataclass, field


@dataclass
class Message:
    """A chat message."""

    id: int | None = None
    conversation_id: int = 0
    role: str = ""  # "user" or "assistant"
    content: str = ""
    created_at: str = ""  # ISO format


@dataclass
class Conversation:
    """A chat conversation."""

    id: int | None = None
    title: str = ""
    system_prompt: str = ""
    created_at: str = ""  # ISO format
    messages: list[Message] = field(default_factory=list)


@dataclass
class Model:
    """An Ollama model."""

    name: str = ""
    size: int = 0
