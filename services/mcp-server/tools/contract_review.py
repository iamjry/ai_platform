"""
Contract Review MCP Tools
AI-powered contract analysis and review
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Import utilities
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.contract_parser import ContractParser, parse_contract_text
from prompts.contract_review_template import (
    CONTRACT_REVIEW_SYSTEM_PROMPT,
    get_contract_review_prompt,
    get_clause_analysis_prompt,
    get_comparison_prompt,
    get_report_prompt
)

logger = logging.getLogger(__name__)

# Load risk patterns
RISK_PATTERNS_PATH = Path(__file__).parent.parent / "data" / "risk_patterns.json"
with open(RISK_PATTERNS_PATH, 'r') as f:
    RISK_PATTERNS = json.load(f)


class ContractReviewer:
    """Main contract review engine"""

    def __init__(self, llm_client=None):
        self.parser = ContractParser()
        self.llm = llm_client
        self.risk_patterns = RISK_PATTERNS

    async def review_contract(
        self,
        contract_content: str,
        contract_name: str = "Contract",
        contract_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive contract review

        Args:
            contract_content: The contract text
            contract_name: Identifier for the contract
            contract_type: Type of contract (employment, nda, service, etc.)

        Returns:
            Complete review analysis
        """
        try:
            # Parse contract
            parsed_data = parse_contract_text(contract_content, contract_name)

            # Automated risk analysis
            risk_analysis = self._analyze_risks(contract_content)

            # Check required clauses
            missing_clauses = self._check_required_clauses(
                contract_content, contract_type
            )

            # LLM-based analysis
            llm_analysis = await self._get_llm_analysis(parsed_data)

            # Calculate risk score
            risk_score = self._calculate_risk_score(
                risk_analysis, missing_clauses
            )

            return {
                "contract_name": contract_name,
                "contract_type": contract_type or "general",
                "parsed_data": parsed_data,
                "risk_analysis": risk_analysis,
                "missing_clauses": missing_clauses,
                "llm_analysis": llm_analysis,
                "risk_score": risk_score,
                "recommendations": self._generate_recommendations(
                    risk_analysis, missing_clauses
                )
            }

        except Exception as e:
            logger.error(f"Error reviewing contract: {str(e)}")
            raise

    def _analyze_risks(self, content: str) -> Dict[str, List]:
        """Analyze contract for risk patterns"""
        risks = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

        # Check high-risk keywords
        for keyword in self.risk_patterns["high_risk_keywords"]:
            if re.search(rf'\b{re.escape(keyword)}\b', content, re.IGNORECASE):
                risks["high"].append({
                    "type": "keyword",
                    "text": keyword,
                    "description": f"Contains high-risk term: '{keyword}'"
                })

        # Check unfair clauses
        for clause in self.risk_patterns["unfair_clauses"]:
            matches = re.finditer(clause["pattern"], content, re.IGNORECASE)
            for match in matches:
                risk_level = clause["risk_level"]
                risks[risk_level].append({
                    "type": "unfair_clause",
                    "text": match.group(),
                    "description": clause["description"],
                    "recommendation": clause["recommendation"]
                })

        # Check ambiguous terms
        ambiguous_count = 0
        for term in self.risk_patterns["ambiguous_terms"]:
            count = len(re.findall(rf'\b{re.escape(term)}\b', content, re.IGNORECASE))
            ambiguous_count += count

        if ambiguous_count > 10:
            risks["medium"].append({
                "type": "ambiguous_language",
                "text": f"{ambiguous_count} ambiguous terms found",
                "description": "Contract contains excessive ambiguous language",
                "recommendation": "Replace ambiguous terms with specific definitions"
            })

        return risks

    def _check_required_clauses(
        self, content: str, contract_type: Optional[str]
    ) -> List[str]:
        """Check for missing required clauses"""
        if not contract_type or contract_type not in self.risk_patterns["required_clauses"]:
            return []

        required = self.risk_patterns["required_clauses"][contract_type]
        missing = []

        for clause_name in required:
            # Simple keyword check (can be improved)
            if not re.search(rf'\b{re.escape(clause_name)}\b', content, re.IGNORECASE):
                missing.append(clause_name)

        return missing

    async def _get_llm_analysis(self, parsed_data: Dict) -> str:
        """Get LLM analysis of contract"""
        if not self.llm:
            return "LLM analysis not available"

        try:
            prompt = get_contract_review_prompt(parsed_data)

            response = await self.llm.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": CONTRACT_REVIEW_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            return f"Error performing LLM analysis: {str(e)}"

    def _calculate_risk_score(
        self, risk_analysis: Dict, missing_clauses: List
    ) -> Dict[str, Any]:
        """Calculate overall risk score"""
        scoring = self.risk_patterns["risk_scoring"]

        total_score = 0
        total_score += len(risk_analysis["critical"]) * scoring["critical"]
        total_score += len(risk_analysis["high"]) * scoring["high"]
        total_score += len(risk_analysis["medium"]) * scoring["medium"]
        total_score += len(risk_analysis["low"]) * scoring["low"]
        total_score += len(missing_clauses) * scoring["medium"]

        # Normalize to 0-100
        score = min(total_score, 100)

        if score >= 75:
            level = "Critical"
        elif score >= 50:
            level = "High"
        elif score >= 25:
            level = "Medium"
        else:
            level = "Low"

        return {
            "score": score,
            "level": level,
            "breakdown": {
                "critical_issues": len(risk_analysis["critical"]),
                "high_issues": len(risk_analysis["high"]),
                "medium_issues": len(risk_analysis["medium"]),
                "low_issues": len(risk_analysis["low"]),
                "missing_clauses": len(missing_clauses)
            }
        }

    def _generate_recommendations(
        self, risk_analysis: Dict, missing_clauses: List
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations"""
        recommendations = []

        # Critical and high risks first
        for risk in risk_analysis["critical"] + risk_analysis["high"]:
            recommendations.append({
                "priority": "MUST FIX",
                "issue": risk.get("description", ""),
                "action": risk.get("recommendation", "Review and modify this clause")
            })

        # Missing clauses
        for clause in missing_clauses:
            recommendations.append({
                "priority": "MUST ADD",
                "issue": f"Missing required clause: {clause}",
                "action": f"Add {clause} clause to contract"
            })

        # Medium risks
        for risk in risk_analysis["medium"][:5]:  # Limit to top 5
            recommendations.append({
                "priority": "SHOULD CONSIDER",
                "issue": risk.get("description", ""),
                "action": risk.get("recommendation", "Review this item")
            })

        return recommendations


# MCP Tool Functions

async def review_contract_tool(
    contract_content: str,
    contract_name: str = "Untitled Contract",
    contract_type: Optional[str] = None,
    llm_client=None
) -> str:
    """
    Review a contract and provide comprehensive analysis

    Args:
        contract_content: Full text of the contract
        contract_name: Name/identifier for the contract
        contract_type: Type (employment/nda/service/lease/sales)
        llm_client: LLM client for AI analysis

    Returns:
        JSON string with review results
    """
    try:
        reviewer = ContractReviewer(llm_client)
        result = await reviewer.review_contract(
            contract_content, contract_name, contract_type
        )

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        logger.error(f"Contract review error: {str(e)}")
        return json.dumps({"error": str(e)})


async def analyze_clause_tool(
    clause_text: str,
    context: str = "",
    llm_client=None
) -> str:
    """
    Analyze a specific contract clause

    Args:
        clause_text: The clause to analyze
        context: Additional context about the contract
        llm_client: LLM client

    Returns:
        Analysis of the clause
    """
    try:
        if not llm_client:
            return json.dumps({"error": "LLM client required for clause analysis"})

        prompt = get_clause_analysis_prompt(clause_text, context)

        response = await llm_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": CONTRACT_REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Clause analysis error: {str(e)}")
        return json.dumps({"error": str(e)})


async def compare_contracts_tool(
    contract_a: str,
    contract_b: str,
    llm_client=None
) -> str:
    """
    Compare two contracts

    Args:
        contract_a: First contract text
        contract_b: Second contract text
        llm_client: LLM client

    Returns:
        Comparison analysis
    """
    try:
        if not llm_client:
            return json.dumps({"error": "LLM client required for comparison"})

        prompt = get_comparison_prompt(contract_a, contract_b)

        response = await llm_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": CONTRACT_REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Contract comparison error: {str(e)}")
        return json.dumps({"error": str(e)})


# Tool metadata for MCP registration
CONTRACT_REVIEW_TOOLS = [
    {
        "name": "review_contract",
        "description": "Comprehensively review and analyze a contract for risks, compliance, and fairness",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_content": {
                    "type": "string",
                    "description": "Full text of the contract to review"
                },
                "contract_name": {
                    "type": "string",
                    "description": "Name or identifier for the contract",
                    "default": "Untitled Contract"
                },
                "contract_type": {
                    "type": "string",
                    "enum": ["employment", "nda", "service", "lease", "sales", "general"],
                    "description": "Type of contract for specialized analysis"
                }
            },
            "required": ["contract_content"]
        },
        "handler": review_contract_tool
    },
    {
        "name": "analyze_clause",
        "description": "Analyze a specific contract clause in detail",
        "parameters": {
            "type": "object",
            "properties": {
                "clause_text": {
                    "type": "string",
                    "description": "The specific clause to analyze"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context about the contract"
                }
            },
            "required": ["clause_text"]
        },
        "handler": analyze_clause_tool
    },
    {
        "name": "compare_contracts",
        "description": "Compare two contracts and highlight key differences",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_a": {
                    "type": "string",
                    "description": "First contract text"
                },
                "contract_b": {
                    "type": "string",
                    "description": "Second contract text"
                }
            },
            "required": ["contract_a", "contract_b"]
        },
        "handler": compare_contracts_tool
    }
]
