# Contract Review Integration Guide

## Quick Start

### 1. Verify Dependencies

```bash
cd services/mcp-server
pip install -r requirements.txt
```

### 2. Import and Use

```python
from tools.contract_review import CONTRACT_REVIEW_TOOLS, review_contract_tool

# Register tools with MCP server
for tool in CONTRACT_REVIEW_TOOLS:
    register_tool(tool)

# Use the tool
result = await review_contract_tool(
    contract_content="YOUR CONTRACT TEXT HERE",
    contract_type="employment",
    llm_client=your_llm_client
)
```

### 3. Register with MCP Server

Add to `services/mcp-server/main.py`:

```python
from tools.contract_review import CONTRACT_REVIEW_TOOLS

# In your tool registration section
for tool_config in CONTRACT_REVIEW_TOOLS:
    app.add_tool(
        name=tool_config["name"],
        description=tool_config["description"],
        parameters=tool_config["parameters"],
        handler=tool_config["handler"]
    )
```

## API Endpoints

Once integrated, these endpoints will be available:

- `POST /tools/review_contract`
- `POST /tools/analyze_clause`
- `POST /tools/compare_contracts`

## Testing

```bash
# Run tests
cd services/mcp-server
python tests/test_contract_review.py

# Run with pytest
pytest tests/test_contract_review.py -v
```

## Example Usage via Agent

```
User: Please review this employment contract:
[paste contract]

Agent: I'll analyze that contract for you.
[Calls review_contract tool]
[Presents analysis with risk score and recommendations]
```

## Files Created

- `utils/contract_parser.py` - Contract parsing utilities
- `tools/contract_review.py` - Main review tools
- `data/risk_patterns.json` - Risk pattern database
- `prompts/contract_review_template.py` - AI prompts
- `docs/CONTRACT_REVIEW_GUIDE.md` - User guide
- `tests/test_contract_review.py` - Test suite

## Next Steps

1. Rebuild MCP server Docker image
2. Restart MCP server service
3. Test via API or agent interface
4. Customize risk patterns as needed

---

**Version:** 1.0.0
**Status:** Ready for Integration
