"""
Test Contract Review Functionality
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.contract_review import (
    ContractReviewer,
    review_contract_tool,
    analyze_clause_tool
)
from utils.contract_parser import parse_contract_text


# Sample test contracts
SAMPLE_EMPLOYMENT_CONTRACT = """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is entered into as of January 1, 2024,
between Tech Solutions Inc. ("Company") and John Smith ("Employee").

1. POSITION AND DUTIES
Employee shall serve as Senior Software Engineer and shall perform duties
as assigned by the Company at its sole discretion.

2. COMPENSATION
Base salary of $150,000 per year, payable bi-weekly.

3. TERMINATION
Company may terminate this agreement at any time without cause or notice.
Upon termination, Employee forfeits all unvested stock options.

4. NON-COMPETE
Employee agrees not to work for any competing business for 5 years
after termination, anywhere in the world.

5. CONFIDENTIALITY
Employee shall keep all Company information confidential in perpetuity.

6. INDEMNIFICATION
Employee agrees to indemnify Company for any and all losses with
unlimited liability.

7. INTELLECTUAL PROPERTY
All work product created by Employee belongs solely to Company,
including work done outside business hours.

8. DISPUTE RESOLUTION
Any disputes shall be resolved through binding arbitration in
Company's jurisdiction, with Employee waiving all rights to appeal.
"""

SAMPLE_NDA = """
NON-DISCLOSURE AGREEMENT

Between:
- Disclosing Party: ACME Corporation
- Receiving Party: Beta Solutions LLC

1. CONFIDENTIAL INFORMATION
All information shared shall be considered confidential.

2. OBLIGATIONS
Receiving Party shall protect confidential information.

3. TERM
This agreement shall last for 10 years from signing.

