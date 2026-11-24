import pytest

from app.services import eligibility as el


def result_for(profile, scheme_id):
    out = el.check_all(profile)
    return next(r for r in out["results"] if r["scheme_id"] == scheme_id)


def test_farmer_likely_eligible_for_pm_kisan():
    r = result_for({"owns_agricultural_land": True, "pays_income_tax": False}, "pm-kisan")
    assert r["status"] == "likely_eligible"
    assert r["official_url"].startswith("https://")


def test_income_tax_payer_excluded_from_pm_kisan():
    r = result_for({"owns_agricultural_land": True, "pays_income_tax": True}, "pm-kisan")
    assert r["status"] == "not_eligible"
    assert any(c["kind"] == "exclusion" and c["state"] == "not_met" for c in r["criteria"])


def test_missing_answers_need_more_info_not_a_guess():
    r = result_for({"owns_agricultural_land": True}, "pm-kisan")
    assert r["status"] == "needs_more_info"
    assert "pays_income_tax" in r["missing_fields"]


def test_empty_profile_never_claims_eligibility():
    out = el.check_all({})
    assert out["counts"]["likely_eligible"] == 0


def test_age_bounds_for_atal_pension():
    base = {"has_bank_account": True, "pays_income_tax": False}
    assert result_for({**base, "age": 30}, "atal-pension")["status"] == "likely_eligible"
    assert result_for({**base, "age": 41}, "atal-pension")["status"] == "not_eligible"
    assert result_for({**base, "age": 17}, "atal-pension")["status"] == "not_eligible"


def test_any_of_rule_for_pmjay():
    assert result_for({"age": 72}, "ab-pmjay")["status"] == "likely_eligible"
    assert result_for({"age": 30, "pmjay_listed": True}, "ab-pmjay")["status"] == "likely_eligible"
    assert result_for({"age": 30, "pmjay_listed": False}, "ab-pmjay")["status"] == "not_eligible"
    assert result_for({"age": 30}, "ab-pmjay")["status"] == "needs_more_info"


def test_results_sorted_best_first():
    out = el.check_all({"age": 72, "owns_agricultural_land": True, "pays_income_tax": False})
    order = {"likely_eligible": 0, "needs_more_info": 1, "not_eligible": 2}
    ranks = [order[r["status"]] for r in out["results"]]
    assert ranks == sorted(ranks)


@pytest.mark.parametrize("bad", [{"age": "abc"}, {"age": -1}, {"age": 500}, {"residence": "moon"}, {"pays_income_tax": "maybe"}, {"hacker": 1}])
def test_invalid_input_rejected(bad):
    with pytest.raises(el.ProfileError):
        el.check_all(bad)


def test_string_booleans_accepted():
    assert el.normalize_profile({"pays_income_tax": "false"}) == {"pays_income_tax": False}


def test_fields_available_in_all_languages():
    for lang in ("en", "hi", "mr"):
        fields = el.fields_for_language(lang)
        assert len(fields) == len(el.FIELDS)
        assert all(f["label"] for f in fields)
    assert el.fields_for_language("hi")[0]["label"] != el.fields_for_language("en")[0]["label"]


def test_disclaimer_present_and_no_approval_language():
    out = el.check_all({"age": 30})
    assert "not a decision or a guarantee" in out["disclaimer"]
    assert all("approved" not in r["summary"].lower() for r in out["results"])
