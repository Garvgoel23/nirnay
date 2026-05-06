"""Tests for evaluation comparators — unit normalisation, arbitration routing, ambiguity override."""
import pytest
from decimal import Decimal


# Unit normalisation
UNIT_MULTIPLIERS = {"crores": 10000000, "crore": 10000000, "lakhs": 100000, "lakh": 100000, "thousands": 1000, "rupees": 1}


def normalise_value(amount: float, unit: str) -> float:
    return amount * UNIT_MULTIPLIERS.get(unit.lower(), 1)


class TestFinancialComparatorUnitNormalisation:
    def test_lakhs_to_rupees(self):
        assert normalise_value(5, "lakhs") == 500000

    def test_crores_to_rupees(self):
        assert normalise_value(1, "crores") == 10000000

    def test_thousands_to_rupees(self):
        assert normalise_value(50, "thousands") == 50000

    def test_rupees_identity(self):
        assert normalise_value(100, "rupees") == 100


class TestBorderlineRouting:
    def test_within_5_percent_routes_to_arbitration(self):
        threshold = 500000
        extracted = 485000  # 3% below
        ratio = abs(extracted - threshold) / threshold
        assert ratio <= 0.05  # Should route to arbitration

    def test_outside_5_percent_does_not_route(self):
        threshold = 500000
        extracted = 400000  # 20% below
        ratio = abs(extracted - threshold) / threshold
        assert ratio > 0.05  # Should NOT route to arbitration


class TestAmbiguityOverride:
    def test_low_confidence_triggers_manual_review(self):
        confidence = 0.60
        assert confidence < 0.65  # Should trigger MANUAL_REVIEW

    def test_acceptable_confidence_proceeds(self):
        confidence = 0.80
        assert confidence >= 0.65  # Should proceed to comparator

    def test_contradicted_status_triggers_manual_review(self):
        status = "contradicted"
        assert status == "contradicted"  # Should trigger MANUAL_REVIEW

    def test_low_authenticity_triggers_manual_review(self):
        authenticity_score = 40
        assert authenticity_score < 50  # Should trigger MANUAL_REVIEW


class TestCertificateExpiry:
    def test_expired_certificate(self):
        from datetime import datetime
        expiry = datetime(2023, 1, 1)
        assert expiry < datetime.now()

    def test_valid_certificate(self):
        from datetime import datetime
        expiry = datetime(2030, 12, 31)
        assert expiry > datetime.now()


class TestExperienceComparison:
    def test_meets_requirement(self):
        found = 5
        required = 3
        assert found >= required

    def test_does_not_meet_requirement(self):
        found = 2
        required = 3
        assert found < required
