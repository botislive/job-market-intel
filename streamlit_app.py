"""
Workforce Market Intelligence — Streamlit Dashboard
A professional analytics dashboard for workforce market data.
Runs on port 8501, reads from FastAPI backend on port 8000.
"""

import datetime as _dt
import html as _html
import json as _json
import os
import re as _re
import time

import pandas as pd


def _strip_html(raw: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = _re.sub(r"<[^>]+>", " ", raw or "")
    text = _html.unescape(text)
    return " ".join(text.split())


def _esc(raw: str) -> str:
    """Escape HTML entities for safe interpolation into HTML templates."""
    return _html.escape(str(raw or ""))


import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _rgba(hex_color: str, alpha: float = 1.0) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


SOURCE_COLORS = {
    "linkedin": "#0A66C2",
    "remotive": "#0D6EFD",
    "remoteok": "#8B5CF6",
    "arbeitnow": "#F59E0B",
    "jobicy": "#10B981",
    "rss": "#EF4444",
    "careers": "#EC4899",
}
SOURCE_LABELS = {
    "linkedin": "LinkedIn",
    "remotive": "Remotive",
    "remoteok": "RemoteOK",
    "arbeitnow": "Arbeitnow",
    "jobicy": "Jobicy",
    "rss": "RSS Feeds",
    "careers": "Fortune 100",
}

ACCENT = "#00D4AA"
ACCENT2 = "#4A90D9"
ACCENT3 = "#9B59B6"
BG_PRIMARY = "#0E1117"
BG_CARD = "#1A1D23"
BG_CARD_HOVER = "#22262E"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#A1A1AA"
TEXT_MUTED = "#71717A"
BORDER = "#27272A"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
ERROR = "#EF4444"


def render_job_card(job: dict, *, show_posted: bool = True, max_skills: int = 8) -> None:
    """Render a clickable job card (components.html avoids Streamlit markdown HTML quirks)."""
    src = job.get("source", "")
    label = SOURCE_LABELS.get(src, src)
    color = SOURCE_COLORS.get(src, "#6366F1")
    company = _esc(job.get("company", "Unknown"))
    title = _esc(job.get("title", "Untitled"))
    location = _esc(job.get("location", "—"))
    url = _esc(job.get("url", "#") or "#")
    skills_raw = job.get("skills", "")
    skill_list = [_esc(s.strip()) for s in skills_raw.split(",") if s.strip()][:max_skills]
    skill_tags = " ".join(
        f'<span style="display:inline-block;padding:3px 10px;border-radius:20px;font-size:0.72rem;'
        f'font-weight:600;background:{ACCENT}15;color:{ACCENT};border:1px solid {ACCENT}30">{s}</span>'
        for s in skill_list
    )
    posted = job.get("posted_at", "")
    posted_html = (
        f' <span style="color:{TEXT_MUTED}">{_esc(str(posted)[:10])}</span>'
        if show_posted and posted
        else ""
    )
    salary = _esc(job.get("salary", ""))
    salary_html = (
        f' <span style="color:{SUCCESS};font-weight:600">{salary}</span>'
        if salary
        else ""
    )
    skills_block = (
        f'<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px">{skill_tags}</div>'
        if skill_tags
        else ""
    )
    card_height = 118 if skill_tags else 88

    components.html(
        f"""<!DOCTYPE html>
<html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 0; font-family: Inter, sans-serif; background: transparent; }}
  .job-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 14px 18px;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
  }}
  .job-card:hover {{
    border-color: {_rgba(ACCENT, 0.25)};
    background: {BG_CARD_HOVER};
  }}
  .job-title {{ color: {TEXT_PRIMARY}; font-size: 1rem; font-weight: 600; margin-bottom: 4px; }}
  .job-meta {{ color: {TEXT_SECONDARY}; font-size: 0.82rem; line-height: 1.5; }}
  .job-company {{ color: {ACCENT}; font-weight: 600; }}
  .badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
  }}
  .row {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }}
</style></head><body>
<a href="{url}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;color:inherit;display:block">
<div class="job-card">
  <div class="row">
    <div style="flex:1;min-width:0">
      <div class="job-title">{title}</div>
      <div class="job-meta">
        <span class="job-company">{company}</span>
        <span style="opacity:0.6"> · </span>{location}{salary_html}
        <span style="opacity:0.6"> · </span>
        <span class="badge" style="background:{color}20;color:{color};border:1px solid {color}40">{_esc(label)}</span>
        {posted_html}
      </div>
    </div>
    <span class="badge" style="background:{ACCENT}15;color:{ACCENT};border:1px solid {ACCENT}30;flex-shrink:0">↗ View</span>
  </div>
  {skills_block}
</div>
</a>
</body></html>""",
        height=card_height,
        scrolling=False,
    )


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        --accent: {ACCENT};
        --accent2: {ACCENT2};
        --accent3: {ACCENT3};
        --bg-primary: {BG_PRIMARY};
        --bg-card: {BG_CARD};
        --bg-card-hover: {BG_CARD_HOVER};
        --text-primary: {TEXT_PRIMARY};
        --text-secondary: {TEXT_SECONDARY};
        --text-muted: {TEXT_MUTED};
        --border: {BORDER};
        --success: {SUCCESS};
        --warning: {WARNING};
        --error: {ERROR};
    }}

    .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: var(--bg-primary);
    }}

    section[data-testid="stSidebar"] {{
        background: {BG_CARD};
        border-right: 1px solid {BORDER};
    }}

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: {TEXT_PRIMARY};
    }}

    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }}

    div[data-testid="stMetric"] {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 20px 24px;
        transition: border-color 0.2s;
    }}
    div[data-testid="stMetric"]:hover {{
        border-color: {ACCENT}40;
    }}
    div[data-testid="stMetric"] label {{
        color: {TEXT_SECONDARY} !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {TEXT_PRIMARY} !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
        font-size: 0.85rem !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0;
        background: {BG_CARD};
        border-radius: 10px;
        padding: 4px;
        border: 1px solid {BORDER};
        margin-bottom: 1.2rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {TEXT_SECONDARY};
        font-weight: 500;
        font-size: 0.85rem;
        padding: 8px 20px;
        border-radius: 8px;
        border: none;
        background: transparent;
    }}
    .stTabs [aria-selected="true"] {{
        color: {TEXT_PRIMARY} !important;
        background: {BG_CARD_HOVER} !important;
        border-bottom: none !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}

    .stButton > button {{
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 8px 20px;
        border: 1px solid {BORDER};
        background: {BG_CARD};
        color: {TEXT_PRIMARY};
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        border-color: {ACCENT};
        color: {ACCENT};
        background: {BG_CARD_HOVER};
    }}
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {{
        background: {ACCENT};
        color: #000;
        border-color: {ACCENT};
    }}
    .stButton > button[data-testid="stBaseButton-primary"]:hover {{
        background: #00B894;
        border-color: #00B894;
        color: #000;
    }}

    div[data-baseweb="input"] {{
        background: {BG_CARD} !important;
        border-color: {BORDER} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="input"]:focus-within {{
        border-color: {ACCENT} !important;
    }}
    div[data-baseweb="select"] {{
        background: {BG_CARD} !important;
        border-color: {BORDER} !important;
        border-radius: 8px !important;
    }}

    .section-header {{
        color: {TEXT_PRIMARY};
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0.5rem 0 0.8rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid {BORDER};
    }}

    .badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}

    .job-card {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 10px;
        transition: border-color 0.2s, background 0.2s;
        cursor: pointer;
    }}
    .job-card:hover {{
        border-color: {ACCENT}40;
        background: {BG_CARD_HOVER};
    }}
    a.job-card-link {{
        text-decoration: none;
        color: inherit;
        display: block;
    }}
    .job-title {{
        color: {TEXT_PRIMARY};
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 4px;
    }}
    .job-meta {{
        color: {TEXT_SECONDARY};
        font-size: 0.82rem;
    }}
    .job-company {{
        color: {ACCENT};
        font-weight: 600;
    }}

    .pipeline-status {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 600;
    }}
    .pipeline-ok {{
        background: {SUCCESS}15;
        color: {SUCCESS};
        border: 1px solid {SUCCESS}30;
    }}
    .pipeline-err {{
        background: {ERROR}15;
        color: {ERROR};
        border: 1px solid {ERROR}30;
    }}
    .pipeline-warn {{
        background: {WARNING}15;
        color: {WARNING};
        border: 1px solid {WARNING}30;
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: {TEXT_PRIMARY} !important;
    }}
    .stMarkdown p {{
        color: {TEXT_SECONDARY};
    }}

    .dataframe-container {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}

    footer {{
        visibility: hidden;
    }}
    #MainMenu {{
        visibility: hidden;
    }}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
