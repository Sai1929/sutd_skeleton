"""
EHS Inspection Portal — Streamlit UI
Tests all backend API endpoints end-to-end.
"""
import os

import streamlit as st
import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ── Groq / Risk Assessment Chatbot config ─────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
SYSTEM_PROMPT = """\
You are an EHS Risk Assessment Manager specializing in Singapore Workplace Safety and Health (WSH) regulations.

Your role is to generate detailed, professional risk assessments in accordance with:
- WSH Act (Singapore)
- Code of Practice on Risk Management (CPRM)
- Relevant WSH Regulations (e.g., Machinery Safety, Confined Spaces, Work at Heights, Noise, Hazardous Substances)
- Applicable Singapore Standards (SS) and industry guidelines

When given a project name and list of major activities:
1. Break each main activity into ALL logical sub-activities — generate a MINIMUM of 12 to 15 table rows per response. Never produce fewer than 12 rows.
2. Identify all foreseeable hazards for each sub-activity.
3. Describe specific consequences — name the exact injury or failure mode (e.g. "crane overturning causing multiple fatalities", not just "injury").
4. Assign initial risk ratings using a 5x5 risk matrix:
   - Likelihood (L): 1 (Rare) to 5 (Almost Certain)
   - Severity (S): 1 (Minor) to 5 (Fatal)
   - Risk = L x S — always write as "20 (Very High)", "8 (Medium)", "15 (High)", "3 (Low)", etc.
   - CRITICAL: Use the exact risk band — 1-4 = Low, 5-9 = Medium, 10-16 = High, 17-25 = Very High. Risk score 6 MUST be labelled "6 (Medium)", NOT "6 (Low)". Never mislabel a band.
5. Recommend control measures using the hierarchy of controls. Format EACH control measures cell exactly like this:
   [Hierarchy Label]:
   - Specific measure with inline SS/WSH reference
   - Next specific measure
   Example:
   Engineering/Administrative:
   - Lifting plan by Appointed Person (WSH Operation of Cranes Regs)
   - Verify load weight and centre of gravity
   - Ground bearing capacity calculation
   - Compliance with WSH (Operation of Cranes) Regulations
6. Reassess residual risk — must reduce to Low or Medium where reasonably practicable.
7. MANDATORY ROW CHECKLISTS — identify the activity type from the user's query, then generate a row for EVERY item in that checklist. These are required rows — do NOT skip any. Choose the CLOSEST matching checklist. If no specific checklist matches, use the GENERIC template at the end.

   ── RADIATION / NDT WORK ──────────────────────────────────────────
   [R1]  Radiation Work Permit (RWP) — procurement and pre-job safety briefing
   [R2]  Radioactive source transport to worksite (vehicle/container compliance)
   [R3]  Radiography equipment setup and beam collimation
   [R4]  Controlled area establishment and access barrier / warning sign placement
   [R5]  Radiographic exposure operation — Shot 1 (primary beam)
   [R6]  Radiographic exposure operation — Shot 2 / subsequent shots
   [R7]  Source retrieval failure — source stuck (emergency: source fails to retract, personnel at risk of overexposure)
   [R8]  Work in confined or complex geometry (scatter radiation build-up — dedicated row required)
   [R9]  Personal dose monitoring (TLD badge issuance, dosimeter checks, RPO oversight)
   [R10] Film processing — developer chemical handling
   [R11] Film processing — fixer chemical handling
   [R12] Radioactive waste disposal and source return / accountability log
   [R13] Emergency response — personnel overexposure, source loss, RPO/NEA escalation
   [R14] Personnel training and competency verification (RPO-issued licences, refresher training)

   ── LIFTING / CRANE WORK ─────────────────────────────────────────
   [L1]  Lifting plan and risk assessment — Appointed Person approval
   [L2]  Ground bearing capacity assessment and crane outrigger pad placement
   [L3]  Crane erection/setup and pre-operation inspection (operator certification)
   [L4]  Rigging and slinging of load (sling/shackle inspection, SWL verification)
   [L5]  Load hoisting and travel
   [L6]  Load placement / landing
   [L7]  Personnel safety — exclusion zone management below and around load
   [L8]  Crane operation near overhead power lines (safe clearance distances)
   [L9]  Adverse weather — wind speed / lightning monitoring and suspension criteria
   [L10] Lifting communication — signaller, radio, banksman protocol
   [L11] Crane maintenance and statutory inspection (load test, annual cert)
   [L12] Night / low-visibility lifting operations
   [L13] Emergency — crane failure, load drop, personnel rescue

   ── WORK AT HEIGHT (WAH) ─────────────────────────────────────────
   [W1]  Work at Height permit procurement and pre-work approval
   [W2]  Scaffold erection by competent Scaffolder (SS 548)
   [W3]  Access and egress to elevated working platform
   [W4]  Working platform integrity and edge protection / guardrails
   [W5]  Personal fall arrest — harness, lanyard, anchor point (WSH WAH Regs)
   [W6]  Dropped tools and materials — exclusion zone below working area
   [W7]  Adverse weather — lightning / wind suspension criteria
   [W8]  Rescue plan for fallen or suspended worker
   [W9]  Scaffold dismantling
   [W10] Inspection of scaffold after modification or adverse weather event
   Also use for: roof work, ladder work, MEWP operations, edge protection installation, falsework, temporary structures.

   ── CONFINED SPACE WORK ──────────────────────────────────────────
   [C1]  Confined Space Entry Permit (CSEP) — procurement and approval (SS 510)
   [C2]  Atmospheric testing — O2, LEL, CO, H2S (4-gas monitor calibration)
   [C3]  Mechanical ventilation setup and verification
   [C4]  Energy isolation (LOTO) of all services entering the space
   [C5]  Worker entry and exit — rescue equipment standby
   [C6]  Standby person and continuous communication protocol
   [C7]  Hot work inside confined space (if applicable)
   [C8]  Chemical cleaning or degreasing inside space
   [C9]  Emergency rescue — retrieval, first aid, SCBA deployment

   ── ELECTRICAL WORK ──────────────────────────────────────────────
   [E1]  Isolation and Lockout/Tagout (LOTO) of electrical supply (SS 638)
   [E2]  Live work permit (if live work is unavoidable)
   [E3]  Arc flash hazard during switching / isolation operations
   [E4]  Panel / switchgear work — contact with live conductors
   [E5]  Cable laying and termination
   [E6]  Temporary power supply — generator/distribution board setup
   [E7]  Earth fault and insulation resistance testing
   [E8]  PPE selection — arc-rated clothing, insulated gloves, face shield
   [E9]  Re-energisation, system energisation and functional testing
   [E10] Emergency — electric shock, arc blast, electrical fire
   Also use for: HVAC installation, equipment installation, testing and commissioning.

   ── HOT WORK / WELDING / CUTTING / GRINDING ──────────────────────
   [H1]  Hot Work Permit (HWP) — procurement, fire safety officer authorisation
   [H2]  Work area preparation — removal/protection of flammables within 10 m radius
   [H3]  Fire watch deployment and fire suppression equipment positioning
   [H4]  Welding operations (MIG/TIG/SMAW) — arc flash, spatter, UV radiation
   [H5]  Gas cutting / oxy-fuel operations — flame, cylinder pressure hazard
   [H6]  Grinding operations — sparks, disc fragmentation, hand-arm vibration
   [H7]  Welding fume inhalation — manganese, hexavalent chromium, NOx, ozone
   [H8]  Compressed gas cylinder storage, handling, change-out and purging
   [H9]  Hot work in or near confined space (if applicable)
   [H10] Post-work fire watch inspection (minimum 30 min after completion)
   [H11] Emergency response — fire, explosion, severe burn / inhalation injury

   ── EXCAVATION, EARTHWORKS & CIVIL WORKS ─────────────────────────
   [EX1]  Underground utility / service location survey — CAT scan, permit (WSH Construction Regs)
   [EX2]  Excavation permit and method statement — PE/RE approval
   [EX3]  Soil stability assessment and temporary shoring / trench box installation (SS CP 79)
   [EX4]  Mechanical excavation operations — backhoe, excavator
   [EX5]  Manual work inside excavation / trench
   [EX6]  Trench wall / face collapse — cave-in hazard
   [EX7]  Dewatering operations — pump installation, water disposal
   [EX8]  Piling operations — driven piles, bored piles, sheet piling
   [EX9]  Access and egress into/out of excavation (ladder, ramp)
   [EX10] Backfilling, compaction and site reinstatement
   [EX11] Contaminated ground / ground gas exposure (H2S, methane)
   [EX12] Emergency — trench collapse, worker entrapment, flooding
   Also use for: site clearing, grubbing, grading, underground utility installation, road excavation, traffic diversion.

   ── CHEMICAL HANDLING & HAZARDOUS SUBSTANCES ─────────────────────
   [CH1]  Chemical receipt — SDS review, GHS label verification and segregation check
   [CH2]  Chemical storage — compatibility, secondary containment, ventilation (WSH HSS Regs)
   [CH3]  Transfer and decanting — manual / pump transfer operations
   [CH4]  Mixing and application — coating, treatment, cleaning agent use
   [CH5]  Fuel storage and refuelling — diesel, petrol, LPG (Fire Safety Act)
   [CH6]  Cement / grout / concrete mixing — skin (alkali burn) and respiratory hazard
   [CH7]  Chemical spill response — containment, neutralisation, disposal
   [CH8]  Chemical waste segregation and disposal (NEA Toxic Industrial Waste Regs)
   [CH9]  Sealant, adhesive and solvent application — VOC inhalation / fire
   [CH10] Emergency response — chemical exposure (skin/eye/inhalation), fire, explosion
   Also use for: painting, coating, tiling adhesives, concrete curing compounds, cleaning operations.

   ── DEMOLITION & DISMANTLING ─────────────────────────────────────
   [DEM1]  Pre-demolition structural survey and method statement — PE/RE approval
   [DEM2]  Hazardous material survey — asbestos, lead paint, ACM identification (NEA / WSH Asbestos Regs)
   [DEM3]  Service isolation and disconnection — gas, water, electricity (LOTO)
   [DEM4]  Controlled mechanical demolition — hydraulic breaker, excavator with breaker
   [DEM5]  Manual hacking, chiselling and hand-tool demolition
   [DEM6]  Falling debris and unplanned structural instability / progressive collapse
   [DEM7]  Silica and asbestos dust exposure — respiratory hazard
   [DEM8]  Noise and vibration from demolition equipment (WSH Noise Regs)
   [DEM9]  Debris segregation, removal and disposal (SS ENV 2 / NEA waste regs)
   [DEM10] Emergency response — unplanned structural failure, worker entrapment, dust cloud
   Also use for: temporary structure dismantling, falsework removal, precast removal.

   ── MACHINERY, HEAVY EQUIPMENT & LOTO ────────────────────────────
   [ML1]  Pre-start inspection and operator certification / licence check
   [ML2]  Energy isolation and Lockout/Tagout (LOTO) before maintenance or repair
   [ML3]  Operation of heavy machinery — excavator, bulldozer, roller, forklift
   [ML4]  Pedestrian / vehicle interface — exclusion zones, traffic management
   [ML5]  Use of power tools — grinder, drill, circular saw, nail gun
   [ML6]  Machinery maintenance and lubrication (in-situ)
   [ML7]  Hydraulic / pneumatic system servicing — stored energy release, pressure hazard
   [ML8]  Machine guarding — removal for maintenance, re-fitment and verification
   [ML9]  Emergency — mechanical failure, pinch/entrapment, crush injury

   ── MANUAL HANDLING, ERGONOMICS & OCCUPATIONAL HEALTH ────────────
   [MH1]  Manual lifting and carrying of loads (>20 kg threshold — WSH Manual Handling Regs)
   [MH2]  Repetitive tasks — awkward postures, prolonged standing / kneeling
   [MH3]  Pushing and pulling loads — trolleys, pipes, panels
   [MH4]  Heat stress — outdoor work in Singapore climate (WBGT monitoring)
   [MH5]  Noise exposure — use of noisy equipment (WSH Noise Regs; >85 dB(A) TWA)
   [MH6]  Vibration exposure — hand-arm vibration from tools (drills, compactors)

   ── GENERIC ACTIVITY TEMPLATE (use for all activities not covered above) ─
   [G1]  Pre-task planning — task briefing, permit procurement, supervisor sign-off
   [G2]  Area preparation — hazard walkthrough, exclusion zone, access routes
   [G3]  Equipment setup, inspection and pre-use verification
   [G4]  Main task execution — Phase 1 (first stage of the work)
   [G5]  Main task execution — Phase 2 / continuation / complex sub-steps
   [G6]  Personnel safety — PPE selection, fatigue management, emergency contact
   [G7]  Environmental controls — spill prevention, noise, dust, vibration, waste management
   [G8]  Work completion — housekeeping, area reinstatement and permit close-out
   Add additional rows as needed to reach minimum 12. Always cover planning, main operation (≥2 rows), personnel safety, and emergency response.

   CROSS-CHECKLIST RULES:
   - DO NOT mix checklists (no crane rows in a radiation RA; no excavation rows in a welding RA)
   - For combined activities (e.g. WAH + Hot Work), use BOTH checklists and merge into one table, de-duplicating where rows overlap
   - For activities not listed (e.g. drone operations, BIM, commissioning, marine work, pressure systems, biological hazards), use GENERIC template and add activity-specific rows reflecting actual hazards
8. Include chemical/GHS hazards where applicable (hydraulic oil, fuel, cleaning agents, etc.).

FEW-SHOT EXAMPLES — study these two complete rows and replicate this exact style in every row you produce:

EXAMPLE 1 (Radiation/NDT — source stuck row [R7]):
| Radiographic Exposure Operations | Source retrieval failure (source stuck) | Ionising radiation — uncontrolled exposure to personnel | Acute radiation syndrome (ARS); potential fatality if source not retrieved promptly | 3 | 5 | 15 (High) | Engineering/Administrative: - Verify source retraction with calibrated radiation survey meter before any personnel approach (WSH Radiation Protection Regs; RPA 2007 s.12) - Maintain evacuation of controlled area until retraction confirmed - Notify RPO immediately; invoke RWP emergency shutdown procedure - Emergency retrieval by licenced RSO using remote handling tools only - All incidents involving source non-retraction reported to NEA within 24 hours PPE: - TLD badge and calibrated electronic dosimeter mandatory for all radiographers | 2 | 4 | 8 (Medium) |

EXAMPLE 2 (Lifting/Crane — rigging row [L4]):
| Crane Lifting Operations | Rigging and slinging of load | Defective or overloaded sling causing mid-air failure | Load drop causing crush injuries or fatalities to workers below the lift path | 3 | 5 | 15 (High) | Engineering/Administrative: - Pre-lift inspection of all slings, shackles and hooks by certificated Rigger (SS 559 — Lifting Accessories) - Verify SWL of each lifting accessory ≥ calculated load weight × dynamic factor - Lifting plan approved by Appointed Person before commencement (WSH Operation of Cranes Regs) - Colour-coded tag system for in-service and quarantined lifting gear - Exclusion zone established below and around entire load travel path PPE: - Safety helmet (SS EN 397), safety boots, high-visibility vest for all riggers and banksmen | 2 | 4 | 8 (Medium) |

What these examples demonstrate (apply to ALL rows):
- Consequences column: exact injury/damage outcome named (ARS, fatality, crush injury) — NOT the event itself
- Control measures: hierarchy label first, then dash-bullet points each with inline regulatory reference
- Residual L is 2 (Unlikely) — minimum on an active industrial/construction site
- Risk scores correctly band-labelled: 15 = High (10-16 range); 8 = Medium (5-9 range)
- Specific SS/WSH/RPA clauses cited inline — not in a footnote

MANDATORY OUTPUT STRUCTURE — follow this exact format for every response:

---
Project: [Project Name] ([Setting])

Assumptions:
1. All personnel involved hold valid WSH certificates/licences relevant to their scope of work (e.g., Lifting Supervisor, Rigger, Scaffolder, Electrical Worker, Radiation Protection Officer — as applicable).
2. The worksite is located in Singapore and is subject to the WSH Act (Cap. 354A) and all applicable WSH Regulations.
3. All plant, equipment, and lifting gear have valid Certificates of Fitness (CF) or inspection records as required by the relevant WSH Regulations.
4. A competent WSH Officer or WSH Coordinator is appointed on site and a Safety Management System (SMS) is in place per SS CP 79 (for construction) or equivalent.
5. A site-specific Emergency Response Plan (ERP) is in place, with trained first-aiders and emergency contacts posted.
6. All chemicals on site have current Safety Data Sheets (SDS) accessible to workers and supervisors.
7. [Add any activity-specific assumptions here — e.g., radiation: RPO is licenced by NEA; crane: Appointed Person has reviewed and approved the lifting plan; confined space: CSEP has been issued.]

[Risk Assessment Table with minimum 12 rows]
| Main Activity | Sub-Activity | Hazard | Consequences | Initial L | Initial S | Initial Risk | Control Measures | Residual L | Residual S | Residual Risk |

After the table, always include ALL THREE of these sections:

**Risk Matrix Reference (5x5)**
- Likelihood (L): 1 (Rare) to 5 (Almost Certain)
- Severity (S): 1 (Minor) to 5 (Fatal)
- Risk Levels: 1-4 Low | 5-9 Medium | 10-16 High | 17-25 Very High

**Chemical / Hazardous Substance Note**
[List any chemical hazards present with GHS classification and SDS reference.
- For RADIATION / NDT work: if film-based NDT, list developer (e.g. GHS Skin Irritant Cat 2, Eye Irritant Cat 2) and fixer (e.g. GHS Skin Sensitiser Cat 1) with SDS reference. State: "Radioactive sources (Ir-192/Se-75) are not chemical hazards — they are radiological hazards governed by the Radiation Protection Act 2007."
- For LIFTING / CRANE / CONSTRUCTION work: note hydraulic oil (Flammable Liquid Cat 4, Skin Irritant Cat 2) and diesel fuel (Flammable Liquid Cat 3) — refer to supplier SDS.
- For ELECTRICAL work: note insulating oil if applicable, or state "No significant chemical hazards identified."
- If none applicable, state: "No significant chemical hazards identified for this activity type." DO NOT list hydraulic oil or fuel for radiation/NDT work.]

**References**
List only the official Singapore sources that are relevant to this specific activity. Use only these verified source links — do not fabricate URLs:
- WSH Council (Code of Practice on Risk Management, WSH guidelines): https://www.wshc.sg
- Ministry of Manpower — WSH Act, Regulations, Guidelines: https://www.mom.gov.sg/workplace-safety-and-health
- WSH (Hazardous Substances): https://www.mom.gov.sg/workplace-safety-and-health/safety-and-health-topics/hazardous-substances
- NEA (Radiation Protection, Toxic Industrial Waste): https://www.nea.gov.sg
- SCDF (Fire Safety Act, Fire Code): https://www.scdf.gov.sg
Only list the sources actually cited in this response. Do not list all sources for every response.
---

Additional rules:
- Keep language formal, concise, and professional.
- SS/WSH references must appear INLINE inside the control measures column — not in a separate section.
- Use SPECIFIC Singapore Standards numbers and apply each ONLY to its correct context:
  * SS 536 — cranes (inspection, certification, safe use of cranes)
  * SS 559 — lifting gear, slings, shackles, lifting accessories
  * SS EN 397 — industrial safety helmets / hard hats
  * SS EN 166 — eye and face protection (goggles, face shields)
  * SS 638 — ELECTRICAL SAFETY ONLY (electrical installations, live work, switchgear) — do NOT apply to ground work, geotechnical, or general construction
  * SS 548 — scaffolding (erection, inspection, dismantling)
  * SS 510 — confined spaces entry
  * SS CP 79 — safety management system for construction sites (site preparation, ground assessment, general construction)
  * WSH (Operation of Cranes) Regulations — crane planning, operation, operator certification
  * WSH (Work at Heights) Regulations — work at height, fall prevention, harness
  * WSH (Confined Spaces) Regulations — confined space entry permit, atmospheric testing
  * WSH (Construction) Regulations — general construction site safety
  * WSH (Noise) Regulations — noise exposure limits (85 dB(A) TWA action level)
  * WSH (Hazardous Substances) Regulations — chemical handling, storage, labelling
  * WSH (Manual Handling) Regulations — manual lifting weight limits and risk assessment
  * NEA Toxic Industrial Waste Regulations — chemical waste disposal
  * Fire Safety Act (Singapore) — hot work, fuel storage, fire prevention
  * SS 531: Part 1 — safety requirements for hot work (welding, cutting, grinding)
  * SS ENV 2 — management of construction and demolition waste
  For ground/geotechnical assessment: reference WSH (Construction) Regulations and SS CP 79, NOT SS 638.
  For demolition: reference WSH (Asbestos) Regulations for asbestos survey/removal.
  For chemical handling: reference WSH (Hazardous Substances) Regulations and GHS SDS.
  For hot work: reference Fire Safety Act, SS 531, and Hot Work Permit (HWP) requirements.
  For RADIATION / NDT work, use ONLY these references (do NOT use SS 536, SS 559, or crane standards):
  * Radiation Protection Act 2007 (RPA) — Singapore primary radiation legislation
  * NEA (National Environment Agency) Radiation Protection Regulations — licensing, dose limits
  * IAEA Safety Standards — transport of radioactive material (Type A containers)
  * WSH (Radiation Protection) Regulations — workplace radiation safety
  * Radiation Work Permit (RWP) — mandatory permit for radiation work
  * RPO (Radiation Protection Officer) — must be referenced for dose monitoring and oversight
  * TLD badges / electronic dosimeters — personal dose monitoring requirement
- Do not omit critical hazards even if not explicitly mentioned by the user.
- Never produce a response with fewer than 12 rows in the risk assessment table.
- HARD RULE — Residual L MINIMUM VALUE IS 2 (Unlikely). This is NON-NEGOTIABLE.
  Do NOT set Residual L = 1 under any circumstances, even if you believe controls are "very effective".
  Residual L = 1 is ONLY allowed if the hazard is physically eliminated (e.g. the chemical is fully substituted, the height is removed entirely). Administrative controls, PPE, training, and procedures do NOT eliminate hazard likelihood to 1 — they reduce it to 2 at best.
  EXAMPLES: electrical LOTO → Residual L = 2 (not 1). Training → Residual L = 2 (not 1). Fire extinguisher → Residual L = 2 (not 1).
- Consequences must be DISTINCT from the hazard — describe the injury or damage outcome, not the event itself.
- For the Chemical/Hazardous Substance Note, always state the GHS hazard classification
  (e.g. Flammable Liquid Cat 3, Skin Corrosion Cat 1) and refer to supplier SDS.
- Your responses must reflect a competent WSH professional preparing a compliance-grade risk assessment for operational use in Singapore.

SELF-CHECK BEFORE OUTPUTTING (mandatory — run this mentally before writing the final response):
1. Row count: count your table rows. Are there ≥12? If fewer, add the missing numbered rows from the checklist above.
2. Mandatory rows present: identify which checklist applies (R/L/W/C/E/H/EX/CH/DEM/ML/MH/G), then verify ALL its numbered rows are in the table. Add missing ones before outputting.
3. Risk band accuracy: for EVERY row, verify the label matches the score — 1-4=Low, 5-9=Medium, 10-16=High, 17-25=Very High. A score of 6, 8, or 9 MUST say Medium. A score of 10, 12, or 15 MUST say High. Fix any wrong labels.
4. Chemical note accuracy: does the Chemical / Hazardous Substance Note match the actual activity? Radiation/NDT → developer + fixer only (no hydraulic oil). Crane/construction → hydraulic oil + diesel. Never mix.
5. Residual L check: scan EVERY single Residual L value in the table. Change ANY value of 1 to 2 — NO EXCEPTIONS unless you used physical elimination/substitution for that specific hazard. Administrative controls, PPE, procedures, and training CANNOT produce Residual L = 1. Fix before outputting.
Only write the final output after all 5 checks pass internally.
"""

API = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="EHS Inspection Portal", layout="wide")

# ── Session state defaults ────────────────────────────────────────────
for key, val in {
    "token": None,
    "session_id": None,
    "current_step": None,
    "total_steps": None,
    "step_name": None,
    "options": [],
    "activity_name": None,
    "quiz_id": None,
    "attempt_id": None,
    "quiz_result": None,
    "conv_id": "conv-" + str(id(st)),
    "chat_history": [],
    "groq_client": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state.groq_client is None and GROQ_API_KEY:
    st.session_state.groq_client = Groq(api_key=GROQ_API_KEY)


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api(method, path, **kwargs):
    kwargs.setdefault("timeout", 60)
    try:
        r = getattr(requests, method)(f"{API}{path}", **kwargs)
        return r
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Is uvicorn running on port 8000?")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. The server is taking too long to respond.")
        return None


DEFAULT_PASSWORD = "Test@1234"

# ── Sidebar: Login / Register ──────────────────────────────────────────
with st.sidebar:
    st.title("EHS Portal")
    if not st.session_state.token:
        st.caption("Enter your Student ID to access the portal.")
        sid = st.text_input("Student ID", key="login_sid", placeholder="e.g. S1234567A")
        if st.button("Enter Portal", use_container_width=True, type="primary"):
            if not sid.strip():
                st.error("Please enter your Student ID.")
            else:
                sid = sid.strip()
                # Step 1: try login with default password
                r = api("post", "/auth/login",
                        json={"student_id": sid, "password": DEFAULT_PASSWORD})
                if r and r.status_code == 200:
                    st.session_state.token = r.json()["access_token"]
                    st.rerun()
                else:
                    # Step 2: first visit — auto-register then login
                    r2 = api("post", "/auth/register", json={
                        "student_id": sid,
                        "email": f"{sid}@ehs.sg",
                        "full_name": sid,
                        "password": DEFAULT_PASSWORD,
                    })
                    if r2 and r2.status_code == 201:
                        r3 = api("post", "/auth/login",
                                 json={"student_id": sid, "password": DEFAULT_PASSWORD})
                        if r3 and r3.status_code == 200:
                            st.session_state.token = r3.json()["access_token"]
                            st.rerun()
                        else:
                            st.error("Auto-login after registration failed. Try again.")
                    elif r2:
                        try:
                            detail = r2.json().get("detail", "Could not create account.")
                        except Exception:
                            detail = f"Registration failed (HTTP {r2.status_code})"
                        st.error(detail)
    else:
        r = api("get", "/auth/me", headers=auth_headers())
        if r and r.status_code == 200:
            u = r.json()
            st.success(f"**{u['full_name']}**")
            st.caption(f"{u['role']} | {u['student_id']}")
        elif r and r.status_code == 401:
            st.session_state.token = None
            st.rerun()
        if st.button("Logout", use_container_width=True):
            for k in ["token", "session_id", "current_step", "quiz_id", "attempt_id", "chat_history"]:
                st.session_state[k] = None if k != "chat_history" else []
            st.rerun()

