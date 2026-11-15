"""Custom CSS design system for HealthTriage.

Strict Light Mode Enforcement:
- Enforces color-scheme: light at root and media query levels.
- Clean white (#FFFFFF) and light slate (#F8FAFC) backgrounds.
- Calm teal (#0D9488), slate blue (#2563EB), and soft emerald (#059669) accents.
- Professional typography (Inter font).
- Clear, accessible acuity cards and responsive layout.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Strict Light Mode Enforcement (prevents OS/browser dark mode inversion) */
:root {
    color-scheme: light !important;
}

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Hide Streamlit Header, Toolbar, Main Menu, and Profile/Manage Badges */
header[data-testid="stHeader"] {
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}

[data-testid="stToolbar"], #MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    visibility: hidden !important;
    display: none !important;
}

/* Hide Streamlit Cloud bottom/top management pills and avatar badges */
.viewerBadge_container__1QSob,
.viewerBadge_link__1S137,
[class*="viewerBadge"],
[data-testid="manage-app-button"],
#manage-app-button,
[class*="manageApp"] {
    display: none !important;
    visibility: hidden !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    background-color: #F8FAFC !important;
    border-right: 1px solid #E2E8F0 !important;
    color: #1E293B !important;
}

@media (prefers-color-scheme: dark) {
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
    }
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
        color: #1E293B !important;
    }
}

/* Remove default excess padding */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1050px;
}

/* Top App Brand Bar */
.brand-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.85rem 1.5rem;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.brand-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #0F766E;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.brand-badge {
    font-size: 0.75rem;
    font-weight: 600;
    color: #0D9488;
    background: #CCFBF1;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, #F0FDFA 0%, #F8FAFC 100%);
    border: 1px solid #CCFBF1;
    border-radius: 16px;
    padding: 2.75rem 2.25rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px -1px rgba(13, 148, 136, 0.05);
}

.hero-heading {
    font-size: 2.1rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.25;
    margin-bottom: 0.85rem;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #475569;
    line-height: 1.6;
    margin-bottom: 1.5rem;
    max-width: 720px;
}

/* Step Cards */
.step-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.5rem;
    height: 100%;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.step-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background-color: #E6FFFA;
    color: #0D9488;
    font-weight: 700;
    font-size: 0.95rem;
    border-radius: 8px;
    margin-bottom: 0.85rem;
}

.step-title {
    font-weight: 600;
    font-size: 1.05rem;
    color: #0F172A;
    margin-bottom: 0.4rem;
}

.step-description {
    font-size: 0.9rem;
    color: #64748B;
    line-height: 1.5;
}

/* Concise Healthcare Disclaimer */
.health-disclaimer {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #0D9488;
    padding: 0.9rem 1.25rem;
    border-radius: 8px;
    font-size: 0.85rem;
    color: #475569;
    line-height: 1.5;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}

/* Emergency Callout Box */
.emergency-callout {
    background-color: #FEF2F2;
    border: 1px solid #FECACA;
    border-left: 5px solid #EF4444;
    padding: 1rem 1.25rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    color: #991B1B;
    font-size: 0.9rem;
    line-height: 1.5;
}

/* Public Urgency Result Cards */
.result-card {
    padding: 2rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.result-emergency {
    background: #FEF2F2;
    border: 2px solid #EF4444;
}

.result-very-urgent {
    background: #FFF7ED;
    border: 2px solid #F97316;
}

.result-urgent {
    background: #FFFBEB;
    border: 2px solid #F59E0B;
}

.result-standard {
    background: #F0F9FF;
    border: 2px solid #38BDF8;
}

.result-self-care {
    background: #F0FDF4;
    border: 2px solid #22C55E;
}

.result-badge {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

.badge-emergency { background: #FEE2E2; color: #991B1B; }
.badge-very-urgent { background: #FFEDD5; color: #9A3412; }
.badge-urgent { background: #FEF3C7; color: #92400E; }
.badge-standard { background: #E0F2FE; color: #0369A1; }
.badge-self-care { background: #DCFCE7; color: #166534; }

.result-title {
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.result-summary {
    font-size: 1.05rem;
    line-height: 1.55;
    margin-bottom: 1.25rem;
}

/* Action Boxes inside results */
.action-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.action-card h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: #0F172A;
}

.action-card p {
    margin: 0;
    font-size: 0.92rem;
    color: #334155;
    line-height: 1.5;
}
</style>
"""
