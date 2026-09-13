"""Minimal Streamlit coursework demonstration for the accepted NPCU RAG path."""

import logging

import streamlit as st

from cu_intelligence.generation import AnswerStatus, GenerationError
from cu_intelligence.retrieval import RetrievalError
from cu_intelligence.ui.service import (
    CourseworkDemoResult,
    build_live_coursework_demo_service,
    evidence_preview,
)

LOGGER = logging.getLogger(__name__)

EXAMPLE_QUESTIONS = (
    "What is the current maximum Join and Borrow loan for a new member?",
    "What minimum internal risk score applies to Join and Borrow?",
    "What should happen when a payroll processing failure causes loan payments to be missed?",
    "When is PAR30 considered red?",
    "What is the policy for cryptocurrency investment?",
)


@st.cache_resource(show_spinner=False)
def _service():
    return build_live_coursework_demo_service()


def _render_result(result: CourseworkDemoResult) -> None:
    answer = result.answer
    evidence_by_chunk_id = {item.chunk_id: item for item in result.evidence}
    st.subheader("Answer")
    if answer.status is AnswerStatus.INSUFFICIENT_EVIDENCE:
        st.warning(answer.insufficient_evidence_explanation)
    else:
        for statement in answer.statements:
            markers = " ".join(f"[{number}]" for number in statement.citation_numbers)
            st.markdown(f"{statement.text} {markers}")

        st.subheader("Sources")
        for citation in answer.citations:
            status = citation.document_status.value
            source_evidence = evidence_by_chunk_id.get(citation.chunk_id)
            with st.container(border=True):
                st.markdown(f"**{citation.citation_number}. {citation.title}**")
                st.caption(
                    f"Version {citation.version} · {status} · Page {citation.page_number}"
                )
                if source_evidence is not None:
                    st.caption(
                        f"Effective date: {source_evidence.effective_date.isoformat()}"
                    )
                st.caption(f"Source: {citation.source_filename}")

    with st.expander("View retrieval details"):
        if not result.evidence:
            st.caption("No retrieval evidence was returned.")
        for item in result.evidence:
            st.markdown(
                f"**Rank {item.rank}: {item.title}**  \n"
                f"Version {item.version} · {item.document_status.value} · "
                f"Page {item.page_number} · Score {item.similarity_score:.4f}"
            )
            st.caption(evidence_preview(item))
            st.divider()


def main() -> None:
    st.set_page_config(
        page_title="NPCU Policy Intelligence Assistant",
        page_icon="📚",
        layout="centered",
    )
    st.title("NPCU Policy Intelligence Assistant")
    st.markdown("Ask questions against the synthetic NPCU policy knowledge base.")
    st.info(
        "This demonstration uses synthetic credit-union policies and contains no real member data."
    )

    with st.form("policy-question-form"):
        question = st.text_input(
            "Ask a policy question",
            placeholder="What is the current Join and Borrow limit?",
        )
        submitted = st.form_submit_button("Ask", type="primary")

    if submitted:
        if not question.strip():
            st.warning("Enter a policy question before selecting Ask.")
        else:
            try:
                with st.spinner("Searching the policy knowledge base…"):
                    result = _service().ask(question)
                _render_result(result)
            except (RetrievalError, GenerationError):
                LOGGER.exception("The coursework demo request failed")
                st.error(
                    "The policy service is temporarily unavailable. Check the configured "
                    "provider connection and try again."
                )
            except Exception:  # keep unexpected details out of the UI
                LOGGER.exception("Unexpected coursework demo failure")
                st.error("Something unexpected went wrong. Review the local application log.")

    st.divider()
    st.subheader("Example questions")
    for example in EXAMPLE_QUESTIONS:
        st.markdown(f"- {example}")
    st.caption(
        "The final example is intentionally outside the policy corpus and should demonstrate "
        "the insufficient-evidence response."
    )


if __name__ == "__main__":
    main()
