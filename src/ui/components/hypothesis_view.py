"""Goal-Driven Hypothesis Testing Component (Backward Chaining).

Allows clinicians or students to interrogate the knowledge base with target hypotheses:
- E.g., 'Is EMERGENCY triage supported for this patient?'
- E.g., 'What missing observations would be required to prove URGENT triage?'
"""

from typing import Any, Dict, Optional
import streamlit as st
from src.config import TriageUrgency
from src.triage_coordinator import TriageCoordinator


def render_hypothesis_view(
    coordinator: TriageCoordinator,
    observations: Dict[str, Any],
    observation_cfs: Optional[Dict[str, float]] = None,
) -> None:
    """Render backward chaining hypothesis explorer."""
    st.markdown("### 🎯 Goal-Driven Hypothesis Testing (Backward Chaining)")
    st.markdown(
        "Interrogate the knowledge base to test whether specific triage acuities or clinical findings "
        "can be formally proved from current working memory."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        target_urgency = st.selectbox(
            "Select Triage Urgency Hypothesis to Prove",
            options=[
                TriageUrgency.EMERGENCY.value,
                TriageUrgency.VERY_URGENT.value,
                TriageUrgency.URGENT.value,
                TriageUrgency.STANDARD.value,
                TriageUrgency.SELF_CARE.value,
            ],
            index=0,
            help="Select the goal hypothesis for backward chaining."
        )

    with col2:
        st.write("")
        st.write("")
        run_query = st.button("🚀 Evaluate Hypothesis via Backward Chaining")

    if run_query:
        with st.spinner("Running recursive backward chaining engine..."):
            trace = coordinator.prove_hypothesis(
                goal_attribute="triage_urgency",
                goal_value=target_urgency,
                observations=observations,
                observation_cfs=observation_cfs,
            )

        st.markdown("---")
        st.markdown("#### 🏁 Hypothesis Proof Outcome")

        if trace.proved:
            st.success(
                f"✅ **GOAL PROVED**: The hypothesis `{trace.goal_attribute} == {trace.goal_value}` "
                f"is mathematically supported with Certainty Factor **CF = {trace.final_cf:.2f}**."
            )
        else:
            st.warning(
                f"❌ **GOAL NOT PROVED**: The hypothesis `{trace.goal_attribute} == {trace.goal_value}` "
                f"cannot be established with sufficient certainty from current working memory."
            )

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### 📜 Supporting Production Rules")
            if trace.supporting_rules:
                for r_id in trace.supporting_rules:
                    rule_obj = coordinator.kb.get_rule(r_id)
                    rule_name = rule_obj.name if rule_obj else r_id
                    st.write(f"- `{r_id}`: **{rule_name}**")
            else:
                st.write("No production rules currently conclude this goal from known facts.")

        with col_b:
            st.markdown("##### ❓ Missing Evidence Required to Prove Goal")
            if trace.missing_facts_required:
                st.info(
                    "The following observations are currently `UNKNOWN` in working memory. "
                    "Gathering these findings could substantiate or refute this goal:"
                )
                for missing in trace.missing_facts_required:
                    st.write(f"- 🔍 **`{missing}`**")
            else:
                st.write("No additional missing evidence identified.")

        st.markdown("##### 🔎 Candidate Rules Examined in Goal Stack")
        st.write(", ".join([f"`{r}`" for r in trace.rules_evaluated]) if trace.rules_evaluated else "None")