def api_get(path: str, params: dict | None = None, timeout: int = 15) -> dict | list | None:
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def api_post(path: str, timeout: int = 300) -> dict | None:
    try:
        r = requests.post(f"{BACKEND_URL}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def check_backend() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/api/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Cached data fetchers
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_stats() -> dict | None:
    return api_get("/api/stats")


@st.cache_data(ttl=300)
def fetch_jobs(
    source: str | None = None,
    company: str | None = None,
    fortune100: bool = False,
    fortune100_company: str | None = None,
    skill: str | None = None,
    q: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict | None:
    params: dict = {"limit": limit, "offset": offset}
    if source:
        params["source"] = source
    if company:
        params["company"] = company
    if fortune100:
        params["fortune100"] = "true"
    if fortune100_company:
        params["fortune100_company"] = fortune100_company
    if skill:
        params["skill"] = skill
    if q:
        params["q"] = q
    return api_get("/api/jobs", params=params)


@st.cache_data(ttl=600)
def fetch_companies() -> list | None:
    return api_get("/api/careers/companies")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚡ Control Center")

        backend_ok = check_backend()
        if backend_ok:
            st.markdown(
                '<span class="pipeline-status pipeline-ok">● Backend Connected</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="pipeline-status pipeline-err">● Backend Offline</span>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### Quick Actions")

        if st.button("🔄 Refresh All Data", use_container_width=True):
            fetch_stats.clear()
            fetch_jobs.clear()
            fetch_companies.clear()
            st.rerun()

        st.markdown("---")

        with st.expander("⚙️ Scrape Operations", expanded=False):
            st.caption("Pull fresh data from all sources")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("All Sources", use_container_width=True, type="primary"):
                    with st.spinner("Scraping..."):
                        result = api_post("/api/scrape")
                    if result:
                        st.success(f"Added {result.get('jobs_added', 0)} new jobs")
                        fetch_stats.clear()
                        fetch_jobs.clear()
                        st.rerun()
                    else:
                        st.error("Scrape failed")
            with c2:
                if st.button("Fortune 100", use_container_width=True):
                    with st.spinner("Scraping career pages..."):
                        result = api_post("/api/scrape/careers")
                    if result:
                        st.success(f"Added {result.get('jobs_added', 0)} new jobs")
                        fetch_stats.clear()
                        fetch_jobs.clear()
                        st.rerun()
                    else:
                        st.error("Scrape failed")

        st.markdown("---")
        st.caption(f"Backend: `{BACKEND_URL}`")
        st.caption(f"Updated: {time.strftime('%H:%M:%S')}")


# ---------------------------------------------------------------------------
# Tab 1: Market Overview
# ---------------------------------------------------------------------------
def tab_market_overview():
    stats = fetch_stats()
    if not stats:
        st.error("Unable to load market data. Check if the backend is running.")
        return

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Jobs", f"{stats['total_jobs']:,}")
    with k2:
        st.metric("Companies", f"{stats['total_companies']:,}")
    with k3:
        st.metric("Data Sources", stats["total_sources"])
    with k4:
        last = stats.get("last_scrape")
        if last:
            try:
                dt = _dt.datetime.fromisoformat(last)
                ago = _dt.datetime.now(_dt.timezone.utc) - dt
                mins = int(ago.total_seconds() / 60)
                label = f"{mins}m ago" if mins < 60 else f"{mins // 60}h {mins % 60}m ago"
            except Exception:
                label = last
        else:
            label = "Never"
        st.metric("Last Sync", label)

    st.markdown('<div style="margin: 0.8rem 0"></div>', unsafe_allow_html=True)

    # Charts row
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<p class="section-header">Jobs by Source</p>', unsafe_allow_html=True)
        by_source = stats.get("by_source", [])
        if by_source:
            df_src = pd.DataFrame(by_source)
            df_src["label"] = df_src["source"].map(lambda s: SOURCE_LABELS.get(s, s.title()))
            df_src["color"] = df_src["source"].map(lambda s: SOURCE_COLORS.get(s, "#6366F1"))
            df_src = df_src.sort_values("count", ascending=True)
            fig = go.Figure(
                go.Bar(
                    x=df_src["count"],
                    y=df_src["label"],
                    orientation="h",
                    marker=dict(color=df_src["color"], cornerradius=4),
                    text=df_src["count"],
                    textposition="outside",
                    textfont=dict(color=TEXT_SECONDARY, size=13),
                    hovertemplate="<b>%{y}</b><br>%{x} jobs<extra></extra>",
                )
            )
            fig.update_layout(
                height=320,
                margin=dict(l=10, r=30, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, showticklabels=False, visible=False),
                yaxis=dict(
                    tickfont=dict(color=TEXT_SECONDARY, size=12),
                    gridcolor="rgba(0,0,0,0)",
                ),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No source data available yet.")

    with col_right:
        st.markdown('<p class="section-header">Top Skills in Demand</p>', unsafe_allow_html=True)
        top_skills = stats.get("top_skills", [])
        if top_skills:
            df_skills = pd.DataFrame(top_skills[:10]).iloc[::-1]
            max_c = df_skills["count"].max()
            fig2 = go.Figure(
                go.Bar(
                    x=df_skills["count"],
                    y=df_skills["skill"],
                    orientation="h",
                    marker=dict(
                        color=df_skills["count"],
                        colorscale=[[0, _rgba(ACCENT, 0.19)], [1, ACCENT]],
                        cornerradius=4,
                    ),
                    text=df_skills["count"],
                    textposition="outside",
                    textfont=dict(color=TEXT_SECONDARY, size=13),
                    hovertemplate="<b>%{y}</b><br>%{x} jobs<extra></extra>",
                )
            )
            fig2.update_layout(
                height=320,
                margin=dict(l=10, r=40, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, showticklabels=False, visible=False),
                yaxis=dict(
                    tickfont=dict(color=TEXT_SECONDARY, size=12),
                    gridcolor="rgba(0,0,0,0)",
                ),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No skill data available yet.")

    # Second row: companies + recent jobs
    col_companies, col_recent = st.columns([1, 1])

    with col_companies:
        st.markdown('<p class="section-header">Top Hiring Companies</p>', unsafe_allow_html=True)
        top_companies = stats.get("top_companies", [])
        if top_companies:
            df_co = pd.DataFrame(top_companies[:10])
            fig3 = go.Figure(
                go.Bar(
                    x=df_co["count"],
                    y=df_co["company"],
                    orientation="h",
                    marker=dict(
                        color=df_co["count"],
                        colorscale=[[0, _rgba(ACCENT2, 0.19)], [1, ACCENT2]],
                        cornerradius=4,
                    ),
                    text=df_co["count"],
                    textposition="outside",
                    textfont=dict(color=TEXT_SECONDARY, size=13),
                    hovertemplate="<b>%{y}</b><br>%{x} jobs<extra></extra>",
                )
            )
            fig3.update_layout(
                height=380,
                margin=dict(l=10, r=40, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, showticklabels=False, visible=False),
                yaxis=dict(
                    tickfont=dict(color=TEXT_SECONDARY, size=12),
                    gridcolor="rgba(0,0,0,0)",
                ),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No company data available yet.")

    with col_recent:
        st.markdown('<p class="section-header">Latest Postings</p>', unsafe_allow_html=True)
        recent = stats.get("recent_jobs", [])
        if recent:
            for j in recent[:8]:
                render_job_card(j, show_posted=False, max_skills=5)
        else:
            st.info("No recent jobs available yet.")


# ---------------------------------------------------------------------------
# Tab 2: Job Explorer
# ---------------------------------------------------------------------------
def tab_job_explorer():
    st.markdown('<p class="section-header">Job Explorer</p>', unsafe_allow_html=True)

    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        search_q = st.text_input("🔍 Search", placeholder="Title, company, description...", key="job_search")
    with f2:
        stats_data = fetch_stats()
        source_options = ["All"] + [
            SOURCE_LABELS.get(s["source"], s["source"])
            for s in (stats_data.get("by_source", []) if stats_data else [])
        ]
        sel_source = st.selectbox("Source", source_options, key="job_source")
    with f3:
        sel_skill = st.text_input("Skill", placeholder="e.g. Python, React...", key="job_skill")
    with f4:
        job_type_options = ["All", "Full-time", "Contract", "Part-time", "Internship"]
        sel_job_type = st.selectbox("Job Type", job_type_options, key="job_type")

    # Resolve source filter
    source_filter = None
    if sel_source != "All":
        for k, v in SOURCE_LABELS.items():
            if v == sel_source:
                source_filter = k
                break

    # Pagination
    if "job_page" not in st.session_state:
        st.session_state.job_page = 0
    PAGE_SIZE = 20
    offset = st.session_state.job_page * PAGE_SIZE

    # Fetch
    data = fetch_jobs(
        source=source_filter,
        skill=sel_skill if sel_skill else None,
        q=search_q if search_q else None,
        limit=PAGE_SIZE + 1,
        offset=offset,
    )

    if not data:
        st.error("Unable to load jobs. Check if the backend is running.")
        return

    total = data.get("total", 0)
    jobs = data.get("jobs", [])
    has_next = len(jobs) > PAGE_SIZE
    jobs = jobs[:PAGE_SIZE]

    # Filter by job_type client-side (API doesn't filter on it)
    if sel_job_type != "All":
        jobs = [j for j in jobs if j.get("job_type", "").lower() == sel_job_type.lower()]

    # Header with count
    col_h1, col_h2 = st.columns([1, 1])
    with col_h1:
        st.caption(f"Showing {len(jobs)} of {total} jobs")
    with col_h2:
        if jobs:
            df_export = pd.DataFrame(
                [
                    {
                        "Title": j["title"],
                        "Company": j["company"],
                        "Location": j["location"],
                        "Source": SOURCE_LABELS.get(j["source"], j["source"]),
                        "Skills": j["skills"],
                        "Job Type": j["job_type"],
                        "Posted": j["posted_at"],
                        "URL": j["url"],
                    }
                    for j in jobs
                ]
            )
            csv = df_export.to_csv(index=False)
            st.download_button(
                "📥 Export CSV",
                csv,
                file_name="jobs_export.csv",
                mime="text/csv",
                use_container_width=False,
            )

    # Job cards
    if not jobs:
        st.info("No jobs match your filters.")
    else:
        for j in jobs:
            render_job_card(j)

    # Pagination controls
    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.session_state.job_page > 0:
            if st.button("← Previous", use_container_width=True, key="prev_page"):
                st.session_state.job_page -= 1
                st.rerun()
    with p3:
        if has_next:
            if st.button("Next →", use_container_width=True, type="primary", key="next_page"):
                st.session_state.job_page += 1
                st.rerun()


# ---------------------------------------------------------------------------
# Tab 3: Skills Intelligence
# ---------------------------------------------------------------------------
def tab_skills_intelligence():
    stats = fetch_stats()
    if not stats:
        st.error("Unable to load data.")
        return

    top_skills = stats.get("top_skills", [])
    if not top_skills:
        st.info("No skill data available. Run a scrape first.")
        return

    st.markdown('<p class="section-header">Skills Landscape</p>', unsafe_allow_html=True)

    # Skills by source breakdown
    st.markdown("### Skill Distribution by Source")

    all_jobs_data = fetch_jobs(limit=200)
    if all_jobs_data and all_jobs_data.get("jobs"):
        jobs = all_jobs_data["jobs"]
        skill_source_rows = []
        for j in jobs:
            src = j.get("source", "unknown")
            skills = [s.strip() for s in j.get("skills", "").split(",") if s.strip()]
            for skill in skills[:5]:
                skill_source_rows.append(
                    {"skill": skill, "source": SOURCE_LABELS.get(src, src)}
                )

        if skill_source_rows:
            df_ss = pd.DataFrame(skill_source_rows)
            skill_counts = df_ss["skill"].value_counts().head(12).index.tolist()
            df_filtered = df_ss[df_ss["skill"].isin(skill_counts)]
            cross = pd.crosstab(df_filtered["skill"], df_filtered["source"])

            fig_heat = px.imshow(
                cross.values,
                labels=dict(x="Source", y="Skill", color="Count"),
                x=cross.columns.tolist(),
                y=cross.index.tolist(),
                color_continuous_scale=[[0, "#0E1117"], [0.25, _rgba(ACCENT, 0.19)], [1, ACCENT]],
                aspect="auto",
            )
            fig_heat.update_layout(
                height=420,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color=TEXT_SECONDARY),
                xaxis=dict(tickfont=dict(size=11, color=TEXT_SECONDARY)),
                yaxis=dict(tickfont=dict(size=11, color=TEXT_SECONDARY)),
                coloraxis_colorbar=dict(
                    tickfont=dict(color=TEXT_SECONDARY),
                    title_font=dict(color=TEXT_SECONDARY),
                ),
            )
            st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # Full skills table
    st.markdown("### All Skills Ranking")
    df_skills = pd.DataFrame(top_skills)
    df_skills.columns = ["Skill", "Job Count"]
    df_skills["% of Total"] = (df_skills["Job Count"] / df_skills["Job Count"].sum() * 100).round(1)
    df_skills["Rank"] = range(1, len(df_skills) + 1)
    df_skills = df_skills[["Rank", "Skill", "Job Count", "% of Total"]]

    st.dataframe(
        df_skills,
        use_container_width=True,
        hide_index=True,
        height=min(len(df_skills) * 35 + 40, 500),
    )

    # Skills pie
    col_pie1, col_pie2 = st.columns(2)
    with col_pie1:
        st.markdown("### Skill Concentration")
        top_5 = pd.DataFrame(top_skills[:5])
        if not top_5.empty:
            other_count = sum(s["count"] for s in top_skills[5:])
            pie_data = pd.concat(
                [
                    top_5,
                    pd.DataFrame([{"skill": "Other", "count": other_count}]),
                ],
                ignore_index=True,
            )
            fig_pie = px.pie(
                pie_data,
                values="count",
                names="skill",
                hole=0.55,
                color_discrete_sequence=[
                    ACCENT,
                    ACCENT2,
                    ACCENT3,
                    "#F59E0B",
                    "#EF4444",
                    "#6B7280",
                ],
            )
            fig_pie.update_layout(
                height=320,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color=TEXT_SECONDARY),
                legend=dict(
                    font=dict(size=11, color=TEXT_SECONDARY),
                    bgcolor="rgba(0,0,0,0)",
                ),
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    with col_pie2:
        st.markdown("### Source Reliability")
        by_source = stats.get("by_source", [])
        if by_source:
            df_rel = pd.DataFrame(by_source)
            df_rel["label"] = df_rel["source"].map(lambda s: SOURCE_LABELS.get(s, s.title()))
            df_rel["color"] = df_rel["source"].map(lambda s: SOURCE_COLORS.get(s, "#6366F1"))
            fig_rel = px.pie(
                df_rel,
                values="count",
                names="label",
                hole=0.55,
                color_discrete_sequence=df_rel["color"].tolist(),
            )
            fig_rel.update_layout(
                height=320,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color=TEXT_SECONDARY),
                legend=dict(
                    font=dict(size=11, color=TEXT_SECONDARY),
                    bgcolor="rgba(0,0,0,0)",
                ),
            )
            fig_rel.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_rel, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Tab 4: Company Intelligence
# ---------------------------------------------------------------------------
def tab_company_intelligence():
    stats = fetch_stats()
    companies_data = fetch_companies()

    if not stats:
        st.error("Unable to load data.")
        return

    st.markdown('<p class="section-header">Fortune 100 Hiring Tracker</p>', unsafe_allow_html=True)

    if companies_data:
        df_f100 = pd.DataFrame(companies_data)
        df_f100_hiring = df_f100[df_f100["job_count"] > 0].sort_values("job_count", ascending=False)

        if not df_f100_hiring.empty:
            col_f1, col_f2 = st.columns([2, 1])

            with col_f1:
                st.markdown("### Active Fortune 100 Recruiters")
                fig_f100 = go.Figure(
                    go.Bar(
                        x=df_f100_hiring["job_count"].head(15),
                        y=df_f100_hiring["name"].head(15),
                        orientation="h",
                        marker=dict(
                            color=df_f100_hiring["job_count"].head(15),
                            colorscale=[[0, _rgba(ACCENT3, 0.25)], [1, ACCENT3]],
                            cornerradius=4,
                        ),
                        text=df_f100_hiring["job_count"].head(15),
                        textposition="outside",
                        textfont=dict(color=TEXT_SECONDARY, size=13),
                    )
                )
                fig_f100.update_layout(
                    height=max(350, len(df_f100_hiring.head(15)) * 35),
                    margin=dict(l=10, r=50, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, showticklabels=False, visible=False),
                    yaxis=dict(
                        tickfont=dict(color=TEXT_SECONDARY, size=12),
                        autorange="reversed",
                    ),
                    font=dict(family="Inter, sans-serif"),
                )
                st.plotly_chart(fig_f100, use_container_width=True, config={"displayModeBar": False})

            with col_f2:
                st.markdown("### Hiring Summary")
                total_f100_jobs = df_f100_hiring["job_count"].sum()
                st.metric("Fortune 100 Jobs", f"{total_f100_jobs:,}")
                st.metric("Companies Hiring", len(df_f100_hiring))
                st.metric(
                    "Coverage",
                    f"{len(df_f100_hiring)}/{len(df_f100)} companies",
                )

                st.markdown("---")
                st.markdown("### Country Distribution")
                country_counts = df_f100_hiring["country"].value_counts()
                for country, count in country_counts.items():
                    st.markdown(f"**{country}**: {count} companies")

        else:
            st.info("No Fortune 100 companies have active job listings yet. Try running a Fortune 100 scrape.")

        st.markdown("---")

        # Full Fortune 100 table
        st.markdown("### Complete Fortune 100 Directory")
        df_display = df_f100[["rank", "name", "country", "job_count"]].copy()
        df_display.columns = ["Rank", "Company", "Country", "Jobs"]
        df_display = df_display.sort_values("Rank")

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=min(len(df_display) * 35 + 40, 500),
        )
    else:
        st.info("Unable to load Fortune 100 data.")

    st.markdown("---")

    # Company comparison by source
    st.markdown('<p class="section-header">Company × Source Matrix</p>', unsafe_allow_html=True)

    jobs_data = fetch_jobs(limit=200)
    if jobs_data and jobs_data.get("jobs"):
        df_jobs = pd.DataFrame(jobs_data["jobs"])
        top_cos = df_jobs["company"].value_counts().head(10).index.tolist()
        df_top = df_jobs[df_jobs["company"].isin(top_cos)]
        df_top["source_label"] = df_top["source"].map(lambda s: SOURCE_LABELS.get(s, s))
        cross_co = pd.crosstab(df_top["company"], df_top["source_label"])

        fig_co = px.imshow(
            cross_co.values,
            labels=dict(x="Source", y="Company", color="Jobs"),
            x=cross_co.columns.tolist(),
            y=cross_co.index.tolist(),
            color_continuous_scale=[[0, "#0E1117"], [0.2, _rgba(ACCENT2, 0.13)], [1, ACCENT2]],
            aspect="auto",
        )
        fig_co.update_layout(
            height=max(300, len(cross_co) * 35 + 80),
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color=TEXT_SECONDARY),
            xaxis=dict(tickfont=dict(size=11, color=TEXT_SECONDARY)),
            yaxis=dict(tickfont=dict(size=11, color=TEXT_SECONDARY)),
            coloraxis_colorbar=dict(
                tickfont=dict(color=TEXT_SECONDARY),
                title_font=dict(color=TEXT_SECONDARY),
            ),
        )
        st.plotly_chart(fig_co, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Tab 5: Data Pipeline
# ---------------------------------------------------------------------------
def tab_data_pipeline():
    st.markdown('<p class="section-header">Data Pipeline Monitor</p>', unsafe_allow_html=True)

    backend_ok = check_backend()

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        status_cls = "pipeline-ok" if backend_ok else "pipeline-err"
        status_txt = "Healthy" if backend_ok else "Offline"
        st.markdown(
            f'<div class="job-card"><div class="job-meta">Backend Status</div>'
            f'<div style="margin-top:6px"><span class="pipeline-status {status_cls}">● {status_txt}</span></div></div>',
            unsafe_allow_html=True,
        )
    with col_s2:
        stats = fetch_stats()
        total = stats["total_jobs"] if stats else 0
        st.markdown(
            f'<div class="job-card"><div class="job-meta">Total Jobs in DB</div>'
            f'<div style="margin-top:6px;color:{ACCENT};font-size:1.4rem;font-weight:700">{total:,}</div></div>',
            unsafe_allow_html=True,
        )
    with col_s3:
        last = stats.get("last_scrape") if stats else None
        if last:
            try:
                dt = _dt.datetime.fromisoformat(last)
                st.markdown(
                    f'<div class="job-card"><div class="job-meta">Last Scrape</div>'
                    f'<div style="margin-top:6px;color:{TEXT_PRIMARY};font-size:1rem;font-weight:600">{dt.strftime("%Y-%m-%d %H:%M")}</div></div>',
                    unsafe_allow_html=True,
                )
            except Exception:
                pass
        else:
            st.markdown(
                f'<div class="job-card"><div class="job-meta">Last Scrape</div>'
                f'<div style="margin-top:6px;color:{TEXT_MUTED}">No scrapes yet</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div style="margin: 0.8rem 0"></div>', unsafe_allow_html=True)

    # Trigger section
    st.markdown("### Trigger Scrape")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(
            f"""
            <div class="job-card">
                <div class="job-title">Full Scrape</div>
                <div class="job-meta" style="margin-top:4px">
                    Pulls from all 9 data sources: LinkedIn, Remotive, RemoteOK, Arbeitnow,
                    Jobicy, RSS feeds, and Fortune 100 career pages.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("▶ Run Full Scrape", use_container_width=True, type="primary", key="full_scrape"):
            with st.spinner("Running full scrape across all sources..."):
                result = api_post("/api/scrape")
            if result:
                st.success(
                    f"Scrape completed: {result.get('jobs_added', 0)} added, "
                    f"{result.get('jobs_updated', 0)} updated in "
                    f"{result.get('duration_seconds', 0):.1f}s"
                )
                fetch_stats.clear()
                fetch_jobs.clear()
                fetch_companies.clear()
            else:
                st.error("Scrape request failed.")

    with col_t2:
        st.markdown(
            f"""
            <div class="job-card">
                <div class="job-title">Fortune 100 Only</div>
                <div class="job-meta" style="margin-top:4px">
                    Targets career pages of Fortune Global 500 companies via
                    Workday, Greenhouse, Lever, SmartRecruiters, and more.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("▶ Run Fortune 100 Scrape", use_container_width=True, key="f100_scrape"):
            with st.spinner("Scraping Fortune 100 career pages..."):
                result = api_post("/api/scrape/careers")
            if result:
                st.success(
                    f"Scrape completed: {result.get('jobs_added', 0)} added, "
                    f"{result.get('jobs_updated', 0)} updated in "
                    f"{result.get('duration_seconds', 0):.1f}s"
                )
                fetch_stats.clear()
                fetch_jobs.clear()
                fetch_companies.clear()
            else:
                st.error("Scrape request failed.")

    st.markdown("---")

    # Source breakdown detail
    st.markdown("### Source Data Quality")
    if stats and stats.get("by_source"):
        by_source = stats["by_source"]
        df_src = pd.DataFrame(by_source)
        df_src["Source"] = df_src["source"].map(lambda s: SOURCE_LABELS.get(s, s.title()))
        df_src["Jobs"] = df_src["count"]
        df_src["% of Total"] = (df_src["count"] / df_src["count"].sum() * 100).round(1)
        df_src["Avg Skills/Job"] = "—"
        df_display = df_src[["Source", "Jobs", "% of Total"]].copy()
        st.dataframe(df_display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    render_sidebar()

    # Header
    st.markdown(
        f"""
        <div style="margin-bottom:0.2rem">
            <h1 style="margin:0;font-size:1.6rem;font-weight:700;color:{TEXT_PRIMARY}">
                Workforce Market Intelligence
            </h1>
            <p style="margin:0.3rem 0 0 0;color:{TEXT_SECONDARY};font-size:0.88rem">
                Real-time job market analytics across 9 data sources
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "📊 Market Overview",
        "🔍 Job Explorer",
        "🧠 Skills Intelligence",
        "🏢 Company Intelligence",
        "⚙️ Data Pipeline",
    ])

    with tabs[0]:
        tab_market_overview()
    with tabs[1]:
        tab_job_explorer()
    with tabs[2]:
        tab_skills_intelligence()
    with tabs[3]:
        tab_company_intelligence()
    with tabs[4]:
        tab_data_pipeline()


if __name__ == "__main__":
    main()
