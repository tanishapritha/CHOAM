from app.mcp.server import main, mcp


def test_mcp_server_exposes_a_callable_entrypoint():
    assert callable(main)
    assert callable(mcp.run)
