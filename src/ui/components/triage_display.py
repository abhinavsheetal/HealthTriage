"""User-Friendly Clinical Triage Presentation Component.

Presents assessment results in clear, patient-centric language:
- Clean urgency badges and explanation of what the result means.
- Clear, actionable next steps.
- Clear explanation of symptoms that influenced the result (without technical jargon).
- Important red-flag warnings on when to seek immediate emergency help.
"""

import streamlit as st
from src.config import TriageUrgency
from src.triage_coordinator import TriageResult


def render_triage_display(result: TriageResult) -> None:
    """Render the patient-friendly triage outcome and guidance."""
    urgency = result.overall_urgency

    # Configuration for patient-friendly presentations
    configs = {
        TriageUrgency.EMERGENCY: {
            "card_class": "result-emergency",
            "badge_class": "badge-emergency",
            "badge_text": "Immediate Emergency Action",
            "title": "Immediate Emergency Care Required",
            "icon": "🚨",
            "timeframe": "Seek Emergency Services (Call 112 or 108 / Go to Hospital Casualty immediately)",
            "meaning": (
                "Your reported symptoms or measurements indicate potential danger signs that require "
                "immediate evaluation and treatment by emergency medical personnel."
            ),
            "next_steps": (
                "Call 112 (National Emergency) or 108 (Ambulance) right away, or have someone take "
                "you to the nearest hospital Emergency / Casualty department. **Do not drive yourself.** Keep calm and rest while waiting for help."
            ),
        },
        TriageUrgency.VERY_URGENT: {
            "card_class": "result-very-urgent",
            "badge_class": "badge-very-urgent",
            "badge_text": "Very Urgent Evaluation",
            "title": "Urgent Medical Attention Needed Soon",
            "icon": "⏱️",
            "timeframe": "Seek Medical Evaluation Within 1 Hour",
            "meaning": (
                "Your symptoms indicate acute discomfort or physiological distress that should be assessed "
                "promptly by a healthcare professional."
            ),
            "next_steps": (
                "Contact an Urgent Care Centre or Emergency Department promptly. "
                "If symptoms rapidly worsen, call emergency services immediately."
            ),
        },
        TriageUrgency.URGENT: {
            "card_class": "result-urgent",
            "badge_class": "badge-urgent",
            "badge_text": "Same-Day Assessment",
            "title": "Same-Day Medical Assessment Recommended",
            "icon": "⚠️",
            "timeframe": "Contact a Doctor or Urgent Care Today (Within 2 to 12 Hours)",
            "meaning": (
                "Your symptoms warrant professional medical evaluation today to ensure proper treatment "
                "and prevent symptoms from becoming more severe."
            ),
            "next_steps": (
                "Contact your doctor or clinic for a same-day appointment, visit a local urgent care centre, "
                "or call the state health helpline (104) / eSanjeevani."
            ),
        },
        TriageUrgency.STANDARD: {
            "card_class": "result-standard",
            "badge_class": "badge-standard",
            "badge_text": "Routine Appointment",
            "title": "Routine Primary Care Consultation",
            "icon": "🩺",
            "timeframe": "Schedule an Appointment Within 1 to 3 Days",
            "meaning": (
                "Your reported symptoms do not appear to show immediate danger signs, but they should be "
                "reviewed by your regular healthcare provider during normal clinic hours."
            ),
            "next_steps": (
                "Contact your regular doctor (General Physician) or primary health clinic to schedule a routine consultation. "
                "If your symptoms change or get noticeably worse, seek medical care sooner."
            ),
        },
        TriageUrgency.SELF_CARE: {
            "card_class": "result-self-care",
            "badge_class": "badge-self-care",
            "badge_text": "Self-Care & Monitoring",
            "title": "Self-Care & Home Symptom Monitoring",
            "icon": "🌱",
            "timeframe": "Home Rest with Safety-Netting Advice",
            "meaning": (
                "Your symptoms appear mild and typical of common, self-limiting health conditions "
                "that can usually be managed safely at home."
            ),
            "next_steps": (
                "Rest, drink plenty of fluids, and use over-the-counter remedies if appropriate. "
                "Monitor your condition over the next few days. If symptoms do not improve after 3 to 5 days, consult your doctor."
            ),
        },
    }

    cfg = configs.get(urgency, configs[TriageUrgency.STANDARD])

    # Out-of-Scope Pediatric Notice
    if result.is_out_of_scope:
        st.error(
            "⚠️ **Demographic Scope Notice:** The patient age entered is under 18. "
            "HealthTriage is calibrated strictly for adults. Pediatric vital signs and danger signs differ significantly. "
            "Please consult a pediatrician or call emergency medical services directly."
        )

    # Main Visual Urgency Card
    st.markdown(
        f"""
        <div class="result-card {cfg['card_class']}">
            <span class="result-badge {cfg['badge_class']}">{cfg['badge_text']}</span>
            <div class="result-title">{cfg['icon']} {cfg['title']}</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: #334155; margin-bottom: 0.85rem;">
                Recommended Timeframe: {cfg['timeframe']}
            </div>
            <div class="result-summary">{cfg['meaning']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Actionable Guidance Cards
    col_act, col_why = st.columns(2)

    with col_act:
        st.markdown(
            f"""
            <div class="action-card">
                <h4>🎯 What You Should Do Next</h4>
                <p>{cfg['next_steps']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_why:
        # User-friendly explanation of findings
        friendly_rationale = result.primary_rationale
        st.markdown(
            f"""
            <div class="action-card">
                <h4>🩺 Understanding This Assessment</h4>
                <p>{friendly_rationale}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Key Influencing Factors (Friendly list)
    if result.fired_rules or result.is_emergency_override:
        st.markdown("#### 🔍 Symptoms and Signs Influencing This Guidance")
        factors = []

        if result.is_emergency_override:
            factors.append("Critical warning sign detected requiring immediate priority assessment.")

        for rule in result.fired_rules:
            # Display the clinical rationale in clear prose
            if rule.consequent and rule.consequent.clinical_rationale:
                factors.append(rule.consequent.clinical_rationale)

        if factors:
            for factor in set(factors):
                st.markdown(f"- **{factor}**")

    # Important Warning Signs (Red Flags)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="emergency-callout">
            <strong>🚨 When to Seek Immediate Emergency Attention:</strong><br>
            Regardless of your assessment result, call <strong>112</strong>, <strong>108</strong> (Ambulance), or go to the nearest hospital Emergency / Casualty immediately if you or the person you are caring for develops:
            <ul style="margin: 0.4rem 0 0 1.2rem; padding: 0;">
                <li>Sudden severe chest pain, pressure, or heaviness spreading to the arm, neck, or jaw.</li>
                <li>Sudden, severe shortness of breath or inability to speak in full sentences.</li>
                <li>Sudden confusion, slurred speech, facial drooping, or weakness on one side of the body.</li>
                <li>Fainting, collapse, or loss of consciousness.</li>
                <li>Bluish or grayish lips, face, or fingertips.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