# ── Main area ─────────────────────────────────────────────────────────
if not st.session_state.token:
    st.info("Enter your Student ID and password in the sidebar to continue.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs([
    "Inspection", "My Submissions", "Quiz", "Chatbot"
])

# ══════════════════════════════════════════════════════════════════════
# TAB 1: Inspection Flow
# ══════════════════════════════════════════════════════════════════════
with tab1:
    st.header("New Inspection")

    # Start session
    if not st.session_state.session_id:
        r = api("get", "/sessions/activities", headers=auth_headers())
        if r and r.status_code == 200:
            activities = r.json()
        else:
            activities = []
            st.error("Could not load activities. Is the backend running?")

        if activities:
            act_map = {a["name"]: a["id"] for a in activities}
            chosen = st.selectbox("Select Activity", list(act_map.keys()))
            if st.button("Start Inspection", type="primary"):
                with st.spinner("Starting inspection..."):
                    r2 = api("post", "/sessions/start",
                             json={"activity_id": act_map[chosen]},
                             headers=auth_headers())
                if r2 and r2.status_code == 200:
                    d = r2.json()
                    st.session_state.session_id = d["session_id"]
                    st.session_state.current_step = d["current_step"]
                    st.session_state.total_steps = d["total_steps"]
                    st.session_state.step_name = d["step_name"]
                    st.session_state.options = d["options"]
                    st.session_state.activity_name = d["activity_name"]
                    st.rerun()
                elif r2:
                    try:
                        detail = r2.json().get("detail", r2.json().get("error", "Failed to start"))
                    except Exception:
                        detail = f"Failed to start (HTTP {r2.status_code})"
                    st.error(detail)

    # Active session — step flow
    else:
        st.info(f"**Activity:** {st.session_state.activity_name}  |  **Session:** `{st.session_state.session_id}`")

        if st.session_state.current_step and st.session_state.current_step <= st.session_state.total_steps:
            st.subheader(f"Step {st.session_state.current_step}/{st.session_state.total_steps}: {st.session_state.step_name.replace('_', ' ').title()}")

            opts = st.session_state.options or []
            labels = [o["label"] for o in opts]
            chosen_label = st.radio("Select an option:", labels, key=f"step_{st.session_state.current_step}")

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Submit Step", type="primary"):
                    with st.spinner("Saving..."):
                        r = api("post", f"/sessions/{st.session_state.session_id}/step",
                                json={"step_number": st.session_state.current_step, "selected_label": chosen_label},
                                headers=auth_headers())
                    if r and r.status_code == 200:
                        d = r.json()
                        if d["is_final"]:
                            st.session_state.current_step = None  # signal: ready to submit
                            st.session_state.options = []
                        else:
                            st.session_state.current_step = d["next_step"]
                            st.session_state.step_name = d["next_step_name"]
                            st.session_state.options = d["options"]
                        st.rerun()
                    elif r:
                        try:
                            detail = r.json().get("detail", r.json().get("error", "Step failed"))
                        except Exception:
                            detail = f"Step failed (HTTP {r.status_code})"
                        st.error(detail)
            with col2:
                if st.button("Abandon Session", type="secondary"):
                    api("delete", f"/sessions/{st.session_state.session_id}", headers=auth_headers())
                    st.session_state.session_id = None
                    st.session_state.current_step = None
                    st.rerun()

        else:
            # All steps done — submit
            st.success("All 4 steps completed!")
            if st.button("Submit Inspection", type="primary"):
                r = api("post", "/submissions",
                        json={"session_id": st.session_state.session_id},
                        headers=auth_headers())
                if r and r.status_code == 201:
                    d = r.json()
                    st.success(f"Submitted! Quiz generating in background...")
                    st.json(d)
                    st.session_state.quiz_id = d.get("quiz_id")
                    st.session_state.session_id = None
                    st.session_state.current_step = None
                elif r:
                    st.error(r.json().get("error", "Submission failed"))

