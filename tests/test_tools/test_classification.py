"""Tests for classification assistance tools."""

from unittest.mock import AsyncMock, patch

import pytest

from export_control_mcp.models.classification import FederalRegisterNotice

# Sample notices for mocking Federal Register API
MOCK_NOTICES = [
    FederalRegisterNotice(
        document_number="2024-12345",
        title="Entity List Additions and Revisions",
        agency="Bureau of Industry and Security",
        publication_date="2024-01-15",
        effective_date="2024-01-15",
        document_type="Rule",
        summary="BIS is amending the EAR to add entities to the Entity List.",
        affected_countries=["CN", "RU"],
        federal_register_url="https://www.federalregister.gov/d/2024-12345",
    ),
    FederalRegisterNotice(
        document_number="2024-12346",
        title="ITAR Amendment: Revisions to USML Categories VIII",
        agency="Directorate of Defense Trade Controls",
        publication_date="2024-01-05",
        document_type="Proposed Rule",
        summary="DDTC proposes revisions to USML Category VIII.",
        federal_register_url="https://www.federalregister.gov/d/2024-12346",
    ),
]


@pytest.mark.asyncio
class TestSuggestClassification:
    """Tests for suggest_classification tool."""

    async def test_suggest_classification_military_item(self):
        """Test classification suggestion for military item."""
        from export_control_mcp.tools.classification import suggest_classification

        func = suggest_classification.fn
        result = await func("Military weapon system with combat targeting and guidance")

        assert "suggested_jurisdiction" in result
        assert result["suggested_jurisdiction"] in ["ITAR", "dual_use"]
        assert "confidence" in result
        assert "key_factors" in result
        assert len(result["key_factors"]) > 0
        assert "disclaimer" in result

    async def test_suggest_classification_commercial_item(self):
        """Test classification suggestion for commercial item."""
        from export_control_mcp.tools.classification import suggest_classification

        func = suggest_classification.fn
        result = await func("Commercial telecommunications equipment for consumer use")

        assert "suggested_jurisdiction" in result
        assert result["suggested_jurisdiction"] in ["EAR", "EAR99"]
        assert "suggested_eccns" in result
        assert "next_steps" in result

    async def test_suggest_classification_dual_use_item(self):
        """Test classification suggestion for dual-use item."""
        from export_control_mcp.tools.classification import suggest_classification

        func = suggest_classification.fn
        result = await func(
            "High-precision CNC machine tool with 5-axis capability for manufacturing",
            additional_context="Used for aerospace component manufacturing",
        )

        assert "suggested_jurisdiction" in result
        assert "questions_to_resolve" in result
        assert len(result["questions_to_resolve"]) > 0

    async def test_suggest_classification_semiconductor(self):
        """Test classification suggestion for semiconductor equipment."""
        from export_control_mcp.tools.classification import suggest_classification

        func = suggest_classification.fn
        result = await func(
            "Semiconductor manufacturing equipment for integrated circuit production"
        )

        assert "suggested_jurisdiction" in result
        assert result["suggested_jurisdiction"] in ["EAR", "dual_use"]
        assert "suggested_eccns" in result

    async def test_suggest_classification_encryption(self):
        """Test classification suggestion for encryption items."""
        from export_control_mcp.tools.classification import suggest_classification

        func = suggest_classification.fn
        result = await func("Software with encryption capabilities for network security")

        assert "suggested_jurisdiction" in result
        assert "suggested_eccns" in result


