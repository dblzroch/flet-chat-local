"""Tests for flet-chat-local database, client and models."""

from py_flet_chat_local.client import OllamaClient
from py_flet_chat_local.database import Database
from py_flet_chat_local.models import Conversation, Message, Model


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------
def test_message_defaults():
    m = Message(conversation_id=1, role="user", content="Olá")
    assert m.conversation_id == 1
    assert m.role == "user"
    assert m.content == "Olá"
    assert m.id is None


def test_conversation_defaults():
    c = Conversation(title="Minha conversa", system_prompt="Seja útil")
    assert c.title == "Minha conversa"
    assert c.system_prompt == "Seja útil"
    assert c.messages == []
    assert c.id is None


def test_model_defaults():
    mo = Model(name="llama3.2", size=2000000)
    assert mo.name == "llama3.2"
    assert mo.size == 2000000


# ------------------------------------------------------------------
# Database: conversations
# ------------------------------------------------------------------
def test_add_and_get_conversation(tmp_path):
    db = Database(tmp_path / "test.db")
    rid = db.add_conversation(Conversation(title="Teste", system_prompt="Sistema"))
    assert rid == 1

    c = db.get_conversation(1)
    assert c is not None
    assert c.title == "Teste"
    assert c.system_prompt == "Sistema"


def test_get_conversation_not_found(tmp_path):
    db = Database(tmp_path / "test.db")
    assert db.get_conversation(999) is None


def test_get_conversations_ordered(tmp_path):
    db = Database(tmp_path / "test.db")
    db.add_conversation(Conversation(title="A", system_prompt=""))
    db.add_conversation(Conversation(title="B", system_prompt=""))

    convs = db.get_conversations()
    assert len(convs) == 2
    assert convs[0].title == "B"


def test_update_conversation(tmp_path):
    db = Database(tmp_path / "test.db")
    rid = db.add_conversation(Conversation(title="Velho", system_prompt=""))
    conv_update = Conversation(id=rid, title="Novo", system_prompt="Novo prompt")
    assert db.update_conversation(conv_update) is True
    c = db.get_conversation(rid)
    assert c is not None
    assert c.title == "Novo"
    assert c.system_prompt == "Novo prompt"


def test_delete_conversation(tmp_path):
    db = Database(tmp_path / "test.db")
    rid = db.add_conversation(Conversation(title="Temp", system_prompt=""))
    assert db.delete_conversation(rid) is True
    assert db.get_conversations() == []


def test_delete_conversation_cascades_to_messages(tmp_path):
    db = Database(tmp_path / "test.db")
    cid = db.add_conversation(Conversation(title="C", system_prompt=""))
    db.add_message(Message(conversation_id=cid, role="user", content="Oi"))

    assert db.delete_conversation(cid) is True
    msgs = db.get_messages(cid)
    assert msgs == []


# ------------------------------------------------------------------
# Database: messages
# ------------------------------------------------------------------
def test_add_and_get_message(tmp_path):
    db = Database(tmp_path / "test.db")
    cid = db.add_conversation(Conversation(title="C", system_prompt=""))
    rid = db.add_message(Message(conversation_id=cid, role="user", content="Ola"))
    assert rid == 1

    msgs = db.get_messages(cid)
    assert len(msgs) == 1
    assert msgs[0].role == "user"
    assert msgs[0].content == "Ola"


# ------------------------------------------------------------------
# Client: OllamaClient (mocked HTTP)
# ------------------------------------------------------------------
def test_list_models(monkeypatch):
    import httpx
    import respx

    with respx.mock:
        route = respx.get("http://localhost:11434/api/tags")
        route.mock(
            return_value=httpx.Response(
                200,
                json={"models": [{"name": "llama3.2"}, {"name": "codellama"}]},
            )
        )
        client = OllamaClient(base_url="http://localhost:11434")
        models = client.list_models()
        assert models == ["llama3.2", "codellama"]


def test_chat_stream(monkeypatch):
    import json

    import httpx
    import respx

    lines = [
        json.dumps({"message": {"content": "Olá"}, "done": False}),
        json.dumps({"message": {"content": " mundo"}, "done": True}),
    ]
    body = "\n".join(lines)

    with respx.mock:
        route = respx.post("http://localhost:11434/api/chat")
        route.mock(return_value=httpx.Response(200, text=body))
        client = OllamaClient(base_url="http://localhost:11434")
        chunks = list(
            client.chat_stream(
                model="llama3.2",
                messages=[{"role": "user", "content": "Oi"}],
                system_prompt="",
            )
        )
        assert chunks == ["Olá", " mundo"]


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def test_cli_main(monkeypatch):
    """Test that cli.main calls ft.app with the right target."""
    import py_flet_chat_local.cli as cli_mod

    called = {}

    def fake_app(target):
        called["target"] = target

    monkeypatch.setattr(cli_mod, "ft_app", fake_app)
    cli_mod.main()
    assert callable(called.get("target"))
