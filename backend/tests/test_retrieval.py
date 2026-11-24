from app.services import retrieval as rt


def top(query):
    hits = rt.retrieve(query)
    return hits[0].chunk if hits else None


def test_tokenizer_keeps_devanagari_words_whole():
    assert "किसान" in rt.tokenize("मैं किसान हूँ")
    assert "शेतकरी" in rt.tokenize("मी शेतकरी आहे")


def test_farmer_question_finds_pm_kisan():
    assert top("income support for farmers").ref_id == "pm-kisan"


def test_hindi_keyword_matches_scheme():
    assert top("किसान योजना").ref_id == "pm-kisan"


def test_marathi_keyword_matches_scheme():
    assert top("शेतकरी").ref_id == "pm-kisan"


def test_rights_question_finds_arrest_rights():
    assert top("what are my rights if police arrest me").ref_id == "rights-when-arrested"


def test_rti_question():
    assert top("how do I file an RTI application").ref_id == "right-to-information"


def test_irrelevant_question_is_not_relevant():
    hits = rt.retrieve("what is the best pizza topping")
    assert not rt.is_relevant(hits)


def test_every_hit_has_an_official_url():
    for q in ("pension", "loan", "health insurance", "free lawyer"):
        for h in rt.retrieve(q):
            assert h.chunk.url.startswith("https://")


def test_uploaded_document_chunks_are_searched_first():
    doc = {"id": "d1", "filename": "notice.txt", "text": "Penalty of Rs. 50 per month applies after 30/06/2026.\n\nObjections within 15 days."}
    hits = rt.retrieve("what is the penalty", doc)
    assert hits[0].chunk.kind == "uploaded"
    assert "Penalty" in hits[0].chunk.text


def test_chunk_text_respects_size():
    text = "\n".join(f"Line number {i} with some words to fill space." for i in range(200))
    chunks = rt.chunk_text(text, size=500, overlap=50)
    assert len(chunks) > 5
    assert all(len(c) <= 600 for c in chunks)