@pytest.mark.asyncio
class TestClassificationDecisionTree:
    """Tests for classification_decision_tree tool."""

    async def test_decision_tree_step_one(self):
        """Test first step of decision tree."""
        from export_control_mcp.tools.classification import classification_decision_tree

        func = classification_decision_tree.fn
        result = await func(
            "Electronic component for commercial use",
            step=1,
        )

        assert "item_description" in result
        assert result["item_description"] == "Electronic component for commercial use"
        assert "current_step" in result
        assert result["current_step"]["step_number"] == 1
        assert "question" in result["current_step"]
        assert "options" in result["current_step"]
        assert len(result["current_step"]["options"]) > 0
        assert result["is_complete"] is False

    async def test_decision_tree_step_progression(self):
        """Test progression through decision tree steps."""
        from export_control_mcp.tools.classification import classification_decision_tree

        func = classification_decision_tree.fn

        # Test step 2
        result2 = await func("Electronic component", step=2)
        assert result2["current_step"]["step_number"] == 2
        assert len(result2["completed_steps"]) == 1

        # Test step 3
        result3 = await func("Electronic component", step=3)
        assert result3["current_step"]["step_number"] == 3
        assert len(result3["completed_steps"]) == 2

    async def test_decision_tree_final_step(self):
        """Test reaching final step of decision tree."""
        from export_control_mcp.tools.classification import classification_decision_tree

        func = classification_decision_tree.fn
        result = await func(
            "Electronic component",
            step=5,
        )

        assert result["current_step"]["step_number"] == 5
        assert "preliminary_result" in result
        assert len(result["preliminary_result"]) > 0

    async def test_decision_tree_includes_regulation_references(self):
        """Test that steps include regulation references."""
        from export_control_mcp.tools.classification import classification_decision_tree

        func = classification_decision_tree.fn
        result = await func("Test item", step=1)

        assert "regulation_reference" in result["current_step"]
        assert "CFR" in result["current_step"]["regulation_reference"]


@pytest.mark.asyncio
class TestCheckLicenseException:
    """Tests for check_license_exception tool."""

    async def test_license_exception_friendly_country(self):
        """Test license exception check for friendly country."""
        from export_control_mcp.tools.classification import check_license_exception

        func = check_license_exception.fn
        result = await func(
            eccn="3A001",
            destination_country="DE",
            end_use="Commercial telecommunications",
        )

        assert result["eccn"] == "3A001"
        assert result["destination_country"] == "DE"
        assert "exceptions_checked" in result
        assert len(result["exceptions_checked"]) > 0
        assert "summary" in result

    async def test_license_exception_embargoed_country(self):
        """Test license exception check for embargoed country."""
        from export_control_mcp.tools.classification import check_license_exception

        func = check_license_exception.fn
        result = await func(
            eccn="3A001",
            destination_country="IR",
        )

        assert result["requires_license"] is True
        assert "embargo" in result["summary"].lower()
        assert len(result["warnings"]) > 0

    async def test_license_exception_ear99(self):
        """Test license exception check for EAR99 items."""
        from export_control_mcp.tools.classification import check_license_exception

        func = check_license_exception.fn
        result = await func(
            eccn="EAR99",
            destination_country="DE",
        )

        assert result["eccn"] == "EAR99"
        assert "exceptions_checked" in result

    async def test_license_exception_government_end_user(self):
        """Test license exception for government end-user."""
        from export_control_mcp.tools.classification import check_license_exception

        func = check_license_exception.fn
        result = await func(
            eccn="3A001",
            destination_country="DE",
            end_user_type="government",
        )

        assert result["end_user_type"] == "government"
        # GOV exception should be checked for government end-users
        gov_checks = [e for e in result["exceptions_checked"] if e["exception_code"] == "GOV"]
        assert len(gov_checks) > 0

    async def test_license_exception_military_warning(self):
        """Test that military end-use triggers warnings."""
        from export_control_mcp.tools.classification import check_license_exception

        func = check_license_exception.fn
        result = await func(
            eccn="3A001",
            destination_country="DE",
            end_user_type="military",
        )

        assert any("military" in w.lower() for w in result["warnings"])

    async def test_license_exception_restricted_country(self):
        """Test license exception for restricted (but not embargoed) country."""
        from export_control_mcp.tools.classification import check_license_exception

        func = check_license_exception.fn
        result = await func(
            eccn="3A001",
            destination_country="CN",
        )

        assert "exceptions_checked" in result
        # Some exceptions should be marked not eligible for China
        not_eligible = [
            e for e in result["exceptions_checked"] if e["eligibility"] == "not_eligible"
        ]
        assert len(not_eligible) > 0


