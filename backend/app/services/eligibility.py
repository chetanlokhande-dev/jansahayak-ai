"""Structured, rule-based eligibility checking.

For every criterion the result is one of:
  met      - the user's answer satisfies it          (verified against the rule)
  not_met  - the user's answer fails it
  unknown  - the user has not answered / is not sure (we say so; we never guess)

The overall status is never "approved". Even a best case is "likely eligible", with a
reminder that only the scheme authority decides.
"""
from __future__ import annotations

from typing import Any

from . import knowledge

MET, NOT_MET, UNKNOWN = "met", "not_met", "unknown"

DISCLAIMER = (
    "This is a guide based on the details you entered and simplified sample scheme data. "
    "It is not a decision or a guarantee. Only the scheme authority can confirm eligibility, "
    "so please verify on the official source before applying."
)

YES_NO = [
    {"value": "true", "label": {"en": "Yes", "hi": "हाँ", "mr": "होय"}},
    {"value": "false", "label": {"en": "No", "hi": "नहीं", "mr": "नाही"}},
]

# Question definitions (single source of truth for the step-by-step checker).
FIELDS: list[dict[str, Any]] = [
    {
        "id": "age", "type": "number", "min": 0, "max": 120,
        "label": {"en": "How old are you?", "hi": "आपकी उम्र कितनी है?", "mr": "तुमचे वय किती आहे?"},
    },
    {
        "id": "residence", "type": "choice",
        "label": {"en": "Do you live in a rural or urban area?", "hi": "आप ग्रामीण क्षेत्र में रहते हैं या शहरी?", "mr": "तुम्ही ग्रामीण भागात राहता की शहरी?"},
        "options": [
            {"value": "rural", "label": {"en": "Rural (village)", "hi": "ग्रामीण (गाँव)", "mr": "ग्रामीण (गाव)"}},
            {"value": "urban", "label": {"en": "Urban (town / city)", "hi": "शहरी (कस्बा / शहर)", "mr": "शहरी (शहर)"}},
        ],
    },
    {
        "id": "has_bank_account", "type": "bool",
        "label": {"en": "Do you have a savings bank account?", "hi": "क्या आपका बैंक बचत खाता है?", "mr": "तुमचे बँकेत बचत खाते आहे का?"},
    },
    {
        "id": "owns_agricultural_land", "type": "bool",
        "label": {"en": "Does your family own farm land (cultivable land)?", "hi": "क्या आपके परिवार के पास खेती की ज़मीन है?", "mr": "तुमच्या कुटुंबाच्या नावावर शेतजमीन आहे का?"},
    },
    {
        "id": "pays_income_tax", "type": "bool",
        "label": {"en": "Do you pay income tax?", "hi": "क्या आप आयकर (इनकम टैक्स) भरते हैं?", "mr": "तुम्ही आयकर भरता का?"},
    },
    {
        "id": "has_girl_child_under_10", "type": "bool",
        "label": {"en": "Do you have a girl child under 10 years of age?", "hi": "क्या आपकी 10 साल से कम उम्र की बेटी है?", "mr": "तुम्हाला 10 वर्षांखालील मुलगी आहे का?"},
    },
    {
        "id": "has_nonfarm_business", "type": "bool",
        "label": {"en": "Do you run, or plan to start, a small business (shop, workshop, service)?", "hi": "क्या आप छोटा व्यवसाय (दुकान, कारखाना, सेवा) चलाते हैं या शुरू करना चाहते हैं?", "mr": "तुम्ही लहान व्यवसाय (दुकान, कार्यशाळा, सेवा) चालवता किंवा सुरू करू इच्छिता का?"},
    },
    {
        "id": "willing_manual_work", "type": "bool",
        "label": {"en": "Are you willing to do unskilled manual work for wages?", "hi": "क्या आप मज़दूरी पर अकुशल शारीरिक काम करने को तैयार हैं?", "mr": "तुम्ही मजुरीवर अकुशल शारीरिक काम करण्यास तयार आहात का?"},
    },
    {
        "id": "pmjay_listed", "type": "bool",
        "label": {"en": "Is your family listed as eligible under Ayushman Bharat PM-JAY? (Not sure? Choose 'Not sure'.)", "hi": "क्या आपका परिवार आयुष्मान भारत PM-JAY में पात्र के रूप में सूचीबद्ध है? (पता नहीं तो 'पक्का नहीं' चुनें।)", "mr": "तुमचे कुटुंब आयुष्मान भारत PM-JAY मध्ये पात्र म्हणून नोंदलेले आहे का? (माहीत नसल्यास 'खात्री नाही' निवडा.)"},
    },
]

_FIELD_MAP = {f["id"]: f for f in FIELDS}


class ProfileError(ValueError):
    pass


