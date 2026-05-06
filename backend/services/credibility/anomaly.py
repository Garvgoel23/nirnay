"""
Cross-bidder anomaly detection service.
Detects shared entities (GST, PAN, directors), recycled documents (TF-IDF), 
and coordinated bidding (DBSCAN price clustering).
"""
import logging
import re
import uuid
from typing import Dict, List, Tuple

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import numpy as np
from sqlalchemy.orm import Session

from db.models import BidderExtractedValue, TenderAnomaly as TenderAnomalyDB

logger = logging.getLogger(__name__)

# GST number regex pattern (15 chars)
GST_PATTERN = re.compile(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d]{2})\b")

# PAN pattern (10 chars)
PAN_PATTERN = re.compile(r"\b([A-Z]{5}\d{4}[A-Z])\b")


class CrossBidderAnomalyDetector:
    """Detects anomalies across multiple bidders for a tender."""

    def detect(self, tender_id: str, db: Session) -> List[Dict]:
        """
        Run all anomaly detection checks for a tender.

        Args:
            tender_id: The tender identifier
            db: Database session

        Returns:
            List of anomaly dictionaries
        """
        # Pull all extracted values for the tender
        values = db.query(BidderExtractedValue).filter(
            BidderExtractedValue.tender_id == tender_id
        ).all()

        if not values:
            return []

        # Group values by bidder
        bidder_values: Dict[str, List] = {}
        for v in values:
            if v.bidder_id not in bidder_values:
                bidder_values[v.bidder_id] = []
            bidder_values[v.bidder_id].append(v)

        anomalies = []

        # 1. Entity Resolution via networkx
        entity_anomalies = self._detect_shared_entities(bidder_values)
        anomalies.extend(entity_anomalies)

        # 2. Text Similarity (recycled documents)
        similarity_anomalies = self._detect_recycled_documents(values)
        anomalies.extend(similarity_anomalies)

        # 3. Price Clustering (coordinated bidding)
        price_anomalies = self._detect_coordinated_bidding(values)
        anomalies.extend(price_anomalies)

        # Write to database
        for anomaly in anomalies:
            db_anomaly = TenderAnomalyDB(
                id=str(uuid.uuid4()),
                tender_id=tender_id,
                anomaly_type=anomaly["anomaly_type"],
                bidder_ids=anomaly["bidder_ids"],
                evidence=anomaly["evidence"],
                severity=anomaly["severity"],
            )
            db.add(db_anomaly)

        db.commit()

        logger.info(f"Detected {len(anomalies)} anomalies for tender {tender_id}")
        return anomalies

    def _detect_shared_entities(self, bidder_values: Dict[str, List]) -> List[Dict]:
        """Detect shared GST numbers, PANs, and other entities across bidders."""
        anomalies = []
        G = nx.Graph()

        for bidder_id, values in bidder_values.items():
            G.add_node(bidder_id, node_type="bidder")

            for v in values:
                if not v.extracted_value:
                    continue

                text = v.extracted_value

                # Extract GST numbers
                gst_matches = GST_PATTERN.findall(text)
                for gst in gst_matches:
                    if self._validate_gst(gst):
                        entity_key = f"GST:{gst}"
                        G.add_node(entity_key, node_type="entity", entity_type="GST")
                        G.add_edge(bidder_id, entity_key)

                # Extract PAN numbers
                pan_matches = PAN_PATTERN.findall(text)
                for pan in pan_matches:
                    entity_key = f"PAN:{pan}"
                    G.add_node(entity_key, node_type="entity", entity_type="PAN")
                    G.add_edge(bidder_id, entity_key)

                # Normalised company names
                if v.source_snippet:
                    norm_name = self._normalize_company_name(v.source_snippet)
                    if len(norm_name) > 3:
                        entity_key = f"NAME:{norm_name}"
                        G.add_node(entity_key, node_type="entity", entity_type="company_name")
                        G.add_edge(bidder_id, entity_key)

        # Find connected components with >1 bidder
        for component in nx.connected_components(G):
            bidders_in_component = [n for n in component if G.nodes[n].get("node_type") == "bidder"]
            entities_in_component = [n for n in component if G.nodes[n].get("node_type") == "entity"]

            if len(bidders_in_component) > 1:
                shared_types = set()
                shared_values = []
                for entity in entities_in_component:
                    etype = G.nodes[entity].get("entity_type", "unknown")
                    shared_types.add(etype)
                    shared_values.append(entity)

                anomalies.append({
                    "anomaly_type": "SHARED_ENTITY_DETECTED",
                    "bidder_ids": bidders_in_component,
                    "evidence": {
                        "shared_entity_types": list(shared_types),
                        "shared_values": shared_values,
                    },
                    "severity": "critical" if "GST" in shared_types else "high",
                })

        return anomalies

    def _detect_recycled_documents(self, values: List) -> List[Dict]:
        """Detect suspiciously similar technical experience descriptions."""
        anomalies = []

        # Collect experience-related snippets per bidder
        bidder_snippets: Dict[str, str] = {}
        for v in values:
            if (v.source_snippet and
                hasattr(v, 'criterion') and
                v.source_snippet.strip()):
                # Group by bidder
                if v.bidder_id not in bidder_snippets:
                    bidder_snippets[v.bidder_id] = ""
                bidder_snippets[v.bidder_id] += " " + v.source_snippet

        if len(bidder_snippets) < 2:
            return anomalies

        bidder_ids = list(bidder_snippets.keys())
        texts = [bidder_snippets[bid] for bid in bidder_ids]

        try:
            vectorizer = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(texts)
            sim_matrix = cosine_similarity(tfidf_matrix)

            for i in range(len(bidder_ids)):
                for j in range(i + 1, len(bidder_ids)):
                    if sim_matrix[i][j] > 0.87:
                        anomalies.append({
                            "anomaly_type": "RECYCLED_DOCUMENT_SUSPECTED",
                            "bidder_ids": [bidder_ids[i], bidder_ids[j]],
                            "evidence": {
                                "cosine_similarity": float(sim_matrix[i][j]),
                            },
                            "severity": "high",
                        })
        except Exception as e:
            logger.warning(f"TF-IDF similarity check failed: {e}")

        return anomalies

    def _detect_coordinated_bidding(self, values: List) -> List[Dict]:
        """Detect suspiciously close bid prices using DBSCAN clustering."""
        anomalies = []

        # Collect financial values
        bidder_prices: Dict[str, float] = {}
        for v in values:
            if v.extracted_value and v.extraction_status == "found_clear":
                try:
                    price = self._parse_price(v.extracted_value, v.value_unit)
                    if price and price > 0:
                        bidder_prices[v.bidder_id] = price
                except Exception:
                    continue

        if len(bidder_prices) < 2:
            return anomalies

        bidder_ids = list(bidder_prices.keys())
        prices = np.array([bidder_prices[bid] for bid in bidder_ids]).reshape(-1, 1)

        # Normalize prices for DBSCAN
        if prices.max() > 0:
            normalized = prices / prices.max()
        else:
            return anomalies

        try:
            clustering = DBSCAN(eps=0.05, min_samples=2).fit(normalized)
            labels = clustering.labels_

            # Find clusters with ≥2 bidders
            for label in set(labels):
                if label == -1:
                    continue
                cluster_indices = [i for i, l in enumerate(labels) if l == label]
                if len(cluster_indices) >= 2:
                    cluster_bidders = [bidder_ids[i] for i in cluster_indices]
                    cluster_prices = {bidder_ids[i]: float(prices[i][0]) for i in cluster_indices}

                    anomalies.append({
                        "anomaly_type": "COORDINATED_BIDDING_SUSPECTED",
                        "bidder_ids": cluster_bidders,
                        "evidence": {
                            "prices": cluster_prices,
                            "price_spread_pct": float((max(cluster_prices.values()) - min(cluster_prices.values())) / max(cluster_prices.values()) * 100),
                        },
                        "severity": "high",
                    })
        except Exception as e:
            logger.warning(f"DBSCAN clustering failed: {e}")

        return anomalies

    @staticmethod
    def _normalize_company_name(name: str) -> str:
        """Normalize company name for comparison."""
        name = name.lower()
        for suffix in ["pvt ltd", "private limited", "llp", "limited", "ltd", "pvt", "inc"]:
            name = name.replace(suffix, "")
        name = re.sub(r"\s+", " ", name).strip()
        return name

    @staticmethod
    def _validate_gst(gst: str) -> bool:
        """Validate GST number structure."""
        if len(gst) != 15:
            return False
        # State code: 01–37
        try:
            state_code = int(gst[:2])
            if state_code < 1 or state_code > 37:
                return False
        except ValueError:
            return False
        # Character 14 should be 'Z'
        if gst[13] != 'Z':
            return False
        return True

    @staticmethod
    def _parse_price(value: str, unit: str = None) -> float:
        """Parse price string and normalize to rupees."""
        # Remove commas and whitespace
        clean = re.sub(r"[,\s₹Rs.]", "", str(value))
        try:
            amount = float(clean)
        except ValueError:
            return 0.0

        unit_lower = (unit or "").lower()
        multipliers = {
            "crores": 10000000,
            "crore": 10000000,
            "lakhs": 100000,
            "lakh": 100000,
            "thousands": 1000,
            "thousand": 1000,
            "rupees": 1,
        }
        multiplier = multipliers.get(unit_lower, 1)
        return amount * multiplier
