"""Knowledge Base & Clinical Guidelines Catalog Viewer Component."""

import streamlit as st
from src.knowledge.loader import RuleKnowledgeBase


def render_knowledge_viewer(kb: RuleKnowledgeBase) -> None:
    """Render interactive rule database and clinical sources catalog."""
    st.markdown("### 📚 Clinical Knowledge Base & Guideline Catalog")
    st.markdown(
        "Inspect all documented production rules, certainty factors, and official medical guidelines."
    )

    tab1, tab2 = st.tabs(["📜 Production Rules Catalog", "🏛️ Clinical Guideline Sources"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            categories = ["All"] + sorted(list({r.category for r in kb.rules}))
            selected_cat = st.selectbox("Filter by Category", options=categories)
        with col2:
            status_opts = ["All", "clinically_validated", "educationally_demonstrated"]
            selected_status = st.selectbox("Filter by Validation Status", options=status_opts)

        filtered_rules = kb.rules
        if selected_cat != "All":
            filtered_rules = [r for r in filtered_rules if r.category == selected_cat]
        if selected_status != "All":
            filtered_rules = [r for r in filtered_rules if r.validation_status.value == selected_status]

        st.caption(f"Showing {len(filtered_rules)} of {len(kb.rules)} rules in knowledge base.")

        for rule in filtered_rules:
            is_clinical = rule.validation_status.value == "clinically_validated"
            badge_color = "#059669" if is_clinical else "#D97706"
            badge_label = "CLINICALLY VALIDATED" if is_clinical else "EDUCATIONAL DEMONSTRATION"

            prov = kb.sources.get(rule.source_id)

            with st.expander(f"🔹 [{rule.rule_id}] {rule.name} (Priority {rule.priority})"):
                st.markdown(
                    f"""
                    <span style="background-color: {badge_color}; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">
                        {badge_label}
                    </span>
                    <span style="background-color: #E2E8F0; color: #1E293B; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem;">
                        CF: {rule.rule_cf:.2f}
                    </span>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Description:** {rule.description}")
                st.markdown(f"**Action:** {rule.consequent.clinical_action}")
                st.markdown(f"**Medical Rationale:** {rule.consequent.clinical_rationale}")

                st.markdown("##### IF Antecedents (Conjunction):")
                for ant in rule.antecedents:
                    st.write(f"- `{ant.fact_name}` `{ant.operator.value}` `{ant.expected_value}`")

                st.markdown("##### THEN Consequent:")
                st.write(
                    f"- Assert `{rule.consequent.target_attribute}` = `{rule.consequent.target_value}` "
                    f"(Urgency: `{rule.consequent.urgency_level.value if rule.consequent.urgency_level else 'None'}`)"
                )

                if prov:
                    st.markdown(
                        f"""
                        <div class="rule-citation">
                            📚 <strong>Provenance:</strong> {prov.organization} | {prov.source_title} ({rule.section_number})<br>
                            🎯 <strong>Target Population:</strong> {prov.target_population}<br>
                            🔗 <a href='{prov.source_url}' target='_blank'>Access Official Guideline</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with tab2:
        st.markdown("#### Published Clinical Reference Catalog")
        for s_id, prov in kb.sources.items():
            st.markdown(
                f"""
                <div class="rule-card">
                    <div class="rule-card-title">🏛️ {prov.source_title}</div>
                    <div style="font-size: 0.88rem; color: #475569; margin: 0.3rem 0;">
                        <strong>Publishing Organization:</strong> {prov.organization}<br>
                        <strong>Guideline Identifier:</strong> <code>{prov.guideline_identifier}</code><br>
                        <strong>Publication / Update Date:</strong> {prov.publication_date}<br>
                        <strong>Target Demographic:</strong> {prov.target_population}<br>
                        <strong>Section Reference:</strong> {prov.section_number}
                    </div>
                    <div class="rule-citation">
                        🔗 <a href="{prov.source_url}" target="_blank">Official Document Link ({prov.source_url})</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