def fields_for_language(lang: str) -> list[dict[str, Any]]:
    """Return question definitions with labels in one language (falls back to English)."""
    out = []
    for f in FIELDS:
        item: dict[str, Any] = {"id": f["id"], "type": f["type"], "label": f["label"].get(lang, f["label"]["en"])}
        if f["type"] == "number":
            item["min"], item["max"] = f["min"], f["max"]
        if f["type"] == "choice":
            item["options"] = [{"value": o["value"], "label": o["label"].get(lang, o["label"]["en"])} for o in f["options"]]
        if f["type"] == "bool":
            item["options"] = [{"value": o["value"], "label": o["label"].get(lang, o["label"]["en"])} for o in YES_NO]
        out.append(item)
    return out


def normalize_profile(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalise user input. Missing or null answers mean 'unknown'."""
    if not isinstance(raw, dict):
        raise ProfileError("profile must be an object")
    profile: dict[str, Any] = {}
    for key, value in raw.items():
        field = _FIELD_MAP.get(key)
        if field is None:
            raise ProfileError(f"unknown field: {key}")
        if value is None or value == "":
            continue
        if field["type"] == "number":
            try:
                num = int(value)
            except (TypeError, ValueError):
                raise ProfileError(f"{key} must be a whole number") from None
            if not field["min"] <= num <= field["max"]:
                raise ProfileError(f"{key} must be between {field['min']} and {field['max']}")
            profile[key] = num
        elif field["type"] == "bool":
            if isinstance(value, bool):
                profile[key] = value
            elif str(value).lower() in ("true", "false"):
                profile[key] = str(value).lower() == "true"
            else:
                raise ProfileError(f"{key} must be yes or no")
        else:  # choice
            allowed = {o["value"] for o in field["options"]}
            if value not in allowed:
                raise ProfileError(f"{key} must be one of {sorted(allowed)}")
            profile[key] = value
    return profile


def _compare(op: str, actual: Any, expected: Any) -> bool:
    if op == "eq":
        return actual == expected
    if op == "gte":
        return actual >= expected
    if op == "lte":
        return actual <= expected
    if op == "in":
        return actual in expected
    raise ValueError(f"unsupported operator: {op}")


def eval_rule(rule: dict[str, Any], profile: dict[str, Any]) -> tuple[str, list[str]]:
    """Evaluate one rule. Returns (state, missing_field_ids)."""
    if "any_of" in rule:
        results = [eval_rule(r, profile) for r in rule["any_of"]]
        states = [s for s, _ in results]
        if MET in states:
            return MET, []
        missing = sorted({m for _, ms in results for m in ms})
        if all(s == NOT_MET for s in states):
            return NOT_MET, []
        return UNKNOWN, missing
    field = rule["field"]
    if field not in profile:
        return UNKNOWN, [field]
    return (MET if _compare(rule["op"], profile[field], rule["value"]) else NOT_MET), []


def evaluate_scheme(scheme: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    criteria_out: list[dict[str, Any]] = []
    missing: set[str] = set()
    any_not_met = False
    any_unknown = False

    for rule in scheme.get("criteria", []):
        state, miss = eval_rule(rule, profile)
        criteria_out.append({"label": rule["label"], "state": state, "kind": "requirement"})
        missing.update(miss)
        any_not_met |= state == NOT_MET
        any_unknown |= state == UNKNOWN

    for rule in scheme.get("exclusions", []):
        # The exclusion fires when its rule is MET; show it to the user as a positive requirement.
        state, miss = eval_rule(rule, profile)
        shown = {MET: NOT_MET, NOT_MET: MET, UNKNOWN: UNKNOWN}[state]
        criteria_out.append({"label": rule["label"], "state": shown, "kind": "exclusion"})
        missing.update(miss)
        any_not_met |= shown == NOT_MET
        any_unknown |= shown == UNKNOWN

    if any_not_met:
        status, summary = "not_eligible", "Based on your answers, you do not appear to meet at least one listed requirement."
    elif any_unknown:
        status, summary = "needs_more_info", "We need a few more details to say whether you may qualify."
    else:
        status, summary = "likely_eligible", "You appear to meet the listed requirements. Please verify officially before applying."

    return {
        "scheme_id": scheme["id"],
        "scheme_name": scheme["name"],
        "category": scheme["category"],
        "status": status,
        "summary": summary,
        "criteria": criteria_out,
        "missing_fields": sorted(missing),
        "official_url": scheme["official_url"],
        "source_name": scheme["source_name"],
        "data_status": scheme.get("data_status", "sample"),
    }


_ORDER = {"likely_eligible": 0, "needs_more_info": 1, "not_eligible": 2}


def check_all(raw_profile: dict[str, Any]) -> dict[str, Any]:
    profile = normalize_profile(raw_profile)
    results = [evaluate_scheme(s, profile) for s in knowledge.list_schemes()]
    results.sort(key=lambda r: (_ORDER[r["status"]], r["scheme_name"]))
    counts = {k: sum(1 for r in results if r["status"] == k) for k in _ORDER}
    return {"profile": profile, "results": results, "counts": counts, "disclaimer": DISCLAIMER}
