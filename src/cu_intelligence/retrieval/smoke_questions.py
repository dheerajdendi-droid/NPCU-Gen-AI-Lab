"""Small named Gate 3 retrieval smoke set; this is not an evaluation framework."""

from typing import NamedTuple


class RetrievalSmokeQuestion(NamedTuple):
    """One synthetic query and the document expected to contain useful evidence."""

    name: str
    query: str
    expected_document_id: str


RETRIEVAL_SMOKE_QUESTIONS = (
    RetrievalSmokeQuestion(
        name="member-eligibility",
        query="What evidence is needed to establish member eligibility?",
        expected_document_id="01_Member_Eligibility_Onboarding_Policy_v2.2",
    ),
    RetrievalSmokeQuestion(
        name="lending-affordability",
        query="How should lending affordability and income be assessed?",
        expected_document_id="02_Lending_Affordability_Policy_v4.0",
    ),
    RetrievalSmokeQuestion(
        name="vulnerable-members",
        query="What support should be offered to vulnerable members making complaints?",
        expected_document_id="05_Complaints_Vulnerable_Members_Policy_v1.8",
    ),
    RetrievalSmokeQuestion(
        name="supplier-change",
        query="What controls apply to supplier-related IT changes?",
        expected_document_id="10_IT_Change_Supplier_Management_Procedure_v1.6",
    ),
)
