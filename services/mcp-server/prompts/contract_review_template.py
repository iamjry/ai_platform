"""
Contract Review Prompts and Templates
"""

CONTRACT_REVIEW_SYSTEM_PROMPT = """You are an expert contract review attorney with 20+ years of experience in commercial law, employment law, and contract negotiation. Your role is to analyze contracts thoroughly and provide clear, actionable advice.

Your analysis should be:
- Comprehensive: Cover all important aspects
- Risk-focused: Identify potential issues
- Practical: Provide actionable recommendations
- Clear: Use plain language
- Balanced: Note both risks and benefits

Always structure your response with:
1. Executive Summary
2. Contract Type & Overview
3. Key Terms Analysis
4. Risk Assessment
5. Compliance Issues
6. Recommendations
7. Risk Score (0-100)
"""

CONTRACT_ANALYSIS_PROMPT = """Analyze the following contract and provide a comprehensive review:

CONTRACT CONTENT:
{contract_content}

CONTRACT METADATA:
- File Name: {file_name}
- Parties: {parties}
- Dates Found: {dates}
- Key Amounts: {amounts}

Please provide:

1. **EXECUTIVE SUMMARY** (2-3 sentences)
   - Contract type and purpose
   - Overall assessment
   - Critical concerns if any

2. **CONTRACT OVERVIEW**
   - Contract Type: [specify]
   - Parties Involved: [list]
   - Key Dates: [list]
   - Financial Terms: [summarize]

3. **KEY TERMS ANALYSIS**
   For each major clause, provide:
   - Clause title and location
   - Summary
   - Implications
   - Fairness assessment

4. **RISK ASSESSMENT**
   Identify and categorize risks:
   - CRITICAL: [list with explanations]
   - HIGH: [list with explanations]
   - MEDIUM: [list with explanations]
   - LOW: [list with explanations]

5. **COMPLIANCE & MISSING CLAUSES**
   - Required clauses present: [list]
   - Missing important clauses: [list with why they matter]
   - Compliance concerns: [list]

6. **RECOMMENDATIONS**
   Priority actions:
   - MUST FIX: [critical changes]
   - SHOULD CONSIDER: [important improvements]
   - OPTIONAL: [nice-to-have clarifications]

7. **RISK SCORE**
   - Overall Score: [0-100]
   - Risk Level: [Low/Medium/High/Critical]
   - Justification: [explain score]

8. **NEXT STEPS**
   - Immediate actions
   - Items for negotiation
   - Questions to ask other party
"""

CLAUSE_ANALYSIS_PROMPT = """Analyze this specific contract clause in detail:

CLAUSE TEXT:
{clause_text}

CONTRACT CONTEXT:
{context}

Provide:

1. **CLAUSE SUMMARY**
   - Plain language explanation
   - Purpose and intent

2. **LEGAL IMPLICATIONS**
   - What this commits you to
   - What rights you're granting/receiving
   - Duration and scope

3. **RISK ANALYSIS**
   - Potential problems
   - Worst-case scenarios
   - Ambiguous language

4. **FAIRNESS ASSESSMENT**
   - Is this standard for the industry?
   - Is it balanced or one-sided?
   - Comparison to market norms

5. **RECOMMENDATIONS**
   - Suggested modifications
   - Alternative language
   - Questions to ask

6. **RED FLAGS** (if any)
   - Specific concerns
   - Why they matter
"""

CONTRACT_COMPARISON_PROMPT = """Compare these contracts and highlight differences:

CONTRACT A:
{contract_a}

CONTRACT B:
{contract_b}

Provide:

1. **KEY DIFFERENCES**
   - Terms that differ significantly
   - Which contract is more favorable
   - Important additions/omissions

2. **RISK COMPARISON**
   - Which contract has higher risk
   - Specific risk differences
   - Risk mitigation in each

3. **FINANCIAL COMPARISON**
   - Cost differences
   - Payment terms comparison
   - Value for money assessment

4. **RECOMMENDATION**
   - Which contract to choose
   - What to negotiate in preferred contract
   - Deal-breakers in either contract
"""

REPORT_GENERATION_PROMPT = """Generate a professional contract review report based on this analysis:

{analysis_data}

Create a formal report with:

# CONTRACT REVIEW REPORT

## Document Information
- Contract Title: [title]
- Review Date: [date]
- Reviewed By: AI Contract Analysis System

## Executive Summary
[2-3 paragraph summary of key findings]

## Contract Details
[Structured overview of contract]

## Findings
### Critical Issues
[List with details]

### High Priority Issues
[List with details]

### Medium Priority Items
[List with details]

## Compliance Status
[Checklist of required clauses]

## Financial Analysis
[Cost implications and payment terms]

## Risk Matrix
[Visual representation of risks]

## Recommendations
### Immediate Actions Required
[Prioritized list]

### Suggested Modifications
[Clause by clause]

### Questions for Negotiation
[List of discussion points]

## Conclusion
[Final recommendation and risk score]

## Appendices
- Glossary of Legal Terms
- Relevant Legal Standards
- Industry Benchmarks

Format as professional Markdown document.
"""

def get_contract_review_prompt(contract_data: dict) -> str:
    """Generate contract review prompt from parsed data"""
    return CONTRACT_ANALYSIS_PROMPT.format(
        contract_content=contract_data.get('raw_content', '')[:8000],  # Limit size
        file_name=contract_data.get('file_name', 'Unknown'),
        parties=', '.join(contract_data.get('parties', ['Not specified'])),
        dates=', '.join(contract_data.get('dates', ['Not found'])),
        amounts=', '.join(contract_data.get('amounts', ['Not specified']))
    )

def get_clause_analysis_prompt(clause_text: str, context: str = "") -> str:
    """Generate clause analysis prompt"""
    return CLAUSE_ANALYSIS_PROMPT.format(
        clause_text=clause_text,
        context=context
    )

def get_comparison_prompt(contract_a: str, contract_b: str) -> str:
    """Generate contract comparison prompt"""
    return CONTRACT_COMPARISON_PROMPT.format(
        contract_a=contract_a[:4000],  # Limit size
        contract_b=contract_b[:4000]
    )

def get_report_prompt(analysis_data: str) -> str:
    """Generate report generation prompt"""
    return REPORT_GENERATION_PROMPT.format(
        analysis_data=analysis_data
    )
