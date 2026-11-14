"""Patient Symptom Assessment Form Component.

Redesigned for public healthcare usability:
- Simple, everyday language (e.g., "shortness of breath", "cold sweats").
- Clear 3-part layout: Basic Information, Symptoms & Severity, Optional Vitals & Signs.
- Unmeasured vital signs are optional and safely treated as UNKNOWN.
- Helpful guidance and tooltips throughout.
"""

from typing import Any, Dict, List, Optional, Tuple
import streamlit as st


def render_patient_form() -> Tuple[int, Dict[str, Any], Dict[str, float]]:
    """Render friendly patient assessment form.
    
    Returns:
        Tuple[age, observations_dict, observation_cfs_dict]
    """
    st.markdown("## Symptom Assessment")
    st.markdown(
        "Please provide details about what you are experiencing. "
        "Take your time and answer as accurately as possible."
    )

    v_age = 45
    v_obs = {}

    # ==========================================
    # SECTION 1: BASIC INFORMATION
    # ==========================================
    st.markdown("### 1. Basic Information")
    st.caption("Tell us a little about yourself.")

    col1, col2 = st.columns([1, 2])
    with col1:
        age = st.number_input(
            "Your Age (Years)",
            min_value=0,
            max_value=120,
            value=v_age,
            help="This service is calibrated for adults aged 18 and older.",
        )
        if age < 18:
            st.warning(
                "⚠️ **Age Notice:** HealthTriage is designed for adults aged 18 and over. "
                "For children and teenagers, please consult a pediatrician, call 112 / 108, or contact your local health helpline directly."
            )

    with col2:
        st.markdown("**Relevant Medical History**")
        st.caption("Check any conditions you have been diagnosed with:")
        hx_col1, hx_col2 = st.columns(2)
        with hx_col1:
            hx_heart = st.checkbox("Heart disease or previous heart attack")
            hx_bp = st.checkbox("High blood pressure (hypertension)")
        with hx_col2:
            hx_resp = st.checkbox("Asthma, COPD, or lung conditions")
            hx_diabetes = st.checkbox("Diabetes")

    st.markdown("---")

    # ==========================================
    # SECTION 2: YOUR SYMPTOMS
    # ==========================================
    st.markdown("### 2. Symptoms & How You Feel")
    st.caption("Select any symptoms you are currently experiencing:")

    sym_col1, sym_col2 = st.columns(2)

    with sym_col1:
        st.markdown("**Chest & Heart Symptoms**")
        chest_pain = st.checkbox(
            "Chest pain, pressure, tightness, or aching",
            value=bool(v_obs.get("acute_chest_pain", False)),
            help="Any heavy ache, tightness, crushing, or squeezing sensation in the chest.",
        )

        pain_duration = 0
        radiating = False
        diaphoresis = False
        exertional = False
        relieved_rest = False
        wall_pain = False

        if chest_pain:
            st.markdown(
                """<div style="background-color: #F8FAFC; border-left: 3px solid #0D9488; padding: 0.75rem 1rem; border-radius: 6px; margin: 0.5rem 0 1rem 0;">
                <p style="margin: 0 0 0.4rem 0; font-size: 0.88rem; font-weight: 600; color: #0F766E;">Chest Symptom Details:</p>
                """,
                unsafe_allow_html=True,
            )
            pain_duration = st.number_input(
                "How many minutes has the chest discomfort lasted?",
                min_value=0,
                max_value=300,
                value=int(v_obs.get("pain_duration_minutes", 0)),
                help="Persistent chest pain lasting 20 minutes or longer requires urgent medical evaluation.",
            )
            radiating = st.checkbox(
                "Pain spreads to your left arm, shoulder, neck, or jaw",
                value=bool(v_obs.get("radiation_arm_neck_jaw", False)),
            )
            diaphoresis = st.checkbox(
                "Cold sweats, nausea, or unusually heavy sweating",
                value=bool(v_obs.get("diaphoresis", False)),
            )
            exertional = st.checkbox(
                "Discomfort starts during physical exertion and eases when resting",
                value=bool(v_obs.get("exertional_chest_discomfort", False)),
            )
            relieved_rest = st.checkbox(
                "Discomfort completely resolves within a few minutes of resting",
                value=bool(v_obs.get("relieved_by_rest", False)),
            )
            wall_pain = st.checkbox(
                "Discomfort is a sharp ache that hurts more when pressing directly on the chest wall",
                value=bool(v_obs.get("chest_wall_tenderness_reproduced", False)),
            )
            st.markdown("</div>", unsafe_allow_html=True)

    with sym_col2:
        st.markdown("**Breathing & Respiratory Symptoms**")
        dyspnea = st.checkbox(
            "Shortness of breath or difficulty breathing",
            value=bool(v_obs.get("dyspnea", False)),
            help="Feeling breathless while resting or during mild movement.",
        )
        stridor = st.checkbox(
            "High-pitched whistling or harsh sound when breathing in (at rest)",
            value=bool(v_obs.get("stridor_at_rest", False)),
            help="This can indicate upper airway narrowing and is an important warning sign.",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Fever & General Health**")
        fever = st.checkbox(
            "Fever, shivering, or feeling unusually hot and cold",
            value=bool(v_obs.get("suspected_infection_or_fever", False)),
        )
        poor_perfusion = st.checkbox(
            "Cold, clammy hands or feet with unusually pale skin",
            value=bool(v_obs.get("poor_peripheral_perfusion", False)),
        )
        unresponsive_feel = st.checkbox(
            "Severe confusion, drowsiness, or difficulty staying awake",
            value=bool(v_obs.get("avpu_scale") == "U"),
        )

    st.markdown("<br>", unsafe_allow_html=True)
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        duration_cat = st.selectbox(
            "How long have you had these symptoms?",
            options=[
                "Less than an hour",
                "1 to 6 hours",
                "6 to 24 hours",
                "1 to 3 days",
                "More than 3 days",
            ],
            index=0,
        )
    with d_col2:
        severity_cat = st.select_slider(
            "Overall symptom severity:",
            options=["Mild", "Moderate", "Severe", "Very Severe / Unbearable"],
            value="Moderate",
            help="Select how much the symptoms are currently affecting your ability to carry out normal activities.",
        )

    st.markdown("---")

    # ==========================================
    # SECTION 3: ADDITIONAL INFORMATION (OPTIONAL)
    # ==========================================
    st.markdown("### 3. Additional Information (Optional)")
    st.caption("If you have home monitoring devices, you may enter your readings. Leave blank if not measured.")

    with st.expander("🩺 Add Vital Signs (Optional — Only if Measured)", expanded=bool(v_obs)):
        st.info("💡 You do not need to enter vital signs to complete the assessment. Missing measurements are safely handled.")
        vit_col1, vit_col2, vit_col3 = st.columns(3)

        with vit_col1:
            has_bp = st.checkbox("I measured Blood Pressure", value=("systolic_bp" in v_obs))
            sbp = None
            if has_bp:
                sbp = st.number_input(
                    "Systolic BP (top number, mmHg)",
                    min_value=40,
                    max_value=250,
                    value=int(v_obs.get("systolic_bp", 120)),
                )

            has_hr = st.checkbox("I measured Heart Rate", value=("heart_rate" in v_obs))
            hr = None
            if has_hr:
                hr = st.number_input(
                    "Heart Rate (beats per minute)",
                    min_value=25,
                    max_value=220,
                    value=int(v_obs.get("heart_rate", 75)),
                )

        with vit_col2:
            has_rr = st.checkbox("I counted Breaths per Minute", value=("respiratory_rate" in v_obs))
            rr = None
            if has_rr:
                rr = st.number_input(
                    "Respiratory Rate (breaths/min)",
                    min_value=4,
                    max_value=60,
                    value=int(v_obs.get("respiratory_rate", 16)),
                )

            has_spo2 = st.checkbox("I measured Oxygen Saturation (SpO2)", value=("oxygen_saturation" in v_obs))
            spo2 = None
            if has_spo2:
                spo2 = st.number_input(
                    "Oxygen Saturation SpO2 (%)",
                    min_value=50,
                    max_value=100,
                    value=int(v_obs.get("oxygen_saturation", 98)),
                )

        with vit_col3:
            has_temp = st.checkbox("I measured Temperature", value=("temperature_celsius" in v_obs))
            temp = None
            if has_temp:
                temp = st.number_input(
                    "Body Temperature (°C)",
                    min_value=32.0,
                    max_value=43.0,
                    value=float(v_obs.get("temperature_celsius", 37.0)),
                    step=0.1,
                    format="%.1f",
                )

    # Compile observations dictionary (omitting None for unmeasured vitals)
    observations: Dict[str, Any] = {
        "stridor_at_rest": stridor,
        "poor_peripheral_perfusion": poor_perfusion,
        "dyspnea": dyspnea,
        "suspected_infection_or_fever": fever,
        "acute_chest_pain": chest_pain,
        "pain_duration_minutes": pain_duration if chest_pain else 0,
        "radiation_arm_neck_jaw": radiating if chest_pain else False,
        "diaphoresis": diaphoresis if chest_pain else False,
        "exertional_chest_discomfort": exertional if chest_pain else False,
        "relieved_by_rest": relieved_rest if chest_pain else False,
        "acute_rest_pain": chest_pain,
        "chest_wall_tenderness_reproduced": wall_pain if chest_pain else False,
    }

    if unresponsive_feel:
        observations["avpu_scale"] = "U"

    # Add measured vitals if provided
    if sbp is not None:
        observations["systolic_bp"] = sbp
    if hr is not None:
        observations["heart_rate"] = hr
    if rr is not None:
        observations["respiratory_rate"] = rr
    if spo2 is not None:
        observations["oxygen_saturation"] = spo2
    if temp is not None:
        observations["temperature_celsius"] = temp

    # Build CF dictionary
    observation_cfs: Dict[str, float] = {k: 1.0 for k in observations}

    return age, observations, observation_cfs
