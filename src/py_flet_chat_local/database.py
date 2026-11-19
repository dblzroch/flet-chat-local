"""Database layer for flet-chat-local."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Self

from py_flet_chat_local.models import Conversation, Message


class Database:
    """SQLite storage for conversations and messages."""

    def __init__(self: Self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self: Self) -> None:
        """Create tables if they don't exist."""
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'Nova conversa',
                system_prompt TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conversation_id)
                REFERENCES conversations(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conv
            ON messages(conversation_id, created_at);
        """
        )
        self.conn.commit()

    def _now(self: Self) -> str:
        return datetime.now().isoformat()

    # --- Conversations ---

    def add_conversation(self: Self, conversation: Conversation) -> int:
        """Insert a conversation and return its new id."""
        cur = self.conn.execute(
            """
            INSERT INTO conversations (title, system_prompt, created_at)
            VALUES (?, ?, ?)
            """,
            (
                conversation.title,
                conversation.system_prompt,
                conversation.created_at or self._now(),
            ),
        )
        self.conn.commit()
        last_id = cur.lastrowid
        assert last_id is not None
        return int(last_id)

    def get_conversation(self: Self, conversation_id: int) -> Conversation | None:
        """Return a conversation with its messages, or None if not found."""
        row = self.conn.execute(
            """
            SELECT id, title, system_prompt, created_at
            FROM conversations WHERE id = ?
            """,
            (conversation_id,),
        ).fetchone()
        if row is None:
            return None
        messages = self.get_messages(conversation_id)
        return Conversation(
            id=row["id"],
            title=row["title"],
            system_prompt=row["system_prompt"],
            created_at=row["created_at"],
            messages=messages,
        )

    def get_conversations(self: Self) -> list[Conversation]:
        """Return all conversations ordered by created_at desc."""
        rows = self.conn.execute(
            """
            SELECT id, title, system_prompt, created_at
            FROM conversations
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [
            Conversation(
                id=r["id"],
                title=r["title"],
                system_prompt=r["system_prompt"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def update_conversation(self: Self, conversation: Conversation) -> bool:
        """Update a conversation. Returns True if a row was updated."""
        assert conversation.id is not None
        cur = self.conn.execute(
            """
            UPDATE conversations
            SET title = ?, system_prompt = ?
            WHERE id = ?
            """,
            (conversation.title, conversation.system_prompt, conversation.id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def delete_conversation(self: Self, conversation_id: int) -> bool:
        """Delete a conversation and its messages. Returns True if a row was deleted."""
        cur = self.conn.execute(
            "DELETE FROM conversations WHERE id = ?", (conversation_id,)
        )
        self.conn.commit()
        return cur.rowcount > 0

    # --- Messages ---

    def add_message(self: Self, message: Message) -> int:
        """Insert a message and return its new id."""
        cur = self.conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                message.conversation_id,
                message.role,
                message.content,
                message.created_at or self._now(),
            ),
        )
        self.conn.commit()
        last_id = cur.lastrowid
        assert last_id is not None
        return int(last_id)

    def get_messages(self: Self, conversation_id: int) -> list[Message]:
        """Return all messages for a conversation, ordered by created_at."""
        rows = self.conn.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        ).fetchall()
        return [
            Message(
                id=r["id"],
                conversation_id=r["conversation_id"],
                role=r["role"],
                content=r["content"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def delete_message(self: Self, message_id: int) -> bool:
        """Delete a message. Returns True if a row was deleted."""
        cur = self.conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def close(self: Self) -> None:
        """Close the database connection."""
        self.conn.close()
