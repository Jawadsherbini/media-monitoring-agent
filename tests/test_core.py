"""Fast tests of the pure logic. No network, no API calls, no database writes.  Run: python -m pytest -q"""
from agent.ingest import normalise_title, make_id, clean_text
from agent.classify import is_high_risk, SECTOR_THEMES
from agent.briefing import check_citations
from agent.ask import keywords


def test_normalise_strips_outlet_suffix_and_punctuation():
    a = normalise_title("Saudi tourism up 18% - Arab News")
    b = normalise_title("Saudi Tourism Up 18%!")
    assert a == b == "saudi tourism up 18"


def test_same_story_same_id_across_outlets():
    assert make_id("NEOM Stadium shelved - Reuters") == make_id("NEOM stadium shelved - Gulf News")


def test_clean_text_removes_html():
    assert clean_text("<p>Hello &amp; <b>world</b></p>") == "Hello & world"


def test_high_risk_requires_negative_high_and_sector_theme():
    assert is_high_risk({"theme": "reputational_risk", "sentiment": "negative", "priority": "high"})
    assert is_high_risk({"theme": "aviation_visa_entry", "sentiment": "negative", "priority": "high"})
    assert not is_high_risk({"theme": "not_relevant", "sentiment": "negative", "priority": "high"})
    assert not is_high_risk({"theme": "reputational_risk", "sentiment": "neutral", "priority": "high"})
    assert not is_high_risk({"theme": "reputational_risk", "sentiment": "negative", "priority": "medium"})
    assert "not_relevant" not in SECTOR_THEMES


def test_citation_check_flags_invented_sources():
    result = check_citations("Claim one [1]. Claim two [3][7].", n_items=3)
    assert result["cited"] == [1, 3, 7]
    assert result["invalid"] == [7]
    assert result["uncited_items"] == [2]


def test_keywords_drop_filler_words():
    assert keywords("What has been written about visa changes this week and by whom?") == ["visa", "changes"]
