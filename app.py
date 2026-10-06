import sqlite3
from datetime import date
from html import escape

import pandas as pd
import streamlit as st

DB = "jobs.db"

STATUSES = ["To Apply", "Applied", "Interview", "Offer", "Rejected", "Withdrawn"]

STATUS_EMOJI = {
    "To Apply": "🟡",
    "Applied": "🔵",
    "Interview": "🟣",
    "Offer": "🟢",
    "Rejected": "🔴",
    "Withdrawn": "⚫",
}


# ---------------- Database ----------------

def connect():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            skills TEXT,
            deadline TEXT,
            status TEXT NOT NULL DEFAULT 'To Apply',
            url TEXT,
            notes TEXT
        )
    """)
    return conn


def add_job(company, role, skills, deadline, status, url, notes):
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs
            (company, role, skills, deadline, status, url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (company, role, skills, str(deadline), status, url, notes),
        )


def update_status(job_id, status):
    with connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = ? WHERE id = ?",
            (status, job_id),
        )


def delete_job(job_id):
    with connect() as conn:
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))


def load_jobs():
    with connect() as conn:
        return pd.read_sql_query(
            "SELECT * FROM jobs ORDER BY deadline ASC, id DESC",
            conn,
        )


# ---------------- Page styling ----------------

st.set_page_config(
    page_title="Job Tracker",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Main page */
    .stApp {
        background:
            radial-gradient(
                circle at top left,
                rgba(139, 92, 246, 0.10),
                transparent 32rem
            ),
            #F8F7FC;
    }

    .block-container {
        max-width: 1120px;
        padding-top: 3rem;
        padding-bottom: 5rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }

    /* Hero section */
    .hero {
        padding: 1rem 0 2rem;
    }

    .hero-badge {
        display: inline-block;
        padding: 7px 13px;
        margin-bottom: 14px;
        border-radius: 999px;
        background: #EDE9FE;
        color: #6D28D9;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .hero h1 {
        margin: 0;
        color: #211A38;
        font-size: 3rem;
        line-height: 1.05;
        letter-spacing: -0.06em;
        font-weight: 800;
    }

    .hero p {
        margin: 12px 0 0;
        color: #766D88;
        font-size: 1.05rem;
    }

    /* Add job expander */
    div[data-testid="stExpander"] {
        border: 1px solid #E7E1F2;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.78);
        box-shadow: 0 8px 30px rgba(71, 50, 110, 0.06);
        overflow: hidden;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 700;
        color: #3B2B59;
    }

    /* Inputs */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        border-radius: 11px;
        border-color: #DDD6FE;
        background: #FFFFFF;
    }

    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #8B5CF6;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.12);
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        padding: 18px 20px;
        border: 1px solid #E8E1F2;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.84);
        box-shadow: 0 8px 25px rgba(71, 50, 110, 0.05);
    }

    div[data-testid="stMetricLabel"] {
        color: #81758F;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #30234D;
        font-size: 2rem;
        font-weight: 800;
    }

    /* Job card */
    .job-card {
        position: relative;
        padding: 22px 24px;
        margin: 18px 0 6px;
        border: 1px solid #E7E1F2;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.91);
        box-shadow: 0 10px 30px rgba(71, 50, 110, 0.07);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(71, 50, 110, 0.12);
    }

    .company {
        color: #2B2141;
        font-size: 1.22rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    .role {
        margin-top: 4px;
        color: #776B89;
        font-size: 0.98rem;
    }

    .meta {
        margin-top: 16px;
        color: #766D88;
        font-size: 0.88rem;
    }

    .skills {
        margin-top: 10px;
        color: #504561;
        font-size: 0.9rem;
    }

    .pill {
        display: inline-block;
        margin-top: 14px;
        padding: 6px 11px;
        border-radius: 999px;
        background: #F1EDFF;
        color: #6D28D9;
        font-size: 0.78rem;
        font-weight: 750;
    }
.status-to-apply {
    background: #FEF3C7;
    color: #92400E;
}

.status-applied {
    background: #DBEAFE;
    color: #1D4ED8;
}

.status-interview {
    background: #EDE9FE;
    color: #6D28D9;
}

.status-offer {
    background: #DCFCE7;
    color: #15803D;
}

.status-rejected {
    background: #FEE2E2;
    color: #B91C1C;
}

.status-withdrawn {
    background: #E5E7EB;
    color: #374151;
}
    /* Buttons */
    .stButton > button,
    .stLinkButton > a,
    button[kind="primary"] {
        min-height: 38px;
        border-radius: 10px;
        border: 1px solid #DDD6FE;
        font-weight: 700;
        transition: all 0.2s ease;
    }

    .stButton > button:hover,
    .stLinkButton > a:hover {
        border-color: #8B5CF6;
        color: #6D28D9;
        transform: translateY(-1px);
    }

    button[kind="primary"] {
        background: #8B5CF6;
        color: white;
        border: none;
    }

    button[kind="primary"]:hover {
        background: #7C3AED;
        color: white;
    }

    /* Empty state */
    .empty {
        padding: 80px 24px;
        margin-top: 24px;
        border: 1px dashed #C4B5FD;
        border-radius: 22px;
        background: rgba(255, 255, 255, 0.65);
        text-align: center;
        color: #766D88;
    }

    .empty h3 {
        color: #3B2B59;
    }

    /* Mobile */
    @media (max-width: 640px) {
        .block-container {
            padding: 1.3rem 1rem 4rem;
        }

        .hero h1 {
            font-size: 2.25rem;
        }

        div[data-testid="stMetric"] {
            margin-bottom: 8px;
        }

        .job-card {
            padding: 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------- Header ----------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">Your career dashboard</div>
        <h1>💼 Job Tracker</h1>
        <p>Organize opportunities, track progress, and stay ready for what’s next.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
# ---------------- Load data ----------------

df = load_jobs()

if not df.empty:
    df["deadline_date"] = pd.to_datetime(df["deadline"], errors="coerce").dt.date
    today = date.today()
    df["days_left"] = df["deadline_date"].apply(
        lambda d: (d - today).days if pd.notna(d) else None
    )
else:
    df["days_left"] = pd.Series(dtype="float")


# ---------------- Top actions ----------------

with st.expander("＋ Add a job", expanded=False):
    with st.form("add_job", clear_on_submit=True):
        c1, c2 = st.columns(2)
        company = c1.text_input("Company *", placeholder="Amazon")
        role = c2.text_input("Role *", placeholder="Analyst")

        c3, c4 = st.columns(2)
        deadline = c3.date_input("Deadline", value=date.today())
        status = c4.selectbox("Status", STATUSES, index=0)

        skills = st.text_input(
            "Skills",
            placeholder="SQL, Excel, Power BI",
        )
        url = st.text_input(
            "Job URL",
            placeholder="https://...",
        )
        notes = st.text_area(
            "Notes",
            placeholder="Anything you want to remember about this role...",
        )

        submitted = st.form_submit_button("Save job", use_container_width=True)

        if submitted:
            if not company.strip() or not role.strip():
                st.error("Company and role are required.")
            else:
                add_job(
                    company.strip(),
                    role.strip(),
                    skills.strip(),
                    deadline,
                    status,
                    url.strip(),
                    notes.strip(),
                )
                st.success("Job saved.")
                st.rerun()


# ---------------- Dashboard ----------------

if df.empty:
    st.markdown(
        """
        <div class="empty">
            <h3>No jobs yet</h3>
            <p>Click <b>＋ Add a job</b> above to add your first opportunity.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

