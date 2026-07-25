from models.client import calculate_tier, LoyaltyTier


def test_bronze_zero():
    assert calculate_tier(0) == LoyaltyTier.bronze


def test_bronze_below_threshold():
    assert calculate_tier(499) == LoyaltyTier.bronze


def test_silver_at_threshold():
    assert calculate_tier(500) == LoyaltyTier.silver


def test_silver_below_gold():
    assert calculate_tier(1499) == LoyaltyTier.silver


def test_gold_at_threshold():
    assert calculate_tier(1500) == LoyaltyTier.gold


def test_gold_below_platinum():
    assert calculate_tier(2999) == LoyaltyTier.gold


def test_platinum_at_threshold():
    assert calculate_tier(3000) == LoyaltyTier.platinum


def test_platinum_large_value():
    assert calculate_tier(999999) == LoyaltyTier.platinum


# Edge cases: exatamente nos limites
def test_exactly_silver_lower():
    assert calculate_tier(500) == LoyaltyTier.silver


def test_exactly_gold_lower():
    assert calculate_tier(1500) == LoyaltyTier.gold


def test_exactly_platinum_lower():
    assert calculate_tier(3000) == LoyaltyTier.platinum