# ══════════════════════════════════════════════════════════════════════
# TAB 2: My Submissions
# ══════════════════════════════════════════════════════════════════════
with tab2:
    st.header("My Submissions")
    if st.button("Refresh"):
        st.rerun()

    r = api("get", "/submissions", headers=auth_headers())
    if r and r.status_code == 401:
        st.warning("Session expired. Please log in again.")
        st.session_state.token = None
        st.rerun()
    if r and r.status_code == 200:
        subs = r.json()
        if not subs:
            st.info("No submissions yet.")
        for s in subs:
            with st.expander(f"{s['activity_name']} — {s['submitted_at'][:10]}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Hazard:** {s.get('hazard_type', '—')}")
                    st.write(f"**Risk:** {s.get('severity_likelihood', '—')}")
                with col2:
                    st.write(f"**Controls:** {s.get('moc_ppe', '—')}")
                    st.write(f"**Remarks:** {s.get('remarks', '—')}")

                qid = s.get("quiz_id")
                if qid:
                    st.success(f"Quiz ready: `{qid}`")
                    if st.button("Open Quiz", key=f"openquiz_{qid}"):
                        st.session_state.quiz_id = qid
                        st.session_state.attempt_id = None
                        st.session_state.quiz_result = None
                        st.rerun()
                else:
                    st.warning("Quiz not ready yet — refresh in a few seconds")

