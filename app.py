import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from worker import generate_reasoning
from monitor import analyze_chain
from scorer import get_score, get_icon, get_risk_icon

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="AlignmentScope",
    page_icon="🛡️",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0e1a;
    color: #e2e8f0;
  }

  .stApp { background-color: #0a0e1a; }

  /* Header */
  .header-block {
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 2rem;
  }
  .header-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    color: #f8fafc;
    letter-spacing: -0.5px;
  }
  .header-sub {
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 0.25rem;
    font-family: 'IBM Plex Mono', monospace;
  }

  /* Score card */
  .score-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
  }
  .score-number {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 3.5rem;
    font-weight: 600;
    line-height: 1;
  }
  .score-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 0.4rem;
  }

  /* Step cards */
  .step-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
  }
  .step-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #334155;
    min-width: 24px;
    padding-top: 2px;
  }
  .step-text { flex: 1; font-size: 0.9rem; color: #cbd5e1; }
  .step-reason { font-size: 0.78rem; color: #64748b; margin-top: 0.25rem; }

  .badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
  }
  .badge-SAFE     { background:#052e16; color:#4ade80; border:1px solid #166534; }
  .badge-WARNING  { background:#422006; color:#fbbf24; border:1px solid #92400e; }
  .badge-DANGEROUS{ background:#3b0764; color:#e879f9; border:1px solid #7e22ce; }
  .badge-DECEPTIVE{ background:#450a0a; color:#f87171; border:1px solid #991b1b; }

  /* Summary banner */
  .summary-banner {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
  }
  .summary-banner span { color: #e2e8f0; }

  /* Answer box */
  .answer-box {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-left: 3px solid #3b82f6;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    font-size: 0.88rem;
    color: #94a3b8;
    line-height: 1.7;
  }

  /* Prompt input */
  .stTextArea textarea {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
  }
  .stTextArea textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
  }

  /* Button */
  .stButton > button {
    background: #1d4ed8 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    transition: background 0.15s !important;
    width: 100%;
  }
  .stButton > button:hover { background: #2563eb !important; }

  /* Section labels */
  .section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 0.75rem;
  }

  /* Hide streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
</style>
""", unsafe_allow_html=True)


# ── Score colour helper ───────────────────────────────────────
def score_color(score):
    if score >= 75:  return "#4ade80"
    if score >= 50:  return "#fbbf24"
    if score >= 25:  return "#f97316"
    return "#f87171"


# ── Gauge chart ───────────────────────────────────────────────
def alignment_gauge(score):
    color = score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 36, "color": color, "family": "IBM Plex Mono"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#334155",
                     "tickfont": {"color": "#334155", "size": 10}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#0f172a",
            "bordercolor": "#1e293b",
            "steps": [
                {"range": [0,  25], "color": "#1a0a0a"},
                {"range": [25, 50], "color": "#1a1200"},
                {"range": [50, 75], "color": "#0a1a0a"},
                {"range": [75,100], "color": "#0a1520"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": score
            }
        }
    ))
    fig.update_layout(
        height=200, margin=dict(t=20, b=10, l=20, r=20),
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font_color="#e2e8f0"
    )
    return fig


# ── Distribution bar chart ────────────────────────────────────
def distribution_chart(counts):
    labels = list(counts.keys())
    values = list(counts.values())
    colors = {"SAFE": "#4ade80", "WARNING": "#fbbf24",
              "DANGEROUS": "#e879f9", "DECEPTIVE": "#f87171"}
    bar_colors = [colors.get(l, "#64748b") for l in labels]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=bar_colors,
        marker_line_width=0,
        text=values, textposition="outside",
        textfont={"color": "#94a3b8", "size": 11, "family": "IBM Plex Mono"}
    ))
    fig.update_layout(
        height=200,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        xaxis=dict(showgrid=False, tickfont=dict(color="#64748b", size=11,
                   family="IBM Plex Mono"), tickcolor="#0f172a"),
        yaxis=dict(showgrid=False, visible=False),
        showlegend=False
    )
    return fig


# ── App state ─────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None


# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="header-block">
  <div class="header-title">🛡️ AlignmentScope</div>
  <div class="header-sub">reasoning trace monitor · v0.2</div>
</div>
""", unsafe_allow_html=True)


# ── Layout ────────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown('<div class="section-label">Prompt</div>', unsafe_allow_html=True)
    prompt = st.text_area("", placeholder="e.g. Design a marketing campaign for a weight-loss supplement.",
                          height=160, label_visibility="collapsed")
    run = st.button("⟶  Analyze reasoning chain")

    if st.session_state.result:
        analysis   = st.session_state.result["analysis"]
        score      = analysis["overall_alignment_score"]
        risk_level = analysis["overall_risk_level"].upper()
        color      = score_color(score)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Alignment Score</div>', unsafe_allow_html=True)
        st.plotly_chart(alignment_gauge(score), use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="section-label">Risk Distribution</div>', unsafe_allow_html=True)
        step_analyses = analysis["steps"]
        counts = {"SAFE": 0, "WARNING": 0, "DANGEROUS": 0, "DECEPTIVE": 0}
        for s in step_analyses:
            counts[s["label"].upper()] = counts.get(s["label"].upper(), 0) + 1
        st.plotly_chart(distribution_chart(counts), use_container_width=True, config={"displayModeBar": False})

        risk_icon = get_risk_icon(risk_level)
        st.markdown(f"""
        <div class="score-card" style="margin-top:0.5rem">
          <div style="font-size:1.8rem">{risk_icon}</div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:1rem;
                      font-weight:600;color:{color};margin-top:0.25rem">{risk_level}</div>
          <div class="score-label">overall risk level</div>
        </div>
        """, unsafe_allow_html=True)

# ── Right panel ───────────────────────────────────────────────
with right:

    if run and prompt.strip():
        with st.spinner("Generating reasoning chain…"):
            worker_result = generate_reasoning(prompt)
            steps  = worker_result["steps"]
            answer = worker_result["answer"]

        with st.spinner("Auditing with monitor agent…"):
            analysis = analyze_chain(steps)

        st.session_state.result = {
            "steps": steps, "answer": answer, "analysis": analysis
        }
        st.rerun()

    elif run and not prompt.strip():
        st.warning("Enter a prompt first.")

    if st.session_state.result:
        data     = st.session_state.result
        steps    = data["steps"]
        answer   = data["answer"]
        analysis = data["analysis"]
        step_analyses = analysis["steps"]
        summary  = analysis.get("chain_summary", "")

        # Chain summary
        st.markdown(f"""
        <div class="summary-banner">
          chain summary → <span>{summary}</span>
        </div>
        """, unsafe_allow_html=True)

        # Reasoning steps
        st.markdown('<div class="section-label">Reasoning Trace</div>', unsafe_allow_html=True)
        for i, (step, sa) in enumerate(zip(steps, step_analyses), start=1):
            label  = sa["label"].upper()
            reason = sa["reason"]
            st.markdown(f"""
            <div class="step-card">
              <div class="step-num">0{i}</div>
              <div style="flex:1">
                <div class="step-text">{step}</div>
                <div class="step-reason">{reason}</div>
              </div>
              <div><span class="badge badge-{label}">{label}</span></div>
            </div>
            """, unsafe_allow_html=True)

        # Final answer
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Final Answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

    elif not st.session_state.result:
        st.markdown("""
        <div style="height:300px;display:flex;align-items:center;justify-content:center;
                    color:#1e293b;font-family:'IBM Plex Mono',monospace;font-size:0.85rem;
                    border:1px dashed #1e293b;border-radius:12px;">
          enter a prompt and click analyze
        </div>
        """, unsafe_allow_html=True)