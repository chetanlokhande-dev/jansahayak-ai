"""End-to-end API tests. They need FastAPI + httpx installed (see requirements.txt)."""
import io

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

CID = "test-client-0123456789abcdef"
H = {"X-Client-Id": CID}
client = TestClient(app)


def test_health_and_meta():
    assert client.get("/api/health").json()["status"] == "ok"
    meta = client.get("/api/meta").json()
    assert {l["code"] for l in meta["languages"]} == {"en", "hi", "mr"}
    assert meta["ai_mode"] == "offline"


def test_client_id_required():
    assert client.get("/api/history").status_code == 400
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 400


def test_schemes_and_filters():
    assert len(client.get("/api/schemes").json()["schemes"]) >= 5
    only = client.get("/api/schemes", params={"q": "pension"}).json()["schemes"]
    assert only and all("pension" in (s["name"] + s["summary"]).lower() or "pension" in s["keywords"] for s in only)
    assert client.get("/api/schemes/nope").status_code == 404


def test_chat_flow_with_followup_and_history():
    r = client.post("/api/chat", json={"message": "income support for farmers", "language": "en"}, headers=H).json()
    assert "PM-KISAN" in r["answer"] and r["sources"][0]["url"].startswith("https://")
    cid = r["conversation_id"]
    r2 = client.post("/api/chat", json={"message": "what documents are needed", "conversation_id": cid}, headers=H)
    assert r2.status_code == 200
    conv = client.get(f"/api/history/conversations/{cid}", headers=H).json()
    assert len(conv["messages"]) == 4
    # another browser cannot read it
    assert client.get(f"/api/history/conversations/{cid}", headers={"X-Client-Id": "other-client-0123456789abc"}).status_code == 404
    assert client.delete(f"/api/history/conversations/{cid}", headers=H).status_code == 200


def test_chat_validation():
    assert client.post("/api/chat", json={"message": ""}, headers=H).status_code == 422
    assert client.post("/api/chat", json={"message": "hi", "language": "xx"}, headers=H).status_code == 400
    assert client.post("/api/chat", json={"message": "hi", "conversation_id": "missing"}, headers=H).status_code == 404


def test_document_upload_then_ask_about_it():
    txt = b"Pay the water charges before 30/06/2026. A penalty of Rs. 50 per month applies. Bring your Aadhaar card."
    up = client.post("/api/documents", files={"file": ("notice.txt", io.BytesIO(txt), "text/plain")}, data={"language": "en"}, headers=H)
    assert up.status_code == 200, up.text
    body = up.json()
    assert any("30/06/2026" in x for x in body["analysis"]["important_dates_amounts"])
    ans = client.post("/api/chat", json={"message": "what is the penalty?", "document_id": body["document"]["id"]}, headers=H).json()
    assert ans["sources"][0]["kind"] == "uploaded" and "Rs. 50" in ans["answer"]


def test_upload_rejects_bad_type_and_oversize():
    bad = client.post("/api/documents", files={"file": ("x.exe", io.BytesIO(b"MZ"), "application/octet-stream")}, headers=H)
    assert bad.status_code == 422
    big = client.post("/api/documents", files={"file": ("big.txt", io.BytesIO(b"a" * (11 * 1024 * 1024)), "text/plain")}, headers=H)
    assert big.status_code == 413


def test_sample_documents():
    names = client.get("/api/sample-documents").json()["documents"]
    assert names
    ok = client.post(f"/api/sample-documents/{names[0]}", headers=H)
    assert ok.status_code == 200
    assert client.post("/api/sample-documents/..%2Fconfig.py", headers=H).status_code == 404


def test_eligibility_endpoint():
    fields = client.get("/api/eligibility/fields", params={"lang": "mr"}).json()["fields"]
    assert fields and fields[0]["id"] == "age"
    ok = client.post("/api/eligibility/check", json={"profile": {"owns_agricultural_land": True, "pays_income_tax": False}}, headers=H).json()
    assert any(r["scheme_id"] == "pm-kisan" and r["status"] == "likely_eligible" for r in ok["results"])
    assert client.post("/api/eligibility/check", json={"profile": {"age": "abc"}}, headers=H).status_code == 422


def test_translate_needs_gemini():
    assert client.post("/api/translate", json={"text": "hello", "target_language": "hi"}, headers=H).status_code == 503


def test_rights():
    assert len(client.get("/api/rights").json()["rights"]) >= 5
