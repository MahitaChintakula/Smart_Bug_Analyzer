import streamlit as st
import requests
from textwrap import dedent


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Smart Bug Analyzer",
    page_icon="🐞",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HTML RENDER HELPER
# ============================================================


def render_html(content):
    """
    Safely render custom HTML in Streamlit.

    Removes all unwanted indentation so Streamlit
    does not interpret the HTML as a code block.
    """

    content = dedent(content).strip()

    # Remove leading whitespace from every line.
    lines = content.splitlines()
    content = "\n".join(line.lstrip() for line in lines)

    st.markdown(content, unsafe_allow_html=True)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background: #0f1117;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* ============================================================
   HEADER
   ============================================================ */

.main-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 5px;
}

.subtitle {
    color: #9ca3af;
    font-size: 17px;
    margin-bottom: 25px;
}

/* ============================================================
   CARDS
   ============================================================ */

.card {
    background: #171a21;
    border: 1px solid #292e39;
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 18px;
}

.card-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 12px;
    color: #ffffff;
}

.card-text {
    color: #d1d5db;
    line-height: 1.6;
}

/* ============================================================
   METRIC CARDS
   ============================================================ */

.metric-card {
    background: #171a21;
    border: 1px solid #292e39;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
    min-height: 120px;
}

.metric-label {
    color: #9ca3af;
    font-size: 14px;
}

.metric-value {
    font-size: 28px;
    font-weight: 800;
    margin-top: 8px;
}

/* ============================================================
   SEVERITY
   ============================================================ */

.critical {
    color: #ff4b4b;
}

.high {
    color: #ff9f43;
}

.medium {
    color: #ffd166;
}

.low {
    color: #4ade80;
}

/* ============================================================
   SIMILARITY
   ============================================================ */

.similarity-container {
    margin: 16px 0 22px 0;
}

.similarity-label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 7px;
    color: #d1d5db;
    font-size: 15px;
}

.similarity-bar {
    height: 10px;
    background: #292e39;
    border-radius: 10px;
    overflow: hidden;
}

.similarity-fill {
    height: 100%;
    background: #6366f1;
    border-radius: 10px;
}

/* ============================================================
   AGENTS
   ============================================================ */

.agent {
    background: #171a21;
    border: 1px solid #292e39;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 8px;
}

.agent-name {
    font-weight: 600;
}

.agent-status {
    float: right;
    color: #4ade80;
    font-size: 13px;
}

/* ============================================================
   FIX BOX
   ============================================================ */

.fix-box {
    background: #151d18;
    border: 1px solid #275c39;
    border-radius: 14px;
    padding: 20px;
    line-height: 1.6;
    margin-bottom: 18px;
}

/* ============================================================
   PREVENTION
   ============================================================ */

.prevention-box {
    background: #171b24;
    border-left: 4px solid #6366f1;
    border-radius: 8px;
    padding: 16px;
    margin-top: 10px;
    margin-bottom: 20px;
}

/* ============================================================
   INPUT
   ============================================================ */

textarea {
    border-radius: 12px !important;
}

/* ============================================================
   BUTTON
   ============================================================ */

.stButton > button {
    border-radius: 10px;
    font-weight: 700;
    min-height: 48px;
}

/* ============================================================
   SECTION SPACING
   ============================================================ */

