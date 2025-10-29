# Contract Review Agent - User Guide

## Overview

The Contract Review Agent is an AI-powered tool that analyzes contracts to identify risks, ensure compliance, and provide actionable recommendations. It supports various contract types and provides comprehensive analysis.

## Features

### ✅ Comprehensive Analysis
- Identifies unfair and risky clauses
- Detects ambiguous language
- Checks for missing critical clauses
- Calculates overall risk score

### ✅ Multiple Contract Types
- Employment agreements
- Non-Disclosure Agreements (NDA)
- Service agreements
- Lease agreements
- Sales contracts
- General contracts

### ✅ Risk Assessment
- Automated pattern matching
- AI-powered clause analysis
- Risk scoring (0-100)
- Prioritized recommendations

### ✅ Compliance Checking
- Industry standard validation
- Required clause verification
- Legal compliance review

## Available Tools

### 1. review_contract

Comprehensively review a contract.

**Parameters:**
- `contract_content` (required): Full text of the contract
- `contract_name` (optional): Contract identifier
- `contract_type` (optional): Type of contract (employment/nda/service/lease/sales/general)

**Example:**
```json
{
  "tool": "review_contract",
  "parameters": {
    "contract_content": "EMPLOYMENT AGREEMENT\n\nThis Employment Agreement...",
    "contract_name": "Software Engineer Employment Contract",
    "contract_type": "employment"
  }
}
```

**Returns:**
```json
{
  "contract_name": "Software Engineer Employment Contract",
  "contract_type": "employment",
  "risk_score": {
    "score": 35,
    "level": "Medium",
    "breakdown": {
      "critical_issues": 0,
      "high_issues": 2,
      "medium_issues": 3,
      "low_issues": 1,
      "missing_clauses": 1
    }
  },
  "risk_analysis": {
    "critical": [],
    "high": [
      {
        "type": "unfair_clause",
        "text": "unlimited liability",
        "description": "Unlimited liability exposure",
        "recommendation": "Cap liability at a specific amount"
      }
    ],
    "medium": [...],
    "low": [...]
  },
  "missing_clauses": ["benefits"],
  "recommendations": [
    {
      "priority": "MUST FIX",
      "issue": "Unlimited liability exposure",
      "action": "Cap liability at a specific amount"
    }
  ],
  "llm_analysis": "Detailed AI analysis..."
}
```

### 2. analyze_clause

Analyze a specific clause in detail.

**Parameters:**
- `clause_text` (required): The clause to analyze
- `context` (optional): Additional context

**Example:**
```json
{
  "tool": "analyze_clause",
  "parameters": {
    "clause_text": "The Employee agrees to a non-compete period of 5 years following termination.",
    "context": "Employment agreement for software engineer"
  }
}
```

### 3. compare_contracts

Compare two contracts side by side.

**Parameters:**
- `contract_a` (required): First contract
- `contract_b` (required): Second contract

**Example:**
```json
{
  "tool": "compare_contracts",
  "parameters": {
    "contract_a": "Contract A text...",
    "contract_b": "Contract B text..."
  }
}
```

## Risk Scoring

### Score Ranges
- **0-24**: Low Risk ✅
- **25-49**: Medium Risk ⚠️
- **50-74**: High Risk 🔴
- **75-100**: Critical Risk 🚨

### Risk Factors
- Critical issues: +25 points each
- High-risk issues: +15 points each
- Medium issues: +10 points each
- Low issues: +5 points each
- Missing clauses: +10 points each

## Common Risk Patterns

### Critical Risks
- Unlimited liability
- Perpetual obligations
- Waiver of all rights
- Unilateral termination rights

### High Risks
- Sole discretion clauses
- Automatic renewal without notice
- Broad non-compete clauses
- No termination clause

### Medium Risks
- Ambiguous language
- Missing definitions
- Vague scope of work
- No force majeure clause

## Usage Examples

### Example 1: Review Employment Contract

