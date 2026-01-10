"""Tests for regulation search tools."""

import pytest


@pytest.mark.asyncio
class TestSearchEAR:
    """Tests for search_ear tool."""

    async def test_search_ear_returns_results(self, rag_service, embedding_service, sample_ear_chunk):
        """Test that search_ear returns relevant results."""
        # First populate the store
        embedding = embedding_service.embed(sample_ear_chunk.to_embedding_text())
        rag_service._vector_store.add_chunk(sample_ear_chunk, embedding)

        # Search
        results = await rag_service.search_ear(
            query="export administration regulations",
            limit=5,
        )

        assert len(results) > 0
        assert results[0].chunk.regulation_type.value == "ear"

    async def test_search_ear_with_part_filter(self, rag_service, embedding_service, sample_ear_chunk):
        """Test filtering by EAR part."""
        embedding = embedding_service.embed(sample_ear_chunk.to_embedding_text())
        rag_service._vector_store.add_chunk(sample_ear_chunk, embedding)

        # Search with matching part
        results = await rag_service.search_ear(
            query="export regulations",
            part="Part 730",
            limit=5,
        )

        assert len(results) > 0
        assert all(r.chunk.part == "Part 730" for r in results)

    async def test_search_ear_empty_results(self, rag_service):
        """Test search returns empty list when no data."""
        results = await rag_service.search_ear(
            query="nonexistent topic xyz123",
            limit=5,
        )

        assert results == []


@pytest.mark.asyncio
class TestSearchITAR:
    """Tests for search_itar tool."""

    async def test_search_itar_returns_results(self, rag_service, embedding_service, sample_itar_chunk):
        """Test that search_itar returns relevant results."""
        embedding = embedding_service.embed(sample_itar_chunk.to_embedding_text())
        rag_service._vector_store.add_chunk(sample_itar_chunk, embedding)

        results = await rag_service.search_itar(
            query="defense articles",
            limit=5,
        )

        assert len(results) > 0
        assert results[0].chunk.regulation_type.value == "itar"


@pytest.mark.asyncio
class TestSearchBoth:
    """Tests for searching both EAR and ITAR."""

    async def test_search_returns_both_types(self, rag_service, embedding_service, sample_ear_chunk, sample_itar_chunk):
        """Test that search without filter returns both types."""
        chunks = [sample_ear_chunk, sample_itar_chunk]
        texts = [c.to_embedding_text() for c in chunks]
        embeddings = embedding_service.embed_batch(texts)
        rag_service._vector_store.add_chunks_batch(chunks, embeddings)

        results = await rag_service.search(
            query="export regulations and controls",
            limit=10,
        )

        assert len(results) >= 2
        reg_types = {r.chunk.regulation_type.value for r in results}
        assert "ear" in reg_types
        assert "itar" in reg_types


@pytest.mark.asyncio
class TestGetECCNDetails:
    """Tests for get_eccn_details tool."""

    async def test_get_eccn_from_reference_data(self):
        """Test looking up an ECCN from reference data."""
        from export_control_mcp.tools.regulations import get_eccn_details

        # Access the wrapped function via .fn to bypass MCP decorator
        func = get_eccn_details.fn
        result = await func("3A001")

        assert "error" not in result
        assert result["eccn"] == "3A001"
        assert result["category"] == 3
        assert result["category_name"] == "Electronics"
        assert result["product_group"] == "A"

    async def test_get_eccn_parsing_only(self):
        """Test parsing an ECCN not in reference data."""
        from export_control_mcp.tools.regulations import get_eccn_details

        func = get_eccn_details.fn
        result = await func("9B003")

        assert "error" not in result
        assert result["eccn"] == "9B003"
        assert result["category"] == 9
        assert result["category_name"] == "Aerospace & Propulsion"
        assert result["product_group"] == "B"
        assert result["product_group_name"] == "Test, Inspection, and Production Equipment"

    async def test_get_eccn_invalid_format(self):
        """Test error handling for invalid ECCN format."""
        from export_control_mcp.tools.regulations import get_eccn_details

        func = get_eccn_details.fn
        result = await func("INVALID")

        assert "error" in result
        assert "Invalid ECCN format" in result["error"]

    async def test_get_eccn_case_insensitive(self):
        """Test that ECCN lookup is case insensitive."""
        from export_control_mcp.tools.regulations import get_eccn_details

        func = get_eccn_details.fn
        result = await func("3a001")

        assert "error" not in result
        assert result["eccn"] == "3A001"


@pytest.mark.asyncio
class TestGetUSMLCategoryDetails:
    """Tests for get_usml_category_details tool."""

    async def test_get_usml_category_by_number(self):
        """Test looking up USML category by Arabic number."""
        from export_control_mcp.tools.regulations import get_usml_category_details

        func = get_usml_category_details.fn
        result = await func("1")

        assert "error" not in result
        assert result["category"] == "I"
        assert result["number"] == 1
        assert "Firearms" in result["title"]

    async def test_get_usml_category_by_roman(self):
        """Test looking up USML category by Roman numeral."""
        from export_control_mcp.tools.regulations import get_usml_category_details

        func = get_usml_category_details.fn
        result = await func("IV")

        assert "error" not in result
        assert result["category"] == "IV"
        assert result["number"] == 4

    async def test_get_usml_category_invalid(self):
        """Test error handling for invalid USML category."""
        from export_control_mcp.tools.regulations import get_usml_category_details

        func = get_usml_category_details.fn
        result = await func("99")

        assert "error" in result
        assert "not found" in result["error"]


