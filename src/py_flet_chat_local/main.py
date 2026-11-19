"""Flet UI for flet-chat-local.  # pragma: no cover"""

from pathlib import Path

import flet as ft

from py_flet_chat_local.client import OllamaClient
from py_flet_chat_local.database import Database
from py_flet_chat_local.models import Conversation, Message


def app_main(page: ft.Page) -> None:  # pragma: no cover
    """Build the Flet UI."""
    page.title = "py-chat-local"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 700  # type: ignore[attr-defined]
    page.window_height = 700  # type: ignore[attr-defined]

    db = Database(Path.home() / ".local" / "share" / "flet-chat-local" / "chat.db")
    ollama = OllamaClient()

    # --- UI state ---
    model_dropdown = ft.Dropdown(
        label="Modelo",
        options=[],
        width=200,
    )
    system_prompt_field = ft.TextField(
        label="System prompt",
        value="",
        multiline=True,
        min_lines=2,
        max_lines=4,
        width=400,
    )
    message_field = ft.TextField(
        label="Sua mensagem",
        multiline=False,
        width=450,
        shift_enter=True,
        on_submit=lambda _: send_message(),
    )

    chat_column = ft.Column(expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)
    conversations_list = ft.ListView(expand=False, spacing=4, height=200)

    current_conversation_id: int | None = None

    def refresh_models() -> None:
        """Load available models from Ollama."""
        try:
            models = ollama.list_models()
            model_dropdown.options = [ft.dropdown.Option(m) for m in models]
            if models:
                model_dropdown.value = models[0]
        except Exception:  # Ollama may not be running
            model_dropdown.options = []
        page.update()

    def refresh_conversations() -> None:
        """Load conversations list."""
        conversations = db.get_conversations()
        conversations_list.controls.clear()
        for c in conversations:
            conversations_list.controls.append(
                ft.ListTile(
                    title=ft.Text(c.title, weight=ft.FontWeight.W_500),
                    subtitle=ft.Text(c.created_at[:10], size=11),
                    on_click=lambda e, cid=c.id: load_conversation(cid),
                )
            )
        page.update()

    def load_conversation(conversation_id: int) -> None:
        """Load a conversation into the chat view."""
        nonlocal current_conversation_id
        current_conversation_id = conversation_id
        conv = db.get_conversation(conversation_id)
        if conv is None:
            return
        system_prompt_field.value = conv.system_prompt
        chat_column.controls.clear()
        for m in conv.messages:
            bubble_color = (
                ft.colors.BLUE_100 if m.role == "user" else ft.colors.GREY_200
            )
            align = (
                ft.MainAxisAlignment.END
                if m.role == "user"
                else ft.MainAxisAlignment.START
            )
            chat_column.controls.append(
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(m.content, selectable=True),
                            bgcolor=bubble_color,
                            padding=10,
                            border_radius=10,
                        )
                    ],
                    alignment=align,
                )
            )
        page.update()

    def new_conversation(e: ft.ControlEvent) -> None:
        """Create a new empty conversation."""
        nonlocal current_conversation_id
        conv_id = db.add_conversation(Conversation(title="Nova conversa"))
        current_conversation_id = conv_id
        system_prompt_field.value = ""
        chat_column.controls.clear()
        message_field.value = ""
        refresh_conversations()
        page.update()

    def send_message() -> None:
        """Send a message and stream the response."""
        if not message_field.value or not current_conversation_id:
            return
        if not model_dropdown.value:
            page.snack_bar = ft.SnackBar(ft.Text("Selecione um modelo"))  # type: ignore[attr-defined]
            page.snack_bar.open = True  # type: ignore[attr-defined]
            page.update()
            return

        user_text = message_field.value
        message_field.value = ""

        # Save user message
        db.add_message(
            Message(
                conversation_id=current_conversation_id,
                role="user",
                content=user_text,
            )
        )

        # Add user bubble
        chat_column.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(user_text, selectable=True),
                        bgcolor=ft.colors.BLUE_100,
                        padding=10,
                        border_radius=10,
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            )
        )

        # Assistant bubble (streaming)
        assistant_text = ft.Text("", selectable=True)
        assistant_bubble = ft.Container(
            content=assistant_text,
            bgcolor=ft.colors.GREY_200,
            padding=10,
            border_radius=10,
        )
        chat_column.controls.append(
            ft.Row([assistant_bubble], alignment=ft.MainAxisAlignment.START)
        )
        page.update()

        # Build message history
        conv = db.get_conversation(current_conversation_id)
        if conv is None:
            return
        history = [{"role": m.role, "content": m.content} for m in conv.messages]
        history.append({"role": "user", "content": user_text})

        # Stream response
        try:
            for chunk in ollama.chat_stream(
                model=str(model_dropdown.value),
                messages=history,
                system_prompt=system_prompt_field.value or "",
            ):
                assistant_text.value += chunk
                assistant_text.update()
        except Exception as exc:  # Ollama not running or error
            assistant_text.value = f"Erro: {exc}"

        # Save assistant message
        db.add_message(
            Message(
                conversation_id=current_conversation_id,
                role="assistant",
                content=assistant_text.value,
            )
        )
        page.update()

    def save_system_prompt(e: ft.ControlEvent) -> None:
        """Save the system prompt for the current conversation."""
        if current_conversation_id is None:
            return
        conv = db.get_conversation(current_conversation_id)
        if conv is None:
            return
        assert conv.id is not None
        db.update_conversation(
            Conversation(
                id=conv.id,
                title=conv.title,
                system_prompt=system_prompt_field.value or "",
            )
        )
        page.snack_bar = ft.SnackBar(ft.Text("System prompt salvo"))  # type: ignore[attr-defined]
        page.snack_bar.open = True  # type: ignore[attr-defined]
        page.update()

    # --- Layout ---
    page.add(
        ft.Text("Chat Local (Ollama)", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row(
            [
                model_dropdown,
                ft.ElevatedButton(
                    "Atualizar modelos", on_click=lambda _: refresh_models()
                ),
                ft.ElevatedButton("Nova conversa", on_click=new_conversation),
            ],
            wrap=True,
        ),
        ft.Row(
            [system_prompt_field],
            wrap=True,
        ),
        ft.ElevatedButton("Salvar prompt", on_click=save_system_prompt),
        ft.Divider(),
        ft.Text("Conversas", size=16, weight=ft.FontWeight.BOLD),
        conversations_list,
        ft.Divider(),
        ft.Column(
            [chat_column],
            expand=True,
            height=400,
        ),
        ft.Row(
            [
                message_field,
                ft.ElevatedButton("Enviar", on_click=lambda _: send_message()),
            ],
            wrap=True,
        ),
    )

    refresh_models()
    refresh_conversations()
