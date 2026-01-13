"""Integration tests for MCP tools registration and execution.

These tests verify that tools are properly registered with the MCP server
and produce expected output formats when called.
"""

import pytest

from export_control_mcp.server import mcp


class TestMCPToolRegistration:
    """Tests for MCP tool registration."""

    @pytest.mark.asyncio
    async def test_should_register_regulations_tools(self) -> None:
        """Test that regulation tools are registered with MCP."""
        tools = await mcp.get_tools()
        tool_names = list(tools.keys())

        assert "search_regulations" in tool_names
        assert "get_eccn_details" in tool_names
        assert "get_usml_category_details" in tool_names
        assert "compare_jurisdictions" in tool_names
        assert "explain_export_term" in tool_names
        assert "get_license_exception_info" in tool_names
        assert "get_country_group_info" in tool_names

    @pytest.mark.asyncio
    async def test_should_register_sanctions_tools(self) -> None:
        """Test that sanctions tools are registered with MCP."""
        tools = await mcp.get_tools()
        tool_names = list(tools.keys())

        assert "search_entity_list" in tool_names
        assert "search_sdn_list" in tool_names
        assert "search_denied_persons" in tool_names
        assert "check_country_sanctions" in tool_names
        assert "search_consolidated_screening_list" in tool_names
        assert "get_csl_statistics" in tool_names

    @pytest.mark.asyncio
    async def test_should_register_classification_tools(self) -> None:
        """Test that classification tools are registered with MCP."""
        tools = await mcp.get_tools()
        tool_names = list(tools.keys())

        assert "suggest_classification" in tool_names

    @pytest.mark.asyncio
    async def test_should_register_doe_nuclear_tools(self) -> None:
        """Test that DOE nuclear tools are registered with MCP."""
        tools = await mcp.get_tools()
        tool_names = list(tools.keys())

        assert "check_cfr810_country" in tool_names
        assert "get_cfr810_activities" in tool_names

    @pytest.mark.asyncio
    async def test_should_have_tool_descriptions(self) -> None:
        """Test that all registered tools have descriptions."""
        tools = await mcp.get_tools()

        for name, tool in tools.items():
            assert tool.description, f"Tool {name} missing description"
            assert len(tool.description) > 20, f"Tool {name} description too short"