@pytest.mark.asyncio
class TestCompareJurisdictions:
    """Tests for compare_jurisdictions tool."""

    async def test_compare_jurisdictions_military_item(
        self, rag_service, embedding_service, sample_ear_chunk, sample_itar_chunk
    ):
        """Test jurisdiction analysis for military item."""
        from export_control_mcp.tools.regulations import compare_jurisdictions

        # Populate store for search
        chunks = [sample_ear_chunk, sample_itar_chunk]
        texts = [c.to_embedding_text() for c in chunks]
        embeddings = embedding_service.embed_batch(texts)
        rag_service._vector_store.add_chunks_batch(chunks, embeddings)

        func = compare_jurisdictions.fn
        result = await func(
            "Military weapon system with combat targeting capabilities",
            include_search_results=False,
        )

        assert "likely_jurisdiction" in result
        assert len(result["itar_indicators"]) > 0  # Should detect military keywords
        assert "next_steps" in result

    async def test_compare_jurisdictions_commercial_item(
        self, rag_service, embedding_service, sample_ear_chunk, sample_itar_chunk
    ):
        """Test jurisdiction analysis for commercial item."""
        from export_control_mcp.tools.regulations import compare_jurisdictions

        chunks = [sample_ear_chunk, sample_itar_chunk]
        texts = [c.to_embedding_text() for c in chunks]
        embeddings = embedding_service.embed_batch(texts)
        rag_service._vector_store.add_chunks_batch(chunks, embeddings)

        func = compare_jurisdictions.fn
        result = await func(
            "Commercial telecommunications equipment for civilian consumer use",
            include_search_results=True,
        )

        assert "likely_jurisdiction" in result
        assert len(result["ear_indicators"]) > 0  # Should detect commercial keywords
        # With include_search_results=True, we should have search results
        assert "ear_search_results" in result


@pytest.mark.asyncio
class TestExplainExportTerm:
    """Tests for explain_export_term tool."""

    async def test_explain_term_found(self):
        """Test looking up a known term."""
        from export_control_mcp.tools.regulations import explain_export_term

        func = explain_export_term.fn
        result = await func("deemed export")

        assert "error" not in result
        assert "definition" in result

    async def test_explain_term_case_insensitive(self):
        """Test case-insensitive term lookup."""
        from export_control_mcp.tools.regulations import explain_export_term

        func = explain_export_term.fn
        result = await func("DEEMED EXPORT")

        assert "error" not in result or "definition" in result

    async def test_explain_term_not_found(self):
        """Test error handling for unknown term."""
        from export_control_mcp.tools.regulations import explain_export_term

        func = explain_export_term.fn
        result = await func("nonexistent_term_xyz")

        assert "error" in result
        assert "not found" in result["error"]


@pytest.mark.asyncio
class TestGetLicenseExceptionInfo:
    """Tests for get_license_exception_info tool."""

    async def test_get_license_exception_lvs(self):
        """Test looking up LVS license exception."""
        from export_control_mcp.tools.regulations import get_license_exception_info

        func = get_license_exception_info.fn
        result = await func("LVS")

        assert "error" not in result
        assert result["code"] == "LVS"
        assert "name" in result
        assert "Limited Value" in result["name"]

    async def test_get_license_exception_case_insensitive(self):
        """Test case-insensitive exception lookup."""
        from export_control_mcp.tools.regulations import get_license_exception_info

        func = get_license_exception_info.fn
        result = await func("enc")

        assert "error" not in result
        assert result["code"] == "ENC"

    async def test_get_license_exception_not_found(self):
        """Test error handling for unknown exception code."""
        from export_control_mcp.tools.regulations import get_license_exception_info

        func = get_license_exception_info.fn
        result = await func("INVALID")

        assert "error" in result
        assert "available_exceptions" in result


@pytest.mark.asyncio
class TestGetCountryGroupInfo:
    """Tests for get_country_group_info tool."""

    async def test_get_country_group_friendly(self):
        """Test getting country groups for a friendly country."""
        from export_control_mcp.tools.regulations import get_country_group_info

        func = get_country_group_info.fn
        result = await func("Germany")

        assert "error" not in result
        assert result["country"] == "Germany"
        assert "groups" in result
        assert "A:1" in result["groups"]  # Wassenaar member
        assert len(result["license_implications"]) > 0

    async def test_get_country_group_embargoed(self):
        """Test getting country groups for an embargoed country."""
        from export_control_mcp.tools.regulations import get_country_group_info

        func = get_country_group_info.fn
        result = await func("Iran")

        assert "error" not in result
        assert "groups" in result
        assert any(g.startswith("E:") for g in result["groups"])  # Embargoed
        assert any("embargo" in impl.lower() for impl in result["license_implications"])

    async def test_get_country_group_not_found(self):
        """Test error handling for unknown country."""
        from export_control_mcp.tools.regulations import get_country_group_info

        func = get_country_group_info.fn
        result = await func("NonexistentCountry")

        assert "error" in result
        assert "not found" in result["error"]