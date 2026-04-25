.PHONY: install dev test lint clean run-mcp demo

install:
	pip install -e .

install-all:
	pip install -e ".[all]"

dev:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

lint:
	ruff check telescope_ai/ mcp_server/
	ruff format --check telescope_ai/ mcp_server/

format:
	ruff format telescope_ai/ mcp_server/

run-mcp:
	fastmcp run mcp_server/server.py:mcp

run-mcp-http:
	fastmcp run mcp_server/server.py:mcp --transport http --host 127.0.0.1 --port 8080

demo:
	telescope-ai demo

clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