.section-space {
    height: 10px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# API
# ============================================================

API_URL = "http://127.0.0.1:8000/analyze"


# ============================================================
# HEADER
# ============================================================

render_html(
    """
    <div class="main-title">🐞 Smart Bug Analyzer</div>
    <div class="subtitle">
        AI-powered defect intelligence using historical bug knowledge
    </div>
    """
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🧠 Analyzer")

    render_html(
        """
        <div class="agent">
        <span class="agent-name">📋 Log Analysis</span>
        <span class="agent-status">● Ready</span>
        </div>

        <div class="agent">
        <span class="agent-name">🔎 Duplicate Detection</span>
        <span class="agent-status">● Ready</span>
        </div>

        <div class="agent">
        <span class="agent-name">🧠 Root Cause</span>
        <span class="agent-status">● Ready</span>
        </div>

        <div class="agent">
        <span class="agent-name">🚦 Triage</span>
        <span class="agent-status">● Ready</span>
        </div>

        <div class="agent">
        <span class="agent-name">🛠️ Remediation</span>
        <span class="agent-status">● Ready</span>
        </div>
        """
    )

    st.divider()

    st.caption("Smart Bug Analyzer v1.0")


# ============================================================
# INPUT SECTION
# ============================================================

render_html(
    """
    <div class="card-title">📝 Submit Bug Report</div>
    """
)

bug_report = st.text_area(
    "Bug Report / Error Log / Stack Trace",
    height=230,
    label_visibility="collapsed",
    placeholder="""Paste your bug report, error log, or stack trace here...

Example:

java.lang.NullPointerException
at LoginService.java:45

Login crashes because the user object is null.""",
)


analyze_button = st.button("🔍 Analyze Bug", type="primary", use_container_width=True)


# ============================================================
# ANALYSIS
# ============================================================

if analyze_button:

    if not bug_report.strip():

        st.warning("Please enter a bug report or stack trace.")

    else:

        with st.spinner("Running multi-agent analysis..."):

            try:

                response = requests.post(
                    API_URL, json={"bug_report": bug_report}, timeout=120
                )

                if response.status_code != 200:

                    st.error(f"Backend returned HTTP {response.status_code}")

                    st.stop()

                result = response.json()

            except requests.exceptions.ConnectionError:

                st.error(
                    "Cannot connect to FastAPI. " "Make sure the backend is running."
                )

                st.stop()

            except requests.exceptions.Timeout:

                st.error("The analysis took too long. " "Please try again.")

                st.stop()

            except Exception as e:

                st.error(f"Unexpected error: {e}")

                st.stop()

        st.success("Analysis completed successfully!")

        # ====================================================
        # EXTRACT RESPONSE DATA
        # ====================================================

        triage = result.get("triage", {})

        root_cause = result.get("root_cause", {})

        similar_bugs = result.get("similar_bugs", [])

        log_info = result.get("log_info", {})

        remediation = result.get("remediation", {})

        severity = triage.get("severity", "Unknown")

        priority = triage.get("priority", "Unknown")

        confidence = root_cause.get("confidence", 0)

        # ====================================================
        # CONFIDENCE
        # ====================================================

        try:

            confidence = float(confidence)

            if confidence <= 1:
                confidence_percent = int(confidence * 100)
            else:
                confidence_percent = int(confidence)

        except:

            confidence_percent = 0

        # ====================================================
        # TOP MATCH
        # ====================================================

        match_score = 0

        if similar_bugs:

            try:

                match_score = float(similar_bugs[0].get("similarity_score", 0))

                if match_score <= 1:

                    match_score = int(match_score * 100)

                else:

                    match_score = int(match_score)

            except:

                match_score = 0

        # ====================================================
        # BUG OVERVIEW
        # ====================================================

        st.markdown("## 📊 Bug Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            severity_class = str(severity).lower().replace(" ", "-")

            render_html(
                f"""
                <div class="metric-card">
                <div class="metric-label">
                SEVERITY
                </div>

                <div class="metric-value {severity_class}">
                {severity}
                </div>
                </div>
                """
            )

        with col2:

            render_html(
                f"""
                <div class="metric-card">
                <div class="metric-label">
                PRIORITY
                </div>

                <div class="metric-value">
                {priority}
                </div>
                </div>
                """
            )

        with col3:

            render_html(
                f"""
                <div class="metric-card">
                <div class="metric-label">
                ROOT CAUSE CONFIDENCE
                </div>

                <div class="metric-value">
                {confidence_percent}%
                </div>
                </div>
                """
            )

        with col4:

            render_html(
                f"""
                <div class="metric-card">
                <div class="metric-label">
                TOP HISTORICAL MATCH
                </div>

                <div class="metric-value">
                {match_score}%
                </div>
                </div>
                """
            )

        # ====================================================
        # LOG ANALYSIS
        # ====================================================

        st.markdown("## 📋 Log Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:

            render_html(
                f"""
                <div class="card">

                <div class="card-title">
                ⚠️ Exception
                </div>

                <div class="card-text">
                {log_info.get(
                    "exception",
                    "Not detected"
                )}
                </div>

                </div>
                """
            )

        with col2:

            render_html(
                f"""
                <div class="card">

                <div class="card-title">
                📄 File
                </div>

                <div class="card-text">
                {log_info.get(
                    "file",
                    "Not detected"
                )}
                </div>

                </div>
                """
            )

        with col3:

            render_html(
                f"""
                <div class="card">

                <div class="card-title">
                📍 Line
                </div>

                <div class="card-text">
                {log_info.get(
                    "line",
                    "Not detected"
                )}
                </div>

                </div>
                """
            )

        # ====================================================
        # ROOT CAUSE
        # ====================================================

        st.markdown("## 🧠 Root Cause Analysis")

        render_html(
            f"""
            <div class="card">

            <div class="card-title">
            Probable Root Cause
            </div>

            <div class="card-text">
            {root_cause.get(
                "root_cause",
                "Unable to determine root cause."
            )}
            </div>

            <br>

            <div class="card-title">
            Explanation
            </div>

            <div class="card-text">
            {root_cause.get(
                "explanation",
                "No explanation available."
            )}
            </div>

            </div>
            """
        )

        # ====================================================
        # SIMILAR HISTORICAL BUGS
        # ====================================================

        st.markdown("## 🔎 Similar Historical Bugs")

        if similar_bugs:

            for bug in similar_bugs:

                try:

                    score = float(bug.get("similarity_score", 0))

                except:

                    score = 0

                if score <= 1:

                    percentage = int(score * 100)

                else:

                    percentage = int(score)

                percentage = max(0, min(percentage, 100))

                bug_id = bug.get("bug_id", "")

                title = bug.get("title", "")

                render_html(
                    f"""
                    <div class="similarity-container">

                    <div class="similarity-label">

                    <span>
                    <b>{bug_id}</b>
                    &nbsp;—&nbsp;
                    {title}
                    </span>

                    <span>
                    {percentage}%
                    </span>

                    </div>

                    <div class="similarity-bar">

                    <div
                    class="similarity-fill"
                    style="width:{percentage}%;">
                    </div>

                    </div>

                    </div>
                    """
                )

        else:

            st.info("No historical bugs were found.")

        # ====================================================
        # TRIAGE
        # ====================================================

        st.markdown("## 🚦 Triage")

        render_html(
            f"""
            <div class="card">

            <div class="card-title">
            Classification Reason
            </div>

            <div class="card-text">
            {triage.get(
                "reason",
                "No reason available."
            )}
            </div>

            </div>
            """
        )

        # ====================================================
        # REMEDIATION
        # ====================================================

        st.markdown("## 🛠️ Recommended Remediation")

        render_html(
            f"""
            <div class="fix-box">

            <div class="card-title">
            Recommended Fix
            </div>

            <div class="card-text">
            {remediation.get(
                "recommended_fix",
                "No recommendation available."
            )}
            </div>

            </div>
            """
        )

        # ====================================================
        # FIX STEPS
        # ====================================================

        steps = remediation.get("steps", [])

        if steps:

            st.markdown("### 🔧 Fix Steps")

            for index, step in enumerate(steps, start=1):

                render_html(
                    f"""
                    <div class="card">

                    <div class="card-title">
                    Step {index}
                    </div>

                    <div class="card-text">
                    {step}
                    </div>

                    </div>
                    """
                )

        # ====================================================
        # PREVENTION
        # ====================================================

        prevention = remediation.get("prevention", "")

        if prevention:

            st.markdown("### 🛡️ Prevention")

            render_html(
                f"""
                <div class="prevention-box">
                {prevention}
                </div>
                """
            )

        # ====================================================
        # DEVELOPER RESPONSE
        # ====================================================

        with st.expander("🔧 Developer Response"):

            st.json(result)
