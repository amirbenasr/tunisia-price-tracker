"""Tests for base scraper utilities."""

from decimal import Decimal

import pytest

from src.scrapers.base import BaseScraper


class DummyScraper(BaseScraper):
    """Dummy scraper for testing base class methods."""

    async def scrape(self, page, max_pages=50):
        pass


@pytest.fixture
def scraper():
    """Create a dummy scraper for testing."""
    return DummyScraper(
        website_name="Test Site",
        base_url="https://example.com",
        rate_limit_ms=1000,
    )


class TestPriceParsing:
    """Tests for price parsing."""

    def test_parse_simple_price(self, scraper):
        """Test parsing simple price format."""
        assert scraper.parse_price("45.90") == Decimal("45.90")

    def test_parse_price_with_currency_symbol(self, scraper):
        """Test parsing price with currency symbols."""
        assert scraper.parse_price("45.90€") == Decimal("45.90")
        assert scraper.parse_price("$45.90") == Decimal("45.90")

    def test_parse_price_with_currency_code(self, scraper):
        """Test parsing price with currency codes."""
        assert scraper.parse_price("45.900 TND") == Decimal("45.900")
        assert scraper.parse_price("45.900 DT") == Decimal("45.900")

    def test_parse_price_european_format(self, scraper):
        """Test parsing European format (comma as decimal)."""
        assert scraper.parse_price("45,90") == Decimal("45.90")

    def test_parse_price_with_thousand_separator(self, scraper):
        """Test parsing price with thousand separators."""
        assert scraper.parse_price("1,234.56") == Decimal("1234.56")
        assert scraper.parse_price("1 234") == Decimal("1234")

    def test_parse_invalid_price(self, scraper):
        """Test parsing invalid price returns None."""
        assert scraper.parse_price("") is None
        assert scraper.parse_price("N/A") is None
        assert scraper.parse_price("Contact us") is None


class TestUrlResolution:
    """Tests for URL resolution."""

    def test_resolve_absolute_url(self, scraper):
        """Test absolute URLs are returned as-is."""
        url = "https://other.com/product"
        assert scraper.resolve_url(url) == url

    def test_resolve_relative_url(self, scraper):
        """Test relative URLs are resolved against base URL."""
        assert scraper.resolve_url("/product/123") == "https://example.com/product/123"

    def test_resolve_relative_path(self, scraper):
        """Test relative paths are resolved."""
        assert scraper.resolve_url("product/123") == "https://example.com/product/123"


class TestTextCleaning:
    """Tests for text cleaning."""

    def test_clean_normal_text(self, scraper):
        """Test cleaning normal text."""
        assert scraper.clean_text("Product Name") == "Product Name"

    def test_clean_whitespace(self, scraper):
        """Test cleaning excess whitespace."""
        assert scraper.clean_text("  Product   Name  ") == "Product Name"
        assert scraper.clean_text("Product\n\nName") == "Product Name"

    def test_clean_empty(self, scraper):
        """Test cleaning empty/None values."""
        assert scraper.clean_text(None) is None
        assert scraper.clean_text("") is None
        assert scraper.clean_text("   ") is None


class TestStockStatus:
    """Tests for stock status detection."""

    def test_in_stock_positive(self, scraper):
        """Test detecting in-stock status."""
        assert scraper.is_in_stock("In Stock") is True
        assert scraper.is_in_stock("Disponible") is True
        assert scraper.is_in_stock("En stock") is True

    def test_out_of_stock(self, scraper):
        """Test detecting out-of-stock status."""
        assert scraper.is_in_stock("Out of Stock") is False
        assert scraper.is_in_stock("Rupture de stock") is False
        assert scraper.is_in_stock("Indisponible") is False
        assert scraper.is_in_stock("Épuisé") is False

    def test_default_in_stock(self, scraper):
        """Test default behavior for unknown text."""
        assert scraper.is_in_stock(None) is True
        assert scraper.is_in_stock("") is True


class TestExternalIdGeneration:
    """Tests for external ID generation."""

    def test_generate_external_id(self, scraper):
        """Test external ID generation is consistent."""
        url1 = "https://example.com/product/123"
        url2 = "https://example.com/product/123?ref=test"

        # Same base URL should generate same ID
        id1 = scraper.generate_external_id(url1)
        id2 = scraper.generate_external_id(url2)

        assert id1 == id2
        assert len(id1) == 16

    def test_different_urls_different_ids(self, scraper):
        """Test different URLs generate different IDs."""
        id1 = scraper.generate_external_id("https://example.com/product/123")
        id2 = scraper.generate_external_id("https://example.com/product/456")

        assert id1 != id2
