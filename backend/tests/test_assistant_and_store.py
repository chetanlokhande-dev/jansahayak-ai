import asyncio
from pathlib import Path

from app.config import DATA_DIR, get_settings
from app.services import assistant
from app.services.store import Store


def run(coro):
    return asyncio.run(coro)


def test_settings_default_to_offline():
    assert get_settings().gemini_enabled is False


def test_offline_scheme_answer_is_grounded_with_official_source():
    out = run(assistant.answer("Tell me about income support for farmers", "en", [], None, get_settings()))
    assert out["mode"] == "offline"
    assert "PM-KISAN" in out["answer"] and "6,000" in out["answer"]
    assert out["sources"][0]["url"] == "https://pmkisan.gov.in/"
    assert "sample" in out["answer"].lower()


def test_offline_rights_answer():
    out = run(assistant.answer("what are my rights if arrested", "en", [], None, get_settings()))
    assert "24 hours" in out["answer"]
    assert out["sources"][0]["url"].startswith("https://")


def test_unknown_question_refuses_to_guess_and_lists_official_portals():
    out = run(assistant.answer("who will win the cricket world cup", "en", [], None, get_settings()))
    assert "will not guess" in out["answer"]
    assert out["unavailable"]
    assert any("myscheme.gov.in" in s["url"] for s in out["sources"])


def test_non_english_offline_flags_missing_translation():
    out = run(assistant.answer("किसान योजना", "hi", [], None, get_settings()))
    assert out["unavailable"] and "Gemini" in out["unavailable"][0]


def test_question_about_uploaded_document():
    doc = {"id": "d1", "filename": "notice.txt", "text": "The penalty is Rs. 50 per month after 30/06/2026."}
    out = run(assistant.answer("what is the penalty?", "en", [], doc, get_settings()))
    assert out["sources"][0]["kind"] == "uploaded"
    assert "Rs. 50" in out["answer"]


def test_offline_document_analysis_extracts_dates_amounts_and_documents():
    text = (DATA_DIR / "sample_documents" / "SAMPLE_gram_panchayat_notice.txt").read_text(encoding="utf-8")
    result = run(assistant.analyze_document(text, "notice.txt", "en", get_settings()))
    a = result["analysis"]
    assert result["mode"] == "offline" and result["notice"]
    assert any("30/06/2026" in x for x in a["important_dates_amounts"])
    assert any("Rs. 50" in x for x in a["important_dates_amounts"])
    assert any("Aadhaar" in x for x in a["required_documents"])
    assert a["summary"]


def test_parse_json_tolerates_code_fences():
    from app.services.gemini import parse_json

    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json("not json") is None


def test_translate_without_key_raises_friendly_error():
    import pytest
    from app.services.gemini import GeminiError

    with pytest.raises(GeminiError):
        run(assistant.translate("hello", "hi", get_settings()))


def test_store_conversations_documents_and_isolation(tmp_path: Path):
    s = Store(tmp_path / "t.db")
    c = s.create_conversation("client-a", "My question", "en")
    s.add_message(c, "user", "hi")
    s.add_message(c, "assistant", "hello", {"sources": [{"id": "S1"}]})
    msgs = s.messages(c)
    assert [m["role"] for m in msgs] == ["user", "assistant"] and msgs[1]["sources"][0]["id"] == "S1"

    d = s.add_document("client-a", "f.txt", "txt", "plain-text", "body", {"summary": "x"}, "en", [])
    assert s.get_document("client-a", d)["analysis"]["summary"] == "x"

    # another browser must never see these
    assert s.get_conversation("client-b", c) is None
    assert s.get_document("client-b", d) is None
    assert s.list_conversations("client-b") == []
    assert not s.delete_conversation("client-b", c)

    assert s.delete_conversation("client-a", c) and s.delete_document("client-a", d)
    assert s.list_conversations("client-a") == [] and s.list_documents("client-a") == []