@pytest.mark.asyncio
class TestGetRecentUpdates:
    """Tests for get_recent_updates tool."""

    async def test_get_recent_updates_all(self):
        """Test getting all recent updates."""
        from export_control_mcp.tools.classification import get_recent_updates

        # Mock the Federal Register service
        mock_service = AsyncMock()
        mock_service.search_documents.return_value = MOCK_NOTICES

        with patch(
            "export_control_mcp.services.federal_register.get_federal_register_service",
            return_value=mock_service,
        ):
            func = get_recent_updates.fn
            result = await func()

            assert isinstance(result, list)
            assert len(result) > 0
            assert "document_number" in result[0]
            assert "title" in result[0]
            assert "agency" in result[0]

    async def test_get_recent_updates_filter_by_agency(self):
        """Test filtering updates by agency."""
        from export_control_mcp.tools.classification import get_recent_updates

        # Mock returns only BIS notices when filtered
        bis_notices = [n for n in MOCK_NOTICES if "Bureau of Industry" in n.agency]
        mock_service = AsyncMock()
        mock_service.search_documents.return_value = bis_notices

        with patch(
            "export_control_mcp.services.federal_register.get_federal_register_service",
            return_value=mock_service,
        ):
            func = get_recent_updates.fn
            result = await func(agency="BIS")

            assert isinstance(result, list)
            for notice in result:
                assert "Bureau of Industry and Security" in notice["agency"]

    async def test_get_recent_updates_filter_by_type(self):
        """Test filtering updates by document type."""
        from export_control_mcp.tools.classification import get_recent_updates

        # Mock returns only Rule notices when filtered
        rule_notices = [n for n in MOCK_NOTICES if n.document_type == "Rule"]
        mock_service = AsyncMock()
        mock_service.search_documents.return_value = rule_notices

        with patch(
            "export_control_mcp.services.federal_register.get_federal_register_service",
            return_value=mock_service,
        ):
            func = get_recent_updates.fn
            result = await func(document_type="rule")

            assert isinstance(result, list)
            for notice in result:
                assert notice["document_type"] == "Rule"

    async def test_get_recent_updates_ddtc(self):
        """Test filtering for DDTC updates."""
        from export_control_mcp.tools.classification import get_recent_updates

        # Mock returns only DDTC notices when filtered
        ddtc_notices = [n for n in MOCK_NOTICES if "Defense Trade" in n.agency]
        mock_service = AsyncMock()
        mock_service.search_documents.return_value = ddtc_notices

        with patch(
            "export_control_mcp.services.federal_register.get_federal_register_service",
            return_value=mock_service,
        ):
            func = get_recent_updates.fn
            result = await func(agency="DDTC")

            assert isinstance(result, list)
            for notice in result:
                assert "Directorate of Defense Trade Controls" in notice["agency"]

    async def test_get_recent_updates_includes_affected_items(self):
        """Test that updates include affected ECCNs and countries."""
        from export_control_mcp.tools.classification import get_recent_updates

        mock_service = AsyncMock()
        mock_service.search_documents.return_value = MOCK_NOTICES

        with patch(
            "export_control_mcp.services.federal_register.get_federal_register_service",
            return_value=mock_service,
        ):
            func = get_recent_updates.fn
            result = await func()

            # At least one notice should have affected items
            has_affected_eccns = any(len(n.get("affected_eccns", [])) > 0 for n in result)
            has_affected_countries = any(len(n.get("affected_countries", [])) > 0 for n in result)

            assert has_affected_eccns or has_affected_countries
