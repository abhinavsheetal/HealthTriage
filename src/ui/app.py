"""HealthTriage - Preliminary Clinical Urgency & Triage Guidance System.

A professional, public-facing healthcare decision assistance website.
Grounds recommendations in published clinical practice guidelines (WHO, NICE).
"""

from pathlib import Path
import streamlit as st

from src.triage_coordinator import TriageCoordinator
from src.ui.components.patient_form import render_patient_form
from src.ui.components.triage_display import render_triage_display
from src.ui.styles import CUSTOM_CSS

# Concise public medical disclaimer
PUBLIC_DISCLAIMER = (
    "This tool provides preliminary health guidance based on predefined rules. "
    "It does not diagnose medical conditions or replace professional medical advice. "
    "Always consult a qualified healthcare professional. "
    "If you experience a medical emergency, seek immediate help."
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SOURCES_PATH = BASE_DIR / "data" / "clinical_sources.json"
RULES_DIR = BASE_DIR / "data" / "rules"


@st.cache_resource
def get_coordinator() -> TriageCoordinator:
    """Load and cache the TriageCoordinator."""
    return TriageCoordinator.from_paths(SOURCES_PATH, RULES_DIR)


def main():
    st.set_page_config(
        page_title="HealthTriage - Symptom Guidance",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject Light Theme CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    coordinator = get_coordinator()

    # Session State Initialization
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Home"

    # ==========================================
    # CLEAN PUBLIC SIDEBAR
    # ==========================================
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.25rem;">
                <span style="font-size: 1.7rem;">🩺</span>
                <span style="font-size: 1.4rem; font-weight: 700; color: #0F766E;">HealthTriage</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Simple Public Navigation
        nav_options = ["Home", "Symptom Assessment", "How It Works", "About"]

        current_idx = nav_options.index(st.session_state["current_page"]) if st.session_state["current_page"] in nav_options else 0
        selected_nav = st.radio(
            "Navigate",
            options=nav_options,
            index=current_idx,
            label_visibility="collapsed",
        )
        st.session_state["current_page"] = selected_nav

        st.markdown("---")
        st.markdown(
            """
            <div style="background-color: #FEF2F2; border-left: 3px solid #EF4444; padding: 0.75rem 0.85rem; border-radius: 6px; font-size: 0.82rem; color: #991B1B;">
                <strong>🚨 Emergency Notice:</strong><br>
                If you are experiencing severe chest pain, sudden breathlessness, or collapse, call <strong>112</strong> (National Emergency) or <strong>108</strong> (Ambulance) immediately.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Top Brand Header
    st.markdown(
        """
        <div class="brand-nav">
            <div class="brand-title">
                🩺 HealthTriage
                <span class="brand-badge">Preliminary Guidance</span>
            </div>
            <div style="font-size: 0.85rem; color: #64748B;">
                Evidence-Based Triage Support
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.session_state["current_page"]

    # ==========================================
    # 1. HOME PAGE
    # ==========================================
    if page == "Home":
        st.markdown(
            """
            <div class="hero-section">
                <div class="hero-heading">Understand your symptoms.<br>Know when to seek care.</div>
                <div class="hero-subtitle">
                    HealthTriage helps you assess the urgency of your symptoms and understand whether you should seek emergency medical attention, visit an urgent care clinic, or arrange a routine doctor's consultation.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1, 1])
        with col_btn1:
            if st.button("🚀 Start Symptom Assessment", type="primary", use_container_width=True):
                st.session_state["current_page"] = "Symptom Assessment"
                st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### How It Works in 3 Simple Steps")

        step_col1, step_col2, step_col3 = st.columns(3)
        with step_col1:
            st.markdown(
                """
                <div class="step-card">
                    <div class="step-number">1</div>
                    <div class="step-title">Tell Us What You Feel</div>
                    <div class="step-description">
                        Select your current symptoms using simple, straightforward checkboxes without confusing jargon.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with step_col2:
            st.markdown(
                """
                <div class="step-card">
                    <div class="step-number">2</div>
                    <div class="step-title">Answer Key Questions</div>
                    <div class="step-description">
                        Share how long your symptoms have lasted, their severity, and any optional vital readings you have.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with step_col3:
            st.markdown(
                """
                <div class="step-card">
                    <div class="step-number">3</div>
                    <div class="step-title">Receive Clear Guidance</div>
                    <div class="step-description">
                        Get an instant recommendation on the appropriate level of care, recommended timeframes, and key warning signs.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div class="health-disclaimer">
                <strong>Medical Notice:</strong> {PUBLIC_DISCLAIMER}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ==========================================
    # 2. SYMPTOM ASSESSMENT PAGE
    # ==========================================
    elif page == "Symptom Assessment":
        age, observations, observation_cfs = render_patient_form()

        st.markdown("<br>", unsafe_allow_html=True)
        submit_clicked = st.button(
            "📋 Check My Symptoms Now",
            type="primary",
            use_container_width=True,
        )

        if submit_clicked:
            with st.spinner("Analyzing your reported symptoms against clinical guidelines..."):
                result = coordinator.evaluate_patient(
                    age=age,
                    observations=observations,
                    observation_cfs=observation_cfs,
                )
                st.session_state["assessment_result"] = result
                st.session_state["assessment_obs"] = observations
                st.session_state["assessment_cfs"] = observation_cfs

        if "assessment_result" in st.session_state:
            res = st.session_state["assessment_result"]
            st.markdown("---")
            st.markdown("### Your Assessment Outcome")
            render_triage_display(res)

            btn_col1, btn_col2 = st.columns([1, 2])
            with btn_col1:
                if st.button("🔄 Start a New Assessment"):
                    del st.session_state["assessment_result"]
                    st.rerun()

        st.markdown(
            f"""
            <div class="health-disclaimer">
                <strong>Medical Notice:</strong> {PUBLIC_DISCLAIMER}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ==========================================
    # 3. HOW IT WORKS PAGE
    # ==========================================
    elif page == "How It Works":
        st.markdown("## How HealthTriage Works")
        st.markdown(
            "HealthTriage is built on proven clinical triage methodologies designed to help individuals "
            "navigate healthcare systems safely and appropriately."
        )

        st.markdown("---")
        h_col1, h_col2 = st.columns(2)

        with h_col1:
            st.markdown("### 🏛️ Evidence-Based Guidelines")
            st.write(
                "Our reasoning engine applies documented clinical rules published by world-leading health organizations, "
                "including the **World Health Organization (WHO)** and the **National Institute for Health and Care Excellence (NICE)**."
            )
            st.write(
                "Every clinical rule corresponds to established medical protocols for identifying red-flag danger signs, "
                "respiratory compromise, and acute cardiovascular risk."
            )

            st.markdown("### ⏱️ Urgency Classification, Not Diagnosis")
            st.write(
                "Definitive disease diagnosis requires physical examinations, blood tests, and specialized imaging. "
                "Instead of guessing diagnoses, HealthTriage focuses on what matters most when you feel unwell: "
                "**how urgently you should seek professional medical care**."
            )

        with h_col2:
            st.markdown("### 🛡️ Safe Handling of Incomplete Information")
            st.write(
                "If you do not know a vital sign (like your blood pressure or oxygen saturation), our system never assumes it is normal. "
                "It safely classifies missing information as unrecorded rather than negative, ensuring your assessment remains cautious."
            )

            st.markdown("### 🚨 Emergency Overrides")
            st.write(
                "Certain critical warning signs—such as severe upper airway noise, oxygen levels below 90%, or unresponsiveness—"
                "immediately trigger an emergency priority directive, ensuring life-threatening symptoms are never delayed."
            )

        st.markdown(
            f"""
            <div class="health-disclaimer">
                <strong>Medical Notice:</strong> {PUBLIC_DISCLAIMER}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ==========================================
    # 4. ABOUT PAGE
    # ==========================================
    elif page == "About":
        st.markdown("## About HealthTriage")
        st.markdown(
            "HealthTriage was developed to provide clear, reliable, and accessible preliminary health guidance "
            "to help individuals understand when their symptoms require urgent attention."
        )

        st.markdown("---")
        ab_col1, ab_col2 = st.columns(2)

        with ab_col1:
            st.markdown("### Our Mission")
            st.write(
                "When health concerns arise, knowing whether to call an ambulance, visit urgent care, or wait for a regular doctor's appointment "
                "can be stressful. HealthTriage aims to reduce uncertainty by translating complex clinical guidelines into straightforward, "
                "actionable guidance."
            )

            st.markdown("### Privacy & Confidentiality")
            st.write(
                "Your privacy is paramount. HealthTriage processes your assessment live during your session. "
                "No identifying personal records, medical histories, or contact details are stored or transmitted to external servers."
            )

        with ab_col2:
            st.markdown("### Important Healthcare Contacts (India)")
            st.write("**Emergency Services:**")
            st.write("- 🇮🇳 National Emergency Helpline: Call **112** (All-in-One: Ambulance, Police, Fire)")
            st.write("- 🚑 Emergency Medical & Ambulance: Call **108** (24x7 Toll-Free)")
            st.write("- 🏥 Patient Transport & Maternity: Call **102**")

            st.write("**Non-Emergency Health Advice & Teleconsultation:**")
            st.write("- 📞 State Health Helpline: Dial **104** (Medical guidance & symptom inquiry)")
            st.write("- 💻 eSanjeevani: National Teleconsultation Service ([esanjeevani.mohfw.gov.in](https://esanjeevani.mohfw.gov.in))")
            st.write("- Consult your local General Physician or nearest Primary Health Centre (PHC) / Community Health Centre (CHC).")

        st.markdown(
            f"""
            <div class="health-disclaimer">
                <strong>Medical Notice:</strong> {PUBLIC_DISCLAIMER}
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