```python
# Via API
response = await mcp_client.call_tool(
    "review_contract",
    contract_content="""
    EMPLOYMENT AGREEMENT

    This Employment Agreement is entered into between ABC Corp
    and John Doe.

    1. POSITION AND DUTIES
    Employee shall serve as Software Engineer.

    2. COMPENSATION
    Base salary of $120,000 per year.

    3. TERMINATION
    Either party may terminate at will with 30 days notice.

    4. NON-COMPETE
    Employee agrees not to work for competitors for 2 years
    after termination in the same geographic area.
    """,
    contract_name="John Doe Employment Agreement",
    contract_type="employment"
)

print(response)
```

### Example 2: Analyze Specific Clause

```python
response = await mcp_client.call_tool(
    "analyze_clause",
    clause_text="""
    INDEMNIFICATION: The Contractor agrees to indemnify,
    defend, and hold harmless the Company, its officers,
    directors, and employees from and against any and all
    claims, damages, losses, and expenses, including
    reasonable attorneys' fees.
    """,
    context="Service agreement for consulting services"
)

print(response)
```

### Example 3: Compare Two Offers

```python
response = await mcp_client.call_tool(
    "compare_contracts",
    contract_a=offer_letter_company_a,
    contract_b=offer_letter_company_b
)

print(response)
```

## Best Practices

### 1. Provide Complete Context
- Include entire contract text when possible
- Specify contract type for better analysis
- Add relevant context for clause analysis

### 2. Review All Recommendations
- Pay special attention to "MUST FIX" items
- Consider "SHOULD CONSIDER" items carefully
- Negotiate based on risk score

### 3. Consult Legal Professionals
- This tool assists but doesn't replace lawyers
- For important contracts, get legal review
- Use this for initial screening

### 4. Check for Updates
- Contract law varies by jurisdiction
- Industry standards evolve
- Keep tool's risk patterns updated

## Integration with Agent Service

The Contract Review tools can be used within agent conversations:

```
User: Please review this employment contract

Agent: I'll review the contract for you using the contract review tool.
[Calls review_contract tool]
[Analyzes results]
[Presents findings to user]

Based on the analysis, this contract has a medium risk score of 35/100.
The main concerns are:
1. [Issue 1]
2. [Issue 2]

I recommend:
1. [Recommendation 1]
2. [Recommendation 2]
```

## API Endpoints

### Direct API Access

```bash
# Review contract
curl -X POST http://localhost:8001/tools/review_contract \
  -H "Content-Type: application/json" \
  -d '{
    "contract_content": "contract text...",
    "contract_type": "employment"
  }'

# Analyze clause
curl -X POST http://localhost:8001/tools/analyze_clause \
  -H "Content-Type: application/json" \
  -d '{
    "clause_text": "clause text..."
  }'
```

## Troubleshooting

### Common Issues

**Issue: "LLM analysis not available"**
- Solution: Ensure LiteLLM service is running
- Check API keys in environment variables

**Issue: "Unsupported file format"**
- Solution: Currently supports text input only
- Convert PDF/DOCX to text before submitting

**Issue: "Analysis too long"**
- Solution: Submit contract in sections
- Use analyze_clause for specific parts

## Limitations

- Text-based analysis only (no image/signature analysis)
- English language contracts primarily
- General legal principles (not jurisdiction-specific)
- Assists but doesn't replace legal counsel
- May miss context-dependent nuances

## Future Enhancements

- [ ] File upload support (PDF, DOCX)
- [ ] Multi-language support
- [ ] Jurisdiction-specific rules
- [ ] Visual contract comparison
- [ ] Redline generation
- [ ] Clause library
- [ ] Industry-specific templates

## Support

For issues or questions:
1. Check logs: `/var/log/mcp-server/contract_review.log`
2. Review error messages
3. Consult documentation
4. Contact support team

---

**Version:** 1.0.0
**Last Updated:** 2025-10-29
**Author:** AI Platform Team