class TestMCPToolExecution:
    """Tests for MCP tool execution end-to-end.

    These tests call the underlying function directly via the tool's fn attribute.
    """

    @pytest.mark.asyncio
    async def test_should_execute_search_regulations(self) -> None:
        """Test search_regulations tool execution."""
        tools = await mcp.get_tools()
        tool = tools["search_regulations"]
        result = await tool.fn(query="encryption")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_should_execute_get_eccn_details(self) -> None:
        """Test get_eccn_details tool execution."""
        tools = await mcp.get_tools()
        tool = tools["get_eccn_details"]
        result = await tool.fn(eccn="5A002")

        assert result is not None
        assert isinstance(result, dict)
        assert "eccn" in result or "error" in result

    @pytest.mark.asyncio
    async def test_should_execute_get_usml_category_details(self) -> None:
        """Test get_usml_category_details tool execution."""
        tools = await mcp.get_tools()
        tool = tools["get_usml_category_details"]
        result = await tool.fn(category="I")

        assert result is not None
        assert isinstance(result, dict)
        assert "category" in result or "error" in result

    @pytest.mark.asyncio
    async def test_should_execute_check_country_sanctions(self) -> None:
        """Test check_country_sanctions tool execution."""
        tools = await mcp.get_tools()
        tool = tools["check_country_sanctions"]
        result = await tool.fn(country="IR")

        assert result is not None
        assert isinstance(result, dict)
        assert "country_code" in result or "error" in result

    @pytest.mark.asyncio
    async def test_should_execute_search_entity_list(self) -> None:
        """Test search_entity_list tool execution."""
        tools = await mcp.get_tools()
        tool = tools["search_entity_list"]
        result = await tool.fn(query="test entity")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_should_execute_search_sdn_list(self) -> None:
        """Test search_sdn_list tool execution."""
        tools = await mcp.get_tools()
        tool = tools["search_sdn_list"]
        result = await tool.fn(query="test")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_should_execute_search_denied_persons(self) -> None:
        """Test search_denied_persons tool execution."""
        tools = await mcp.get_tools()
        tool = tools["search_denied_persons"]
        result = await tool.fn(query="test")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_should_execute_explain_export_term(self) -> None:
        """Test explain_export_term tool execution."""
        tools = await mcp.get_tools()
        tool = tools["explain_export_term"]
        result = await tool.fn(term="deemed export")

        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_should_execute_get_license_exception_info(self) -> None:
        """Test get_license_exception_info tool execution."""
        tools = await mcp.get_tools()
        tool = tools["get_license_exception_info"]
        result = await tool.fn(exception_code="LVS")

        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_should_execute_get_country_group_info(self) -> None:
        """Test get_country_group_info tool execution."""
        tools = await mcp.get_tools()
        tool = tools["get_country_group_info"]
        result = await tool.fn(country="Germany")

        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_should_execute_compare_jurisdictions(self) -> None:
        """Test compare_jurisdictions tool execution."""
        tools = await mcp.get_tools()
        tool = tools["compare_jurisdictions"]
        result = await tool.fn(item_description="military grade encryption device")

        assert result is not None
        assert isinstance(result, dict)
        assert "likely_jurisdiction" in result

    @pytest.mark.asyncio
    async def test_should_execute_suggest_classification(self) -> None:
        """Test suggest_classification tool execution."""
        tools = await mcp.get_tools()
        tool = tools["suggest_classification"]
        result = await tool.fn(item_description="high-speed computer for data processing")

        assert result is not None
        assert isinstance(result, dict)
        assert "suggested_eccns" in result or "suggested_jurisdiction" in result

    @pytest.mark.asyncio
    async def test_should_execute_check_cfr810_country(self) -> None:
        """Test check_cfr810_country tool execution."""
        tools = await mcp.get_tools()
        tool = tools["check_cfr810_country"]
        result = await tool.fn(country="France")

        assert result is not None
        assert isinstance(result, dict)
        assert "country" in result

    @pytest.mark.asyncio
    async def test_should_execute_get_cfr810_activities(self) -> None:
        """Test get_cfr810_activities tool execution."""
        tools = await mcp.get_tools()
        tool = tools["get_cfr810_activities"]
        result = await tool.fn()  # No parameters needed

        assert result is not None
        assert isinstance(result, dict)
        assert "generally_authorized_activities" in result

    @pytest.mark.asyncio
    async def test_should_execute_search_consolidated_screening_list(self) -> None:
        """Test search_consolidated_screening_list tool execution."""
        tools = await mcp.get_tools()
        tool = tools["search_consolidated_screening_list"]
        result = await tool.fn(query="test company")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_should_execute_get_csl_statistics(self) -> None:
        """Test get_csl_statistics tool execution."""
        tools = await mcp.get_tools()
        tool = tools["get_csl_statistics"]
        result = await tool.fn()

        assert result is not None
        assert isinstance(result, dict)
        assert "total_entries" in result


class TestMCPToolInputValidation:
    """Tests for MCP tool input validation."""

    @pytest.mark.asyncio
    async def test_should_handle_empty_query(self) -> None:
        """Test that tools handle empty queries gracefully."""
        tools = await mcp.get_tools()
        tool = tools["search_entity_list"]
        result = await tool.fn(query="")

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_should_handle_invalid_country_code(self) -> None:
        """Test that tools handle invalid country codes."""
        tools = await mcp.get_tools()
        tool = tools["check_country_sanctions"]
        result = await tool.fn(country="XX")

        assert result is not None
        assert isinstance(result, dict)
        assert "error" in result or "country_code" in result

    @pytest.mark.asyncio
    async def test_should_handle_invalid_eccn(self) -> None:
        """Test that tools handle invalid ECCNs."""
        tools = await mcp.get_tools()
        tool = tools["get_eccn_details"]
        result = await tool.fn(eccn="INVALID")

        assert result is not None
        assert isinstance(result, dict)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_should_handle_fuzzy_threshold_clamping(self) -> None:
        """Test that fuzzy threshold is clamped to valid range."""
        tools = await mcp.get_tools()
        tool = tools["search_entity_list"]
        result = await tool.fn(query="test", fuzzy_threshold=2.0)

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_should_handle_limit_clamping(self) -> None:
        """Test that limit is clamped to valid range."""
        tools = await mcp.get_tools()
        tool = tools["search_entity_list"]
        result = await tool.fn(query="test", limit=1000)

        assert result is not None
        assert isinstance(result, list)


