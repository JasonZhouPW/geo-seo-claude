import pytest
import sys
sys.path.insert(0, "scripts")
from entity_analyzer import extract_named_entities, analyze_internal_duplicates, compute_entity_graph_score
from bs4 import BeautifulSoup


def test_extract_person_entities():
    text = "Dr. Jane Smith founded TechCorp with 20 years of experience."
    entities = extract_named_entities(text)
    labels = [e["label"] for e in entities]
    assert "PERSON" in labels


def test_extract_org_entities():
    text = "Google Inc. and Microsoft Corp. are leading technology companies."
    entities = extract_named_entities(text)
    labels = [e["label"] for e in entities]
    assert "ORG" in labels


def test_internal_duplicate_detection():
    html = """
    <html><body>
        <p>Search engine optimization is crucial for online visibility. It helps websites rank higher in search results.</p>
        <p>SEO is crucial for online visibility. Search engine optimization helps websites rank higher in search results.</p>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = analyze_internal_duplicates(soup)
    assert result["duplicate_score"] < 100
    assert len(result["duplicates_found"]) > 0


def test_no_duplicates_when_few_paragraphs():
    html = "<html><body><p>Only one paragraph here with enough words to be considered.</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    result = analyze_internal_duplicates(soup)
    assert result["duplicate_score"] == 100


def test_entity_graph_score():
    entity_rel = {
        "entity_diversity_score": 50,
        "relationship_density_score": 40,
    }
    brand_cooc = {"industry_terms_found": 5}
    result = compute_entity_graph_score(entity_rel, brand_cooc)
    assert "entity_graph_score" in result
    assert 0 <= result["entity_graph_score"] <= 100