4. RETURN OF MATERIALS
Upon request, all materials shall be returned.
"""


class TestContractParser:
    """Test contract parsing functionality"""

    def test_parse_employment_contract(self):
        """Test parsing employment contract"""
        result = parse_contract_text(
            SAMPLE_EMPLOYMENT_CONTRACT,
            "Test Employment Contract"
        )

        assert result is not None
        assert result['file_name'] == "Test Employment Contract"
        assert len(result['parties']) > 0
        assert result['word_count'] > 0

    def test_parse_nda(self):
        """Test parsing NDA"""
        result = parse_contract_text(SAMPLE_NDA, "Test NDA")

        assert result is not None
        assert len(result['parties']) >= 2
        assert 'ACME Corporation' in str(result['parties'])


class TestRiskAnalysis:
    """Test risk analysis functionality"""

    def test_detect_high_risk_keywords(self):
        """Test detection of high-risk keywords"""
        reviewer = ContractReviewer()
        risks = reviewer._analyze_risks(SAMPLE_EMPLOYMENT_CONTRACT)

        # Should detect multiple risks
        assert len(risks['high']) > 0 or len(risks['critical']) > 0

        # Check for specific risks
        all_risks = (
            risks['critical'] + risks['high'] +
            risks['medium'] + risks['low']
        )
        risk_texts = [r.get('text', '').lower() for r in all_risks]

        # Should detect unlimited liability
        assert any('unlimited' in text for text in risk_texts)

    def test_detect_unfair_clauses(self):
        """Test detection of unfair clauses"""
        reviewer = ContractReviewer()
        risks = reviewer._analyze_risks(SAMPLE_EMPLOYMENT_CONTRACT)

        # Employment contract has multiple unfair clauses
        total_issues = sum([
            len(risks['critical']),
            len(risks['high']),
            len(risks['medium'])
        ])

        assert total_issues > 0

    def test_check_missing_clauses(self):
        """Test detection of missing required clauses"""
        reviewer = ContractReviewer()
        missing = reviewer._check_required_clauses(
            SAMPLE_NDA,
            "nda"
        )

        # Should check for required NDA clauses
        assert isinstance(missing, list)

    def test_risk_score_calculation(self):
        """Test risk score calculation"""
        reviewer = ContractReviewer()
        risks = reviewer._analyze_risks(SAMPLE_EMPLOYMENT_CONTRACT)
        missing = reviewer._check_required_clauses(
            SAMPLE_EMPLOYMENT_CONTRACT,
            "employment"
        )

        score = reviewer._calculate_risk_score(risks, missing)

        assert 'score' in score
        assert 'level' in score
        assert 0 <= score['score'] <= 100
        assert score['level'] in ['Low', 'Medium', 'High', 'Critical']


class TestContractReviewTool:
    """Test complete contract review"""

    @pytest.mark.asyncio
    async def test_review_employment_contract(self):
        """Test full review of employment contract"""
        result = await review_contract_tool(
            contract_content=SAMPLE_EMPLOYMENT_CONTRACT,
            contract_name="Test Employment Agreement",
            contract_type="employment",
            llm_client=None  # Run without LLM for unit test
        )

        import json
        data = json.loads(result)

        assert 'contract_name' in data
        assert 'risk_score' in data
        assert 'risk_analysis' in data
        assert 'recommendations' in data

    @pytest.mark.asyncio
    async def test_review_nda(self):
        """Test full review of NDA"""
        result = await review_contract_tool(
            contract_content=SAMPLE_NDA,
            contract_name="Test NDA",
            contract_type="nda",
            llm_client=None
        )

        import json
        data = json.loads(result)

        assert data['contract_type'] == 'nda'
        assert 'risk_score' in data


class TestRecommendations:
    """Test recommendation generation"""

    def test_generate_recommendations(self):
        """Test recommendation generation"""
        reviewer = ContractReviewer()
        risks = reviewer._analyze_risks(SAMPLE_EMPLOYMENT_CONTRACT)
        missing = reviewer._check_required_clauses(
            SAMPLE_EMPLOYMENT_CONTRACT,
            "employment"
        )

        recommendations = reviewer._generate_recommendations(risks, missing)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Check recommendation structure
        if recommendations:
            rec = recommendations[0]
            assert 'priority' in rec
            assert 'issue' in rec
            assert 'action' in rec
            assert rec['priority'] in ['MUST FIX', 'MUST ADD', 'SHOULD CONSIDER']


# Sample contracts for manual testing
SAMPLE_CONTRACTS = {
    "employment": SAMPLE_EMPLOYMENT_CONTRACT,
    "nda": SAMPLE_NDA
}


def print_test_results():
    """Print sample analysis for manual review"""
    print("\n" + "="*60)
    print("SAMPLE CONTRACT ANALYSIS")
    print("="*60 + "\n")

    reviewer = ContractReviewer()

    for contract_type, content in SAMPLE_CONTRACTS.items():
        print(f"\n{'='*60}")
        print(f"Contract Type: {contract_type.upper()}")
        print(f"{'='*60}\n")

        risks = reviewer._analyze_risks(content)
        missing = reviewer._check_required_clauses(content, contract_type)
        score = reviewer._calculate_risk_score(risks, missing)
        recommendations = reviewer._generate_recommendations(risks, missing)

        print(f"Risk Score: {score['score']}/100 - {score['level']}")
        print(f"\nBreakdown:")
        print(f"  Critical: {score['breakdown']['critical_issues']}")
        print(f"  High: {score['breakdown']['high_issues']}")
        print(f"  Medium: {score['breakdown']['medium_issues']}")
        print(f"  Low: {score['breakdown']['low_issues']}")
        print(f"  Missing Clauses: {score['breakdown']['missing_clauses']}")

        if risks['critical'] or risks['high']:
            print(f"\n🚨 Major Issues Found:")
            for issue in (risks['critical'] + risks['high'])[:3]:
                print(f"  - {issue.get('description', 'Unknown issue')}")

        if recommendations:
            print(f"\n📋 Top Recommendations:")
            for rec in recommendations[:5]:
                print(f"  [{rec['priority']}] {rec['issue']}")
                print(f"    → {rec['action']}\n")


if __name__ == "__main__":
    # Run pytest
    pytest.main([__file__, "-v"])

    # Print sample results
    print_test_results()