class TestMCPToolOutputFormat:
    """Tests for MCP tool output format consistency."""

    @pytest.mark.asyncio
    async def test_country_sanctions_should_have_expected_fields(self) -> None:
        """Test that country sanctions output has expected fields."""
        tools = await mcp.get_tools()
        tool = tools["check_country_sanctions"]
        result = await tool.fn(country="Iran")

        assert isinstance(result, dict)
        if "error" not in result:
            expected_fields = [
                "country_code",
                "country_name",
                "embargo_type",
                "itar_restricted",
            ]
            for field in expected_fields:
                assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_eccn_details_should_have_expected_fields(self) -> None:
        """Test that ECCN details output has expected fields."""
        tools = await mcp.get_tools()
        tool = tools["get_eccn_details"]
        result = await tool.fn(eccn="5A002")

        assert isinstance(result, dict)
        if "error" not in result:
            assert "eccn" in result
            assert "category" in result

    @pytest.mark.asyncio
    async def test_usml_category_should_have_expected_fields(self) -> None:
        """Test that USML category output has expected fields."""
        tools = await mcp.get_tools()
        tool = tools["get_usml_category_details"]
        result = await tool.fn(category="I")

        assert isinstance(result, dict)
        if "error" not in result:
            assert "category" in result
            assert "title" in result

    @pytest.mark.asyncio
    async def test_classification_suggestion_should_have_expected_structure(self) -> None:
        """Test that classification suggestion has expected structure."""
        tools = await mcp.get_tools()
        tool = tools["suggest_classification"]
        result = await tool.fn(item_description="encrypted communication device")

        assert isinstance(result, dict)
        assert "suggested_jurisdiction" in result
        assert "suggested_eccns" in result
        assert "disclaimer" in result

    @pytest.mark.asyncio
    async def test_cfr810_country_should_have_expected_structure(self) -> None:
        """Test that CFR810 country check has expected structure."""
        tools = await mcp.get_tools()
        tool = tools["check_cfr810_country"]
        result = await tool.fn(country="France")

        assert isinstance(result, dict)
        assert "country" in result
        if "error" not in result:
            assert "authorization_type" in result
            assert "guidance" in result


class TestMCPServerConfiguration:
    """Tests for MCP server configuration."""

    def test_should_have_server_name(self) -> None:
        """Test that server has a name."""
        assert mcp.name == "export-control-mcp"

    def test_should_have_instructions(self) -> None:
        """Test that server has instructions."""
        assert mcp.instructions is not None
        assert len(mcp.instructions) > 100

    @pytest.mark.asyncio
    async def test_should_list_all_tools(self) -> None:
        """Test that get_tools returns all registered tools."""
        tools = await mcp.get_tools()

        assert len(tools) > 0
        assert len(tools) >= 10  # We have at least 10+ tools registered


class TestToolCount:
    """Tests for expected tool count and categories."""

    @pytest.mark.asyncio
    async def test_should_have_minimum_tool_count(self) -> None:
        """Test that we have a reasonable number of tools registered."""
        tools = await mcp.get_tools()

        # We should have at least 15 tools across all categories
        assert len(tools) >= 15, f"Expected at least 15 tools, got {len(tools)}"

    @pytest.mark.asyncio
    async def test_all_tools_should_be_callable(self) -> None:
        """Test that all registered tools are async callables."""
        tools = await mcp.get_tools()

        for name, tool in tools.items():
            # Tool should have a fn attribute that is callable
            assert tool.fn is not None, f"Tool {name} has no function"
            assert callable(tool.fn), f"Tool {name} function is not callable"
