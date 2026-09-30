import streamlit as st
from datetime import date
from pathlib import Path
import tempfile

from swms_engine import generate_pdf, HAZARD_PRESETS, LIKELIHOODS, CONSEQUENCES, risk_code

st.set_page_config(
    page_title="SWMS Generator",
    page_icon="🦺",
    layout="centered",
    initial_sidebar_state="collapsed",
)

TEMPLATE = Path(__file__).with_name("template.pdf")

# Mobile-first styling.
st.markdown("""
<style>
.block-container { max-width: 760px; padding: 1rem 0.9rem 5rem; }
[data-testid="stHeader"] { background: transparent; }
.stButton > button, .stDownloadButton > button { width: 100%; min-height: 3rem; border-radius: 12px; font-weight: 650; }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input { border-radius: 10px; }
div[data-testid="stExpander"] { border-radius: 12px; }
.small-note { color: #666; font-size: .9rem; }
.step-card { padding: .8rem 1rem; border: 1px solid #e6e6e6; border-radius: 14px; margin: .35rem 0; }
</style>
""", unsafe_allow_html=True)

st.title("🦺 SWMS Generator")
st.caption("PR004 • Window Cleaning via Rope Access")
st.warning(
    "This tool populates the supplied SWMS template. A competent person must review the site conditions, "
    "hazards, controls, permits, rescue arrangements and generated document before work starts."
)

if "page" not in st.session_state:
    st.session_state.page = "Home"
if "rows" not in st.session_state:
    st.session_state.rows = []
if "workers" not in st.session_state:
    st.session_state.workers = []
if "generated_pdf" not in st.session_state:
    st.session_state.generated_pdf = None

pages = ["Home", "Job", "Hazards", "Workers", "Generate"]
cols = st.columns(5)
for i, p in enumerate(pages):
    with cols[i]:
        if st.button(p, key=f"nav_{p}", type="primary" if st.session_state.page == p else "secondary"):
            st.session_state.page = p
            st.rerun()


def go(page):
    st.session_state.page = page
    st.rerun()


def risk_select(label, options, key, default_index=0):
    return st.selectbox(label, list(options), format_func=lambda x: f"{x} — {options[x]}", key=key, index=default_index)