total = len(df)
to_apply = int((df["status"] == "To Apply").sum())
interviews = int((df["status"] == "Interview").sum())
due_soon = int(
    ((df["days_left"] >= 0) & (df["days_left"] <= 7)).sum()
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total jobs", total)
m2.metric("To apply", to_apply)
m3.metric("Due soon", due_soon)
m4.metric("Interviews", interviews)

st.write("")


# ---------------- Search / filters ----------------

c1, c2 = st.columns([2, 1])

search = c1.text_input(
    "Search",
    placeholder="Search company, role or skill...",
    label_visibility="collapsed",
)

chosen_status = c2.multiselect(
    "Status",
    STATUSES,
    default=STATUSES,
    label_visibility="collapsed",
)

view = df[df["status"].isin(chosen_status)].copy()

if search.strip():
    query = search.strip().lower()
    searchable = (
        view["company"].fillna("")
        + " "
        + view["role"].fillna("")
        + " "
        + view["skills"].fillna("")
    ).str.lower()

    view = view[searchable.str.contains(query, regex=False)]


st.caption(f"Showing {len(view)} of {len(df)} jobs")


# ---------------- Job cards ----------------

for _, job in view.iterrows():
    status = job["status"]
    emoji = STATUS_EMOJI.get(status, "•")
    status_class = status.lower().replace(" ", "-")

    company_text = escape(str(job["company"]))
    role_text = escape(str(job["role"]))
    skills_text = escape(str(job["skills"])) if job["skills"] else "No skills added"
    notes_text = escape(str(job["notes"])) if job["notes"] else ""

    if pd.isna(job["deadline_date"]):
        deadline_text = "No deadline"
    elif job["days_left"] < 0:
        deadline_text = f"Deadline {job['deadline']} · overdue"
    elif job["days_left"] == 0:
        deadline_text = f"Deadline {job['deadline']} · today"
    elif job["days_left"] == 1:
        deadline_text = f"Deadline {job['deadline']} · 1 day left"
    else:
        deadline_text = f"Deadline {job['deadline']} · {int(job['days_left'])} days left"

    st.markdown(
        f"""
        <div class="job-card">
            <div class="company">{company_text}</div>
            <div class="role">{role_text}</div>
            <span class="pill status-{status_class}">
                {emoji} {status}
            </span>
            <div class="meta">📅 {deadline_text}</div>
            <div class="skills">🧩 {skills_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a1, a2, a3 = st.columns([1, 1, 4])

    if job["url"]:
        a1.link_button("Open job", job["url"], use_container_width=True)

    new_status = a2.selectbox(
        "Status",
        STATUSES,
        index=STATUSES.index(status),
        key=f"status_{job['id']}",
        label_visibility="collapsed",
    )

    if new_status != status:
        update_status(int(job["id"]), new_status)
        st.rerun()

    if job["notes"]:
        with st.expander("Notes"):
            st.write(job["notes"])

    if a3.button("Delete", key=f"delete_{job['id']}"):
        delete_job(int(job["id"]))
        st.rerun()
