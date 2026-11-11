from app.mcp.server import mcp


def test_mcp_server_registers_expected_read_only_tools():
    tool_names = {tool.name for tool in mcp._tool_manager.list_tools()}
    assert {
        "preview_purchase_intent",
        "get_purchase_request",
        "list_negotiation_offers",
        "check_purchase_integrity",
    } <= tool_names