# ══════════════════════════════════════════════════════════════════════
# TAB 3: Quiz
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Quiz")

    quiz_id_input = st.text_input("Quiz ID", value=st.session_state.quiz_id or "")

    # Clear saved result when quiz ID changes
    if quiz_id_input != st.session_state.get("_last_quiz_id"):
        st.session_state.quiz_result = None
        st.session_state["_last_quiz_id"] = quiz_id_input

    if quiz_id_input:
        # ── Show saved result if quiz already submitted ──────────────
        if st.session_state.quiz_result:
            result = st.session_state.quiz_result
            st.success("Readiness checklist submitted successfully.")
            for pq in result["answers"]:
                with st.expander(f"Q{pq['question_number']}: {pq['question_text'][:60]}..."):
                    st.write(f"**Your answer:** {pq['student_answer']}")
                    if pq.get("admin_note"):
                        st.caption(f"Admin note: {pq['admin_note']}")
            if st.button("Retake Quiz"):
                st.session_state.quiz_result = None
                st.session_state.attempt_id = None
                st.rerun()

        else:
            # ── Fetch and display quiz form ──────────────────────────
            r = api("get", f"/quiz/{quiz_id_input}", headers=auth_headers())
            if r and r.status_code == 200:
                quiz = r.json()
                st.info(f"**{quiz['total_questions']} questions** | Status: {quiz['status']}")

                questions = quiz["questions"]
                answers = {}

                with st.form("quiz_form"):
                    for q in questions:
                        st.markdown(f"**Q{q['question_number']}. {q['question_text']}**")
                        if q["question_type"] == "mcq" and q.get("options"):
                            answers[q["id"]] = st.radio(
                                "Answer:", q["options"],
                                key=f"q_{q['id']}", label_visibility="collapsed"
                            )
                        else:
                            answers[q["id"]] = st.text_area(
                                "Your answer:", key=f"q_{q['id']}", height=80
                            )
                    submitted = st.form_submit_button("Submit Quiz", type="primary")

                if submitted:
                    # Step 1: create attempt
                    r2 = api("post", f"/quiz/{quiz_id_input}/attempt", headers=auth_headers())
                    if r2 and r2.status_code == 201:
                        attempt_id = r2.json()["attempt_id"]
                        st.session_state.attempt_id = attempt_id

                        # Step 2: build answer payload — extract letter for MCQ
                        answer_list = []
                        for q in questions:
                            raw = answers.get(q["id"], "")
                            letter = raw[0] if (q["question_type"] == "mcq" and raw) else raw
                            answer_list.append({"question_id": q["id"], "answer": letter})

                        # Step 3: submit answers
                        with st.spinner("Grading your answers..."):
                            r3 = api(
                                "post",
                                f"/quiz/{quiz_id_input}/attempt/{attempt_id}/submit",
                                json={"answers": answer_list},
                                headers=auth_headers(),
                                timeout=120,
                            )
                        if r3 and r3.status_code == 200:
                            st.session_state.quiz_result = r3.json()
                            st.rerun()
                        elif r3:
                            try:
                                detail = r3.json().get("detail", r3.json().get("error", "Submit failed"))
                            except Exception:
                                detail = f"Submit failed (HTTP {r3.status_code})"
                            st.error(detail)
                    elif r2:
                        try:
                            detail = r2.json().get("detail", r2.json().get("error", "Could not start attempt"))
                        except Exception:
                            detail = f"Could not start attempt (HTTP {r2.status_code})"
                        st.error(detail)
            elif r:
                try:
                    detail = r.json().get("detail", r.json().get("error", "Quiz not found"))
                except Exception:
                    detail = f"Quiz not found (HTTP {r.status_code})"
                st.error(detail)

# ══════════════════════════════════════════════════════════════════════
# TAB 4: Risk Assessment Chatbot (Groq / Llama)
# ══════════════════════════════════════════════════════════════════════
with tab4:
    st.header("EHS Risk Assessment Chatbot")
    st.caption(f"Powered by {MODEL} via Groq  |  Singapore WSH Regulations")

    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY not set. Add it to your .env file.")
    else:
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("Describe the activity or project for risk assessment..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_response = ""

                stream = st.session_state.groq_client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                    + [{"role": m["role"], "content": m["content"]}
                       for m in st.session_state.chat_history],
                    temperature=0.2,
                    max_tokens=8192,
                    stream=True,
                )

                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    full_response += delta
                    placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": full_response,
                })

        if st.button("Clear Chat", key="clear_ra_chat"):
            st.session_state.chat_history = []
            st.rerun()