if st.session_state.page == "Home":
    st.subheader("Create a site-specific SWMS")
    st.markdown("""
    <div class="step-card"><b>1 · Job</b><br><span class="small-note">Client, site, dates, supervisor and permits.</span></div>
    <div class="step-card"><b>2 · Hazards</b><br><span class="small-note">Add site-specific tasks, hazards, controls and risk ratings.</span></div>
    <div class="step-card"><b>3 · Workers</b><br><span class="small-note">Add workers and acknowledgement information.</span></div>
    <div class="step-card"><b>4 · Generate</b><br><span class="small-note">Create a filled copy of the supplied PR004 PDF.</span></div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("＋ Start New SWMS", type="primary"):
        st.session_state.rows = []
        st.session_state.workers = []
        st.session_state.generated_pdf = None
        st.session_state.page = "Job"
        st.rerun()
    st.info("The standard PR004 rope-access controls remain in the original template. Site-specific entries are added to its identified-onsite-hazards section.")


elif st.session_state.page == "Job":
    st.subheader("1 · Job details")
    st.caption("Fields are saved while this browser session is open.")

    client_name = st.text_input("Client name", key="client_name")
    client_contact = st.text_input("Client contact name", key="client_contact")
    client_address = st.text_input("Client address", key="client_address")
    work_location = st.text_input("Work location", key="work_location")
    work_activity = st.text_input("Work activity", value="Perform Window Cleaning via Rope Access", key="work_activity")
    required_plant = st.text_area("Required plant / equipment", key="required_plant", placeholder="Rope access equipment, buckets, squeegees, water-fed equipment, etc.")

    st.subheader("SWMS administration")
    jsea_preparer = st.text_input("JSEA preparer", key="jsea_preparer")
    jsea_reviewer = st.text_input("JSEA reviewer", key="jsea_reviewer")
    jsea_date_prepared = st.date_input("JSEA date prepared", value=date.today(), key="jsea_date_prepared")
    jsea_provided = st.date_input("JSEA provided to client", value=date.today(), key="jsea_provided")
    swms_preparer = st.text_input("SWMS preparer", key="swms_preparer")
    swms_reviewer = st.text_input("SWMS reviewer", key="swms_reviewer")
    date_prepared = st.date_input("SWMS date prepared", value=date.today(), key="date_prepared")
    swms_provided = st.date_input("SWMS provided to client", value=date.today(), key="swms_provided")
    last_review_date = st.date_input("Last SWMS review date", value=date.today(), key="last_review_date")
    work_date = st.date_input("Date work performed", value=date.today(), key="work_date")
    start_time = st.time_input("Start time", key="start_time")

    st.subheader("Permits / pre-start")
    st.checkbox("Site specific induction", key="site_induction")
    st.checkbox("General induction", key="general_induction")
    st.checkbox("Access permit to work", key="access_permit")
    st.checkbox("Roof access permit", key="roof_access_permit")
    st.checkbox("Working at Heights permit", key="working_at_heights_permit")

    st.subheader("Site roles")
    st.text_input("Site supervisor", key="site_supervisor")
    st.text_input("First aid officer", key="first_aid_officer")
    st.text_input("Lead technician", key="lead_technician")
    st.text_input("Person responsible for compliance", key="compliance_person")
    st.selectbox("Supervisor qualification", ["IRATA/SPRAT Lv 3", "IRATA/SPRAT Lv 2", "IRATA/SPRAT Lv 1"], key="supervisor_qualification")
    st.selectbox("Technician qualification", ["IRATA/SPRAT Technician", "IRATA/SPRAT Lv 3", "IRATA/SPRAT Lv 2", "IRATA/SPRAT Lv 1", "WSAH"], key="technician_qualification")

    if st.button("Continue to Hazards →", type="primary"):
        go("Hazards")


elif st.session_state.page == "Hazards":
    st.subheader("2 · Site-specific hazards")
    st.caption("Add up to five rows to the template's identified onsite hazards table.")

    if len(st.session_state.rows) < 5:
        preset_names = ["— blank row —"] + list(HAZARD_PRESETS.keys())
        preset = st.selectbox("Start with a standard PR004 hazard/control", preset_names, key="preset_choice")
        if st.button("＋ Add hazard row", type="primary"):
            if preset == "— blank row —":
                row = {"number": str(len(st.session_state.rows)+1), "activity":"", "hazard":"", "controls":"", "person":"Supervisor / All Technicians / Technician", "initial_likelihood":3, "initial_consequence":4, "residual_likelihood":2, "residual_consequence":2}
            else:
                p = HAZARD_PRESETS[preset]
                row = {"number":str(len(st.session_state.rows)+1), "activity":preset, "hazard":p["hazard"], "controls":p["controls"], "person":p["person"], "initial_likelihood":p["initial"][0], "initial_consequence":p["initial"][1], "residual_likelihood":p["residual"][0], "residual_consequence":p["residual"][1]}
            st.session_state.rows.append(row)
            st.rerun()

    if not st.session_state.rows:
        st.info("No site-specific rows yet. Add a blank row or choose a PR004 hazard preset above.")

    for i, row in enumerate(st.session_state.rows):
        with st.expander(f"Hazard {i+1}: {row.get('activity') or 'Site-specific task'}", expanded=True):
            row["activity"] = st.text_input("Activity / task", value=row.get("activity", ""), key=f"activity_{i}")
            row["hazard"] = st.text_area("Hazard(s) and risks", value=row.get("hazard", ""), key=f"hazard_{i}")
            row["controls"] = st.text_area("Risk control(s)", value=row.get("controls", ""), key=f"controls_{i}")
            row["person"] = st.text_input("Person responsible", value=row.get("person", "Supervisor / All Technicians / Technician"), key=f"person_{i}")
            row["initial_likelihood"] = st.selectbox("Initial likelihood", list(LIKELIHOODS), index=list(LIKELIHOODS).index(row.get("initial_likelihood", 3)), format_func=lambda x: f"{x} — {LIKELIHOODS[x]}", key=f"il_{i}")
            row["initial_consequence"] = st.selectbox("Initial consequence", list(CONSEQUENCES), index=list(CONSEQUENCES).index(row.get("initial_consequence", 4)), format_func=lambda x: f"{x} — {CONSEQUENCES[x]}", key=f"ic_{i}")
            row["residual_likelihood"] = st.selectbox("Residual likelihood", list(LIKELIHOODS), index=list(LIKELIHOODS).index(row.get("residual_likelihood", 2)), format_func=lambda x: f"{x} — {LIKELIHOODS[x]}", key=f"rl_{i}")
            row["residual_consequence"] = st.selectbox("Residual consequence", list(CONSEQUENCES), index=list(CONSEQUENCES).index(row.get("residual_consequence", 2)), format_func=lambda x: f"{x} — {CONSEQUENCES[x]}", key=f"rc_{i}")
            st.write(f"**Initial:** `{risk_code(row['initial_likelihood'], row['initial_consequence'])}`  ·  **Residual:** `{risk_code(row['residual_likelihood'], row['residual_consequence'])}`")
            if st.button("Remove this hazard", key=f"remove_{i}"):
                st.session_state.rows.pop(i)
                st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Job"):
            go("Job")
    with c2:
        if st.button("Continue to Workers →", type="primary"):
            go("Workers")


elif st.session_state.page == "Workers":
    st.subheader("3 · Workers & acknowledgement")
    st.caption("Add workers who will sign/acknowledge the SWMS. The supplied template supports up to 21 acknowledgement rows.")

    if len(st.session_state.workers) < 21:
        new_name = st.text_input("Worker name", key="new_worker_name")
        if st.button("＋ Add worker", type="primary"):
            if new_name.strip():
                st.session_state.workers.append({"name":new_name.strip(), "role":"IRATA/SPRAT Technician", "induction":True, "date":str(date.today()), "qualification":"IRATA/SPRAT Technician"})
                st.session_state.new_worker_name = ""
                st.rerun()

    for i, worker in enumerate(st.session_state.workers):
        with st.expander(f"{i+1}. {worker['name']}", expanded=False):
            worker["name"] = st.text_input("Name", value=worker["name"], key=f"worker_name_{i}")
            worker["role"] = st.selectbox("Role / responsibility", ["Ops Manager","Ops Supervisor","Supervisor","IRATA/SPRAT Lv 3","IRATA/SPRAT Lv 2","IRATA/SPRAT Lv 1","WSAH","IRATA/SPRAT Technician"], key=f"worker_role_{i}")
            worker["qualification"] = st.selectbox("Qualification", ["IRATA/SPRAT Technician","IRATA/SPRAT Lv 3","IRATA/SPRAT Lv 2","IRATA/SPRAT Lv 1","WSAH"], key=f"worker_qual_{i}")
            worker["induction"] = st.checkbox("Site induction completed", value=worker["induction"], key=f"worker_induction_{i}")
            worker["date"] = str(st.date_input("Acknowledgement date", value=date.fromisoformat(worker["date"]), key=f"worker_date_{i}"))
            if st.button("Remove worker", key=f"remove_worker_{i}"):
                st.session_state.workers.pop(i)
                st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Hazards"):
            go("Hazards")
    with c2:
        if st.button("Continue to Generate →", type="primary"):
            go("Generate")


elif st.session_state.page == "Generate":
    st.subheader("4 · Generate SWMS")
    st.write(f"**Site:** {st.session_state.get('work_location') or 'Not entered'}")
    st.write(f"**Client:** {st.session_state.get('client_name') or 'Not entered'}")
    st.write(f"**Site-specific hazard rows:** {len(st.session_state.rows)}")
    st.write(f"**Workers:** {len(st.session_state.workers)}")

    st.info("The supplied PR004 template already contains its standard rope-access hazards, controls, PPE, risk matrix and supporting documentation references. This step fills the editable fields and your site-specific entries.")

    if st.button("🦺 Generate filled SWMS PDF", type="primary"):
        data = {
            'client_name':st.session_state.get('client_name',''), 'client_contact':st.session_state.get('client_contact',''), 'client_address':st.session_state.get('client_address',''), 'work_location':st.session_state.get('work_location',''),
            'manager':st.session_state.get('manager','Robert Wojtas'), 'mobile':st.session_state.get('mobile','0424382197'), 'work_activity':st.session_state.get('work_activity','Perform Window Cleaning via Rope Access'), 'required_plant':st.session_state.get('required_plant',''),
            'jsea_preparer':st.session_state.get('jsea_preparer',''), 'jsea_reviewer':st.session_state.get('jsea_reviewer',''), 'jsea_date_prepared':str(st.session_state.get('jsea_date_prepared',date.today())), 'jsea_provided':str(st.session_state.get('jsea_provided',date.today())),
            'swms_preparer':st.session_state.get('swms_preparer',''), 'swms_reviewer':st.session_state.get('swms_reviewer',''), 'date_prepared':str(st.session_state.get('date_prepared',date.today())), 'swms_provided':str(st.session_state.get('swms_provided',date.today())), 'last_review_date':str(st.session_state.get('last_review_date',date.today())),
            'work_date':str(st.session_state.get('work_date',date.today())), 'start_time':str(st.session_state.get('start_time','')), 'site_specific':True,
            'site_induction':st.session_state.get('site_induction',False), 'general_induction':st.session_state.get('general_induction',False), 'access_permit':st.session_state.get('access_permit',False), 'roof_access_permit':st.session_state.get('roof_access_permit',False), 'working_at_heights_permit':st.session_state.get('working_at_heights_permit',False),
            'site_supervisor':st.session_state.get('site_supervisor',''), 'first_aid_officer':st.session_state.get('first_aid_officer',''), 'lead_technician':st.session_state.get('lead_technician',''), 'compliance_person':st.session_state.get('compliance_person',''),
            'supervisor_qualification':st.session_state.get('supervisor_qualification','IRATA/SPRAT Lv 3'), 'technician_qualification':st.session_state.get('technician_qualification','IRATA/SPRAT Technician'),
            'site_specific_rows':st.session_state.rows, 'workers':st.session_state.workers,
        }
        # Preserve compatibility with the existing PDF engine's expected row fields.
        for row in data['site_specific_rows']:
            row['risk'] = risk_code(row.get('initial_likelihood',3), row.get('initial_consequence',4))
            row['residual'] = risk_code(row.get('residual_likelihood',2), row.get('residual_consequence',2))
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output = tmp.name
        generate_pdf(TEMPLATE, output, data)
        st.session_state.generated_pdf = Path(output).read_bytes()
        st.success("SWMS generated. Review the complete PDF before issuing it for work.")

    if st.session_state.generated_pdf:
        filename = f"SWMS_PR004_{st.session_state.get('work_location') or 'Site'}.pdf".replace("/", "-")
        st.download_button("⬇️ Download SWMS PDF", data=st.session_state.generated_pdf, file_name=filename, mime="application/pdf", type="primary")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back to Workers"):
            go("Workers")
    with c2:
        if st.button("🏠 Start another SWMS"):
            st.session_state.rows = []
            st.session_state.workers = []
            st.session_state.generated_pdf = None
            st.session_state.page = "Job"
            st.rerun()
