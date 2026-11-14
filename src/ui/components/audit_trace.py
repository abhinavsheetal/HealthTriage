"""Explainability & Audit Trail Component.

Visualizes:
- Fired production rules with full clinical guideline provenance.
- Step-by-step Certainty Factor calculations (min premise, propagation, combination).
- Rejection trace (rules considered and reasons rejected).
- Distinction between clinically validated guidelines and educational demo rules.
"""

import streamlit as st
from src.engine.explainer import AuditTrail


def render_audit_trace(audit_trail: AuditTrail) -> None:
    """Render full explainable AI trace panel."""
    st.markdown("### 🔍 Explainable AI (XAI) & Clinical Audit Trail")

    # 1. Narrative Clinical Summary
    st.markdown("#### 📝 Clinical Narrative Summary")
    st.markdown(
        f"""
        <div style="background-color: #F8FAFC; border-left: 4px solid #3B82F6; padding: 1rem; border-radius: 6px; font-size: 0.95rem;">
            {audit_trail.generate_narrative_explanation().replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 2. Production Rules Fired & Provenance
    st.markdown(f"#### 📜 Fired Production Rules ({len(audit_trail.fired_rules)} rule(s))")

    if not audit_trail.fired_rules and not audit_trail.emergency_override_triggered:
        st.info("No specific urgent or emergency production rules fired. Baseline primary care applies.")

    if audit_trail.emergency_override_triggered and audit_trail.emergency_override_trace:
        ov = audit_trail.emergency_override_trace
        st.markdown(
            f"""
            <div class="rule-card" style="border-left: 5px solid #DC2626;">
                <div class="rule-card-title">🚨 {ov['rule_name']} (Rule ID: {ov['rule_id']})</div>
                <div style="font-size: 0.85rem; color: #475569; margin-bottom: 0.4rem;">
                    <strong>Type:</strong> Emergency Safety Override (Priority {ov['priority']}) | 
                    <strong>Certainty Factor:</strong> Absolute CF = 1.0 (Unweakened)
                </div>
                <div style="font-size: 0.9rem; margin-bottom: 0.4rem;">
                    <strong>Matched Danger Signs:</strong> {', '.join(ov.get('matched_conditions', []))}
                </div>
                <div style="font-size: 0.9rem; color: #1E293B; margin-bottom: 0.4rem;">
                    <strong>Action:</strong> {ov['clinical_action']}
                </div>
                <div class="rule-citation">
                    📚 <strong>Provenance:</strong> {ov['organization']} | {ov['guideline']} ({ov['section_number']})
                    {f" | <a href='{ov['source_url']}' target='_blank'>Official Source</a>" if ov['source_url'] else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for firing in audit_trail.fired_rules:
        # Badge for validation status
        is_clinical = firing.validation_status == "clinically_validated"
        badge_color = "#059669" if is_clinical else "#D97706"
        badge_text = "CLINICALLY VALIDATED" if is_clinical else "EDUCATIONAL DEMONSTRATION"

        prov = firing.provenance or {}
        prov_text = f"{prov.get('organization', 'Clinical Body')} | {prov.get('title', firing.source_id)} ({firing.section_number})"
        url_link = f" | <a href='{prov.get('url', '')}' target='_blank'>Guideline URL</a>" if prov.get("url") else ""

        with st.expander(f"🔹 {firing.rule_name} (Priority {firing.priority})", expanded=True):
            st.markdown(
                f"""
                <span style="background-color: {badge_color}; color: white; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">
                    {badge_text}
                </span>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f"**Clinical Category:** `{firing.category}` | **Rule ID:** `{firing.rule_id}`")
            st.markdown(f"**Clinical Rationale:** {firing.clinical_rationale}")
            st.markdown(f"**Recommended Action:** {firing.clinical_action}")

            # Antecedents table
            st.markdown("##### Matched Conditions (AND Conjunction)")
            ant_data = [
                {
                    "Clinical Observation": t.fact_name,
                    "Condition Evaluated": t.condition_detail,
                    "Observation CF": f"{t.observation_cf:.2f}",
                    "Satisfied": "✅ TRUE" if t.satisfied else "❌ FALSE",
                }
                for t in firing.antecedent_traces
            ]
            st.table(ant_data)

            # Certainty Factor Math Trace
            st.markdown("##### 📐 Certainty Factor Calculus")
            math_md = (
                f"- **Premise Conjunction:** $CF(\\text{{Premise}}) = \\min({', '.join([f'{t.observation_cf:.2f}' for t in firing.antecedent_traces])}) = {firing.premise_cf:.2f}$\n"
                f"- **Rule Attendant Certainty:** $CF(\\text{{Rule}}) = {firing.rule_cf:.2f}$\n"
                f"- **Propagated Certainty:** $CF(\\text{{Conclusion}}) = {firing.premise_cf:.2f} \\times {firing.rule_cf:.2f} = {firing.propagated_cf:.2f}$\n"
            )
            if firing.prior_hypothesis_cf is not None:
                math_md += (
                    f"- **Evidence Combination with Prior:** $CF_{{\\text{{prior}}}} = {firing.prior_hypothesis_cf:.2f} \\oplus {firing.propagated_cf:.2f} = {firing.combined_hypothesis_cf:.2f}$\n"
                )
            st.markdown(math_md)

            st.markdown(
                f"""
                <div class="rule-citation">
                    📚 <strong>Clinical Source:</strong> {prov_text} {url_link}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 3. Iteration Cycle Log
    st.markdown("---")
    st.markdown("#### 🔄 Forward Chaining Execution Cycle Trace")
    with st.expander("View Full Inference Engine Cycle Trace (Fixed-Point Matching)", expanded=False):
        for it in audit_trail.forward_iterations:
            st.markdown(f"**Iteration Cycle #{it.iteration_number}**")
            st.write(f"- Rules Evaluated: {len(it.considered_rules)}")
            st.write(f"- Rules Fired in Cycle: {len(it.firings)}")
            st.write(f"- Rules Rejected in Cycle: {len(it.rejections)}")
            if it.new_facts_asserted:
                st.write(f"- New Facts Concluded: {', '.join(it.new_facts_asserted)}")
            if it.rejections:
                sample_rejections = it.rejections[:5]
                st.caption(
                    "Sample Rejections: " + "; ".join([f"{r.rule_id} ({r.reason})" for r in sample_rejections])
                )
            st.markdown("---")
