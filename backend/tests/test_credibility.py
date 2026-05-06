"""Tests for credibility services — GST validation, name normalisation, graph detection, similarity, DBSCAN."""
import re
import pytest
import networkx as nx
import numpy as np


# GST validation
def validate_gst(gst: str) -> bool:
    if len(gst) != 15:
        return False
    try:
        state_code = int(gst[:2])
        if state_code < 1 or state_code > 37:
            return False
    except ValueError:
        return False
    if gst[13] != 'Z':
        return False
    return True


# Company name normalisation
def normalize_company_name(name: str) -> str:
    name = name.lower()
    for suffix in ["pvt ltd", "private limited", "llp", "limited", "ltd", "pvt", "inc"]:
        name = name.replace(suffix, "")
    name = re.sub(r"\s+", " ", name).strip()
    return name


class TestGSTValidation:
    def test_valid_gst(self):
        assert validate_gst("27AADCB2230M1ZP") is True

    def test_invalid_state_code(self):
        assert validate_gst("99AADCB2230M1ZP") is False

    def test_missing_z_character(self):
        assert validate_gst("27AADCB2230M1AP") is False

    def test_wrong_length(self):
        assert validate_gst("27AADCB223") is False

    def test_valid_state_code_01(self):
        assert validate_gst("01AADCB2230M1ZP") is True

    def test_valid_state_code_37(self):
        assert validate_gst("37AADCB2230M1ZP") is True


class TestCompanyNameNormalisation:
    def test_pvt_ltd_removal(self):
        assert normalize_company_name("ABC Pvt Ltd") == "abc"

    def test_private_limited_removal(self):
        assert normalize_company_name("XYZ Private Limited") == "xyz"

    def test_equality_after_normalisation(self):
        assert normalize_company_name("ABC Pvt Ltd") == normalize_company_name("abc")

    def test_whitespace_normalisation(self):
        assert normalize_company_name("  Hello   World  Ltd  ") == "hello world"


class TestConnectedComponentDetection:
    def test_shared_gst_detected(self):
        G = nx.Graph()
        G.add_node("bidder_1", node_type="bidder")
        G.add_node("bidder_2", node_type="bidder")
        G.add_node("GST:27AADCB2230M1ZP", node_type="entity")
        G.add_edge("bidder_1", "GST:27AADCB2230M1ZP")
        G.add_edge("bidder_2", "GST:27AADCB2230M1ZP")

        for component in nx.connected_components(G):
            bidders = [n for n in component if G.nodes[n].get("node_type") == "bidder"]
            if len(bidders) > 1:
                assert set(bidders) == {"bidder_1", "bidder_2"}
                return
        pytest.fail("Shared entity not detected")

    def test_independent_bidders(self):
        G = nx.Graph()
        G.add_node("bidder_1", node_type="bidder")
        G.add_node("bidder_2", node_type="bidder")
        G.add_node("GST:A", node_type="entity")
        G.add_node("GST:B", node_type="entity")
        G.add_edge("bidder_1", "GST:A")
        G.add_edge("bidder_2", "GST:B")

        for component in nx.connected_components(G):
            bidders = [n for n in component if G.nodes[n].get("node_type") == "bidder"]
            assert len(bidders) <= 1  # No shared entities


class TestCosineSimilarity:
    def test_threshold_at_087(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        texts = ["completed 5 highway projects in uttar pradesh", "completed 5 highway projects in uttar pradesh region"]
        vectorizer = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        sim = cosine_similarity(matrix)[0][1]
        assert sim > 0.87  # Very similar texts should exceed threshold


class TestDBSCANClustering:
    def test_similar_prices_detected(self):
        from sklearn.cluster import DBSCAN

        prices = np.array([[100], [101], [500], [502]])
        normalized = prices / prices.max()
        clustering = DBSCAN(eps=0.05, min_samples=2).fit(normalized)

        labels = clustering.labels_
        clusters_found = len(set(labels) - {-1})
        assert clusters_found >= 1  # At least one cluster of similar prices
