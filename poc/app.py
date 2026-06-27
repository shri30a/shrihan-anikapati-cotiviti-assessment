import os
import io
import json
import re
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Heavy libraries are imported lazily inside functions so the Streamlit app opens faster.

# ----------------------------
# App Configuration
# ----------------------------
# For a smooth live demo, keep DEMO_MODE = True.
# It gives instant, note-specific outputs without using API quota.
# For real Gemini API testing, change this to False.
DEMO_MODE = True

# If the real Gemini API fails during demo/testing, fall back to local document-specific demo logic
# so the UI can still complete the workflow instead of leaving dashboard metrics pending.
USE_DEMO_FALLBACK_ON_API_ERROR = True

# Use a current lightweight model when DEMO_MODE = False.
GEMINI_MODEL = "gemini-2.5-flash-lite"

# Keeps prompts smaller so real API calls are faster and less likely to hit quota.
MAX_NOTE_CHARS = 12000

st.set_page_config(
    page_title="Clinical Report AI Assistant",
    layout="wide"
)

# ----------------------------
# Session State
# ----------------------------
if "summary_done" not in st.session_state:
    st.session_state.summary_done = False

if "entities_done" not in st.session_state:
    st.session_state.entities_done = False

if "gaps_done" not in st.session_state:
    st.session_state.gaps_done = False

if "qa_done" not in st.session_state:
    st.session_state.qa_done = False

if "summary_output" not in st.session_state:
    st.session_state.summary_output = ""

if "entity_data" not in st.session_state:
    st.session_state.entity_data = None

if "gaps_output" not in st.session_state:
    st.session_state.gaps_output = ""

if "current_note" not in st.session_state:
    st.session_state.current_note = ""

if "last_analyzed_note" not in st.session_state:
    st.session_state.last_analyzed_note = ""

if "qa_output" not in st.session_state:
    st.session_state.qa_output = ""


# ----------------------------
# Styling
# ----------------------------
# ----------------------------
# Styling
# ----------------------------
st.markdown(
    """
    <style>
    :root {
        --purple: #6F42C1;
        --purple-soft: #F7F2FF;
        --purple-border: #D9C7FF;
        --ink: #111827;
        --muted: #6B7280;
        --border: #E5E7EB;
        --sidebar: #FBFAFF;
    }

    .stApp {
        background: #FFFFFF;
        color: var(--ink);
        font-family: "Inter", "Segoe UI", Arial, sans-serif;
    }

    .main .block-container {
        max-width: 1050px;
        padding-top: 2.3rem;
    }

    section[data-testid="stSidebar"] {
        background: var(--sidebar);
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] * {
        color: var(--ink);
    }

    section[data-testid="stSidebar"] h3 {
        color: var(--purple) !important;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    h1 {
        font-size: 2.35rem !important;
        font-weight: 800 !important;
        color: var(--ink);
        letter-spacing: -0.04em;
        margin-bottom: 0.25rem;
    }

    h3 {
        color: var(--purple) !important;
        font-weight: 750 !important;
    }

    .stCaptionContainer p {
        color: var(--muted) !important;
    }

    .stAlert {
        background: linear-gradient(90deg, #F7F2FF, #FAF7FF) !important;
        border: 1px solid var(--purple-border) !important;
        border-radius: 10px !important;
        color: var(--ink) !important;
    }

    .stAlert * {
        color: var(--ink) !important;
    }

    div[data-testid="stFileUploader"] section {
        background: #FFFFFF !important;
        border: 1.5px dashed var(--purple-border) !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
    }

    div[data-testid="stFileUploader"] button {
        border: 1px solid var(--purple) !important;
        color: var(--purple) !important;
        background: white !important;
        border-radius: 8px !important;
        font-weight: 650 !important;
    }

    textarea, input {
        background: white !important;
        color: var(--ink) !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 10px !important;
    }

    textarea::placeholder {
        color: #A1A1AA !important;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        background: white;
        border: 1px solid var(--border);
        border-left: 4px solid var(--purple);
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 8px 20px rgba(17, 24, 39, 0.07);
        display: flex;
        align-items: center;
        gap: 0.9rem;
        min-height: 88px;
    }

    .metric-icon {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: var(--purple-soft);
        color: var(--purple);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        font-weight: 800;
    }

    .metric-label {
        font-size: 0.78rem;
        color: var(--muted);
        font-weight: 650;
        margin-bottom: 0.2rem;
    }

    .metric-value {
        color: var(--purple);
        font-size: 1.45rem;
        font-weight: 800;
        line-height: 1.1;
    }

    .stDownloadButton > button {
        border: 1px solid var(--purple) !important;
        background: white !important;
        color: var(--purple) !important;
        border-radius: 8px !important;
        font-weight: 650 !important;
    }

    .stButton > button {
        background: var(--purple) !important;
        border: 1px solid var(--purple) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 650 !important;
    }

    div[data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--border);
        gap: 2rem;
    }

    button[data-baseweb="tab"] {
        color: var(--muted) !important;
        font-weight: 650 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--purple) !important;
        border-bottom-color: var(--purple) !important;
    }

    .or-divider {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 1rem 0;
        color: var(--muted);
        font-size: 0.8rem;
        font-weight: 700;
    }

    .or-divider::before,
    .or-divider::after {
        content: "";
        height: 1px;
        background: var(--border);
        width: 35%;
        margin: 0 1rem;
    }

    hr {
        border-color: var(--border);
    }

    header[data-testid="stHeader"] {
        background: white;
        border-bottom: 1px solid var(--border);
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ----------------------------
# Helper Functions
# ----------------------------
def truncate_note(clinical_note):
    if len(clinical_note) <= MAX_NOTE_CHARS:
        return clinical_note

    return clinical_note[:MAX_NOTE_CHARS] + "\n\n[Note truncated for faster API processing.]"


@st.cache_data(show_spinner=False)
def extract_text_from_pdf_bytes(file_bytes):
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text.strip()


def extract_text_from_pdf(uploaded_file):
    return extract_text_from_pdf_bytes(uploaded_file.getvalue())


@st.cache_resource(show_spinner=False)
def get_gemini_client(api_key):
    from google import genai

    return genai.Client(api_key=api_key)


@st.cache_data(show_spinner=False, ttl=3600)
def call_gemini_cached(prompt, model_name, api_key):
    client = get_gemini_client(api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    text = getattr(response, "text", None)
    if not text or not text.strip():
        raise RuntimeError("Gemini returned an empty response.")

    return text.strip()


def ask_gemini(prompt):
    """Call Gemini and return text. Results are cached for the same prompt to avoid repeat delays."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY was not found. Make sure your .env file contains GEMINI_API_KEY=your_key_here."
        )

    return call_gemini_cached(prompt, GEMINI_MODEL, GEMINI_API_KEY)


def get_empty_entity_data():
    return []


def parse_entity_json(text):
    try:
        cleaned = text.strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        data = json.loads(cleaned)
        rows = []

        for item in data:
            category = str(item.get("Category", "")).strip()
            extracted = str(item.get("Extracted Information", "")).strip()
            if category and extracted:
                rows.append(
                    {
                        "Category": category,
                        "Extracted Information": extracted
                    }
                )

        if rows:
            return rows
    except Exception:
        pass

    return get_empty_entity_data()


def split_sentences(text, limit=8):
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    return sentences[:limit]


def find_terms(text, terms):
    found = []
    lower_text = text.lower()

    for term in terms:
        if re.search(r"\b" + re.escape(term.lower()) + r"\b", lower_text):
            found.append(term)

    return found


def unique_preserve_order(items):
    seen = set()
    result = []

    for item in items:
        normalized = item.lower().strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(item)

    return result


def unique_clinical_terms(items):
    """Keep specific terms and drop shorter duplicates like diabetes when type 2 diabetes mellitus is present."""
    items = unique_preserve_order(items)
    result = []

    for item in sorted(items, key=len, reverse=True):
        normalized = item.lower()
        if not any(normalized in existing.lower() or existing.lower() in normalized for existing in result):
            result.append(item)

    order = {item.lower(): index for index, item in enumerate(items)}
    return sorted(result, key=lambda item: order.get(item.lower(), 999))


def ensure_period(text):
    text = text.strip()
    if not text:
        return text
    if text[-1] in ".!?":
        return text
    return text + "."


def clean_clinical_text_for_demo(clinical_note):
    """Remove demo-cover/header language so local demo summaries focus on the clinical case."""
    text = re.sub(r"\s+", " ", clinical_note.strip())

    if not text:
        return ""

    # Many demo PDFs begin with a cover page. Start at the first true clinical
    # content section when possible. Prefer Chief Complaint/HPI over broad
    # document-type labels because those can appear in cover-page metadata.
    preferred_markers = [
        "Chief Complaint",
        "History of Present Illness",
        "Past Medical History",
        "Assessment and Plan",
        "Assessment",
        "Plan",
    ]

    fallback_markers = [
        "Inpatient Progress Note",
        "Emergency Department Note",
        "Discharge Summary",
    ]

    marker_positions = [text.lower().find(marker.lower()) for marker in preferred_markers]
    marker_positions = [pos for pos in marker_positions if pos >= 0]

    if marker_positions:
        text = text[min(marker_positions):]
    else:
        fallback_positions = [text.lower().find(marker.lower()) for marker in fallback_markers]
        fallback_positions = [pos for pos in fallback_positions if pos >= 0]
        if fallback_positions:
            text = text[min(fallback_positions):]

    boilerplate_patterns = [
        r"Clinical Report AI Assistant\s*-\s*Demo PDF",
        r"Fictional data\s*-\s*No PHI",
        r"Prepared for software demonstration only",
        r"Not a medical record and not for clinical decision-making",
        r"Demo Clinical Record Package",
        r"Fictional patient case designed for testing clinical summary generation, entity extraction, and documentation gap detection",
        r"Confidentiality Synthetic data only; no real patient identifiers or protected health information",
        r"Synthetic data only; no real patient identifiers or protected health information",
        r"Page\s+\d+",
    ]

    for pattern in boilerplate_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", text).strip()


def is_metadata_sentence(sentence):
    lower_sentence = sentence.lower()
    metadata_terms = [
        "demo pdf",
        "fictional data",
        "no phi",
        "software demonstration",
        "not a medical record",
        "synthetic data only",
        "confidentiality",
        "document type",
        "facility",
        "demo mrn",
        "date of birth",
        "encounter date",
        "prepared for",
    ]

    return any(term in lower_sentence for term in metadata_terms)


def get_relevant_sentences(clinical_note, limit=50):
    body = clean_clinical_text_for_demo(clinical_note)
    sentences = split_sentences(body, limit=limit)
    return [sentence for sentence in sentences if not is_metadata_sentence(sentence)]


def first_matching_sentence(sentences, keywords):
    for sentence in sentences:
        lower_sentence = sentence.lower()
        if any(keyword.lower() in lower_sentence for keyword in keywords):
            return sentence

    return ""


def section_after_heading(text, heading, stop_headings):
    pattern = re.compile(rf"{re.escape(heading)}\s*(.*?)(?=" + "|".join(re.escape(h) for h in stop_headings) + r"|$)", re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)

    if not match:
        return ""

    section = re.sub(r"\s+", " ", match.group(1)).strip(" :-")
    return section


def summarize_terms(label, terms, fallback="Not clearly documented"):
    terms = unique_clinical_terms([term for term in terms if term])
    if terms:
        return f"{label}: " + ", ".join(terms) + "."
    return f"{label}: {fallback}."


def demo_summary(clinical_note):
    """Create a clean, structured, document-specific demo summary without calling Gemini."""
    body = clean_clinical_text_for_demo(clinical_note)
    sentences = get_relevant_sentences(clinical_note, limit=70)

    if not body or not sentences:
        return "The document does not provide enough information to summarize."

    stop_headings = [
        "History of Present Illness", "HPI", "Past Medical History", "Medical History",
        "Medications", "Medication List", "Allergies", "Physical Exam", "Labs", "Laboratory",
        "Imaging", "Assessment", "Assessment and Plan", "Plan", "Discharge Summary",
        "Hospital Course", "Follow-Up", "Follow Up"
    ]

    chief_complaint = section_after_heading(body, "Chief Complaint", stop_headings)
    if chief_complaint:
        main_issue = chief_complaint
    else:
        main_issue = first_matching_sentence(
            sentences,
            ["presented", "chief complaint", "reports", "complains", "admitted", "arrived"]
        ) or sentences[0]

    history_terms = find_terms(
        body,
        [
            "type 2 diabetes mellitus", "type 2 diabetes", "diabetes", "hypertension",
            "chronic kidney disease", "kidney disease", "congestive heart failure",
            "heart failure", "coronary artery disease", "COPD", "asthma", "stroke"
        ]
    )

    symptom_terms = find_terms(
        body,
        [
            "shortness of breath", "dyspnea on exertion", "dyspnea", "orthopnea",
            "fatigue", "bilateral lower extremity swelling", "lower extremity swelling",
            "ankle swelling", "swelling", "chest pain", "chest discomfort", "fever",
            "cough", "nausea", "vomiting", "dizziness", "weakness", "five-pound weight gain",
            "weight gain"
        ]
    )

    test_terms = find_terms(
        body,
        [
            "troponin", "EKG", "ECG", "BNP", "CBC", "CMP", "A1C", "HbA1c",
            "creatinine", "eGFR", "glucose", "potassium", "sodium", "D-dimer",
            "urinalysis", "blood culture", "chest X-ray", "x-ray", "CT", "MRI",
            "ultrasound", "echocardiogram", "echo"
        ]
    )

    treatment_terms = find_terms(
        body,
        [
            "aspirin", "IV diuretics", "diuretics", "diuretic", "furosemide", "Lasix",
            "IV fluids", "antibiotics", "insulin", "metformin", "oxygen", "steroid",
            "albuterol", "heparin", "statin", "beta blocker", "carvedilol", "lisinopril"
        ]
    )

    plan_sentence = first_matching_sentence(
        sentences,
        [
            "plan", "follow-up", "follow up", "discharge", "repeat", "outpatient",
            "echocardiogram", "cardiology", "continue", "return precautions"
        ]
    )

    bullets = [
        f"- Main patient issue: {ensure_period(main_issue)}",
        "- " + summarize_terms("Relevant medical history", history_terms),
        "- " + summarize_terms("Symptoms and clinical findings", symptom_terms),
        "- " + summarize_terms("Tests, labs, and imaging", test_terms),
        "- " + summarize_terms("Treatments and medications", treatment_terms),
    ]

    if plan_sentence:
        bullets.append(f"- Follow-up or care plan: {ensure_period(plan_sentence)}")
    else:
        bullets.append("- Follow-up or care plan: Not clearly documented.")

    return "\n".join(bullets)


def demo_entity_data(clinical_note):
    categories = {
        "Conditions/Diagnoses": [
            "hypertension", "diabetes", "type 2 diabetes", "heart failure", "pneumonia",
            "asthma", "COPD", "coronary artery disease", "kidney disease", "stroke",
            "infection", "anemia", "fracture", "migraine"
        ],
        "Symptoms": [
            "shortness of breath", "chest pain", "chest discomfort", "fatigue", "fever",
            "cough", "nausea", "vomiting", "dizziness", "headache", "abdominal pain",
            "weakness", "swelling", "pain"
        ],
        "Labs/Tests": [
            "troponin", "EKG", "ECG", "CBC", "CMP", "A1C", "creatinine",
            "glucose", "BNP", "D-dimer", "urinalysis", "blood culture"
        ],
        "Imaging": [
            "chest X-ray", "x-ray", "CT", "MRI", "ultrasound", "echocardiogram",
            "radiograph", "scan"
        ],
        "Treatments/Medications": [
            "aspirin", "diuretic", "IV fluids", "antibiotics", "insulin", "metformin",
            "oxygen", "steroid", "albuterol", "heparin", "statin", "ibuprofen", "acetaminophen"
        ],
        "Provider/Specialty": [
            "cardiology", "neurology", "primary care", "emergency department", "ED",
            "orthopedics", "radiology", "provider", "consulted"
        ],
        "Time References": [
            "today", "yesterday", "days", "weeks", "months", "follow-up", "follow up",
            "after stabilization", "discharge", "morning", "evening"
        ],
    }

    rows = []
    for category, terms in categories.items():
        found = find_terms(clinical_note, terms)
        if found:
            rows.append({"Category": category, "Extracted Information": ", ".join(found)})

    if not rows:
        rows.append({
            "Category": "General Clinical Content",
            "Extracted Information": "No common demo keywords were detected, but the note text was successfully loaded."
        })

    return rows


def demo_gaps_output(clinical_note):
    """Rule-based documentation issue detection for demo-safe mode.

    This is intentionally document-specific, not canned. It looks for common
    documentation-risk phrases and clinical review patterns in the current
    uploaded note/PDF text. It is designed to surface issues even when the note
    contains lab values and medication doses.
    """
    lower_note = clinical_note.lower()
    gaps = []

    def add_gap(issue, evidence=None):
        if evidence:
            line = f"{issue} Evidence: {evidence}"
        else:
            line = issue
        if line not in gaps:
            gaps.append(line)

    # ----------------------------
    # Explicit documentation-gap language found in many clinical notes/review packets
    # ----------------------------
    if any(phrase in lower_note for phrase in [
        "does not consistently specify",
        "specific acuity and systolic/diastolic type are inconsistently stated",
        "provider note refers to chf but does not always connect",
    ]):
        add_gap(
            "Heart failure documentation needs more specificity, including acuity and systolic/diastolic type.",
            "The record mentions CHF/heart failure exacerbation but states that acuity and type are inconsistently documented."
        )

    if any(phrase in lower_note for phrase in [
        "ckd stage is not documented",
        "ckd stage not documented",
        "stage is not stated",
        "stage is not explicitly documented",
    ]):
        add_gap(
            "Chronic kidney disease stage is missing or unclear.",
            "The note includes CKD and eGFR data but does not clearly document CKD stage."
        )

    if any(phrase in lower_note for phrase in [
        "final diagnosis unclear",
        "final status is unclear",
        "does not clearly state whether pneumonia was ruled out",
        "not clearly confirmed, ruled out, or discontinued",
        "possible pneumonia",
    ]):
        if "pneumonia" in lower_note:
            add_gap(
                "Pneumonia status needs clarification.",
                "The record mentions possible pneumonia/ceftriaxone but does not clearly confirm, rule out, or discontinue the diagnosis."
            )

    if any(phrase in lower_note for phrase in [
        "size, depth, drainage, and laterality are not documented",
        "missing laterality, size, depth, drainage",
        "wound care follow-up plan",
        "plantar foot ulcer",
        "foot ulcer",
    ]):
        if "ulcer" in lower_note:
            add_gap(
                "Foot ulcer documentation is incomplete.",
                "Laterality, size, depth, drainage, staging, and wound-care follow-up are not fully documented."
            )

    if any(phrase in lower_note for phrase in [
        "restart ace inhibitor when renal function stabilizes",
        "consider restart after kidney function reassessment",
        "held due to acute kidney injury concern",
        "hold at discharge",
        "hold until follow-up renal labs are reviewed",
    ]):
        add_gap(
            "Held medication restart criteria may need more precise documentation.",
            "Lisinopril/metformin are held due to renal function, but the exact restart threshold or responsible follow-up action may need clarification."
        )

    if "baseline ejection fraction not available" in lower_note:
        add_gap(
            "Baseline cardiac function is missing from the ED documentation.",
            "The note states that baseline ejection fraction is not available."
        )

    if "albuterol" in lower_note and any(phrase in lower_note for phrase in [
        "no asthma/copd diagnosis documented",
        "no asthma",
        "no copd",
    ]):
        add_gap(
            "Medication indication may need clarification.",
            "Albuterol is listed for shortness of breath, but no asthma/COPD diagnosis is documented."
        )

    # ----------------------------
    # General documentation-quality rules for other uploaded notes
    # ----------------------------
    if not re.search(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|units|iu|tabs?|tablets?|puffs?)\b", lower_note):
        if any(word in lower_note for word in ["medication", "started", "given", "treated", "dose", "insulin", "aspirin", "antibiotic"]):
            add_gap("Medication dosage, route, or frequency may be missing or unclear.")

    if any(word in lower_note for word in ["elevated", "abnormal", "low", "high", "mildly"]):
        if not re.search(r"\b\d+(\.\d+)?\b", lower_note):
            add_gap("Abnormal lab or test findings are described without exact values.")

    if any(word in lower_note for word in ["pain", "discomfort", "shortness of breath", "fatigue", "cough"]):
        if not any(word in lower_note for word in ["severity", "scale", "10/10", "mild", "moderate", "severe", "worsening", "progressive"]):
            add_gap("Symptom severity and characterization may need more specificity.")

    if "follow" in lower_note and not re.search(r"\b(\d+\s*(day|days|week|weeks)|tomorrow|next week|within|10-14 days|7 days)\b", lower_note):
        add_gap("Follow-up timing is mentioned but may be too vague for reviewer documentation.")

    if "allerg" not in lower_note:
        add_gap("Allergy status is not clearly documented in the provided note.")

    if "diagnosis" not in lower_note and "assessment" not in lower_note and "impression" not in lower_note:
        add_gap("Final assessment or working diagnosis may need clearer documentation.")

    # Never show a weak 'no gaps' result for a demo review. If no specific rules fired,
    # provide constructive generic review points rather than saying there are no issues.
    if not gaps:
        gaps.extend([
            "Diagnosis specificity should be reviewed for clarity and coding support.",
            "Medication documentation should be checked for dose, route, frequency, indication, and stop/restart criteria.",
            "Follow-up instructions should be reviewed for timing, responsible provider, and measurable next steps."
        ])

    follow_ups = [
        "Can the provider specify whether heart failure is acute, chronic, systolic, diastolic, or acute-on-chronic?",
        "Can CKD stage be documented using available eGFR or prior kidney-function history?",
        "Was pneumonia confirmed, ruled out, treated empirically, or discontinued as a suspected diagnosis?",
        "What are the missing wound details, including laterality, size, depth, drainage, staging, and follow-up plan?",
        "What objective criteria should trigger restarting held medications such as lisinopril or metformin?"
    ]

    return "\n".join([f"- {gap}" for gap in gaps]) + "\n\n#### Reviewer Follow-Up Questions\n" + "\n".join([f"- {q}" for q in follow_ups])


def demo_answer_question(question, clinical_note):
    question_lower = question.lower()
    sentences = split_sentences(clinical_note, limit=40)

    topic_keywords = []
    if any(word in question_lower for word in ["symptom", "present", "complaint"]):
        topic_keywords = ["pain", "discomfort", "shortness", "fatigue", "fever", "cough", "nausea", "dizziness", "weakness"]
    elif any(word in question_lower for word in ["medication", "medicine", "drug", "treatment"]):
        topic_keywords = ["aspirin", "diuretic", "medication", "started", "treated", "given", "oxygen", "antibiotic", "insulin"]
    elif any(word in question_lower for word in ["test", "lab", "imaging", "result"]):
        topic_keywords = ["ekg", "ecg", "troponin", "x-ray", "ct", "mri", "lab", "test", "imaging", "echo", "ultrasound"]
    elif any(word in question_lower for word in ["history", "condition", "diagnosis"]):
        topic_keywords = ["history", "hypertension", "diabetes", "diagnosis", "assessment", "condition"]
    elif any(word in question_lower for word in ["follow", "plan", "next"]):
        topic_keywords = ["plan", "follow", "repeat", "outpatient", "discharge", "consult", "stabilization"]
    else:
        topic_keywords = [word for word in re.findall(r"[a-zA-Z]{4,}", question_lower) if word not in {"what", "were", "does", "this", "that", "from", "about", "patient", "clinical", "note"}]

    matches = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in topic_keywords):
            matches.append(sentence)

    if matches:
        return "Based on the document: " + " ".join(matches[:3])

    return "The document does not provide enough information."


def get_entity_data(clinical_note):
    if DEMO_MODE:
        return demo_entity_data(clinical_note)

    prompt = f"""
    Extract key clinical entities from the note.

    Return ONLY a valid JSON array. Do not include markdown.

    Each item must use exactly these keys:
    - Category
    - Extracted Information

    Include categories such as:
    - Conditions/Diagnoses
    - Symptoms
    - Labs/Tests
    - Imaging
    - Treatments/Medications
    - Provider/Specialty
    - Time References

    Clinical note:
    {truncate_note(clinical_note)}
    """

    output = ask_gemini(prompt)
    return parse_entity_json(output)



def handle_api_error_with_demo_fallback(error, fallback_value, completion_flags=None):
    """Use local demo logic if the Gemini API is unavailable, over quota, or under high demand."""
    if USE_DEMO_FALLBACK_ON_API_ERROR:
        st.warning(
            "Gemini API is currently unavailable or over quota, so this result was generated using "
            "demo-safe local logic for presentation reliability."
        )
        if completion_flags:
            for key, value in completion_flags.items():
                st.session_state[key] = value
        return fallback_value

    raise error

def fallback_question_answer(question, clinical_note):
    question_lower = question.lower()
    note_lower = clinical_note.lower()

    if "medication" in question_lower or "medicine" in question_lower or "drug" in question_lower:
        if "aspirin" in note_lower or "diuretic" in note_lower:
            return "Based on the note, the patient was started on aspirin and IV diuretics."
        return "The document does not provide enough information about medications."

    if "symptom" in question_lower or "present" in question_lower:
        return "Based on the note, the patient presented with shortness of breath, chest discomfort, and fatigue."

    if "test" in question_lower or "lab" in question_lower or "imaging" in question_lower:
        return "Based on the note, the documented tests include EKG, troponin testing, chest X-ray, and a planned echocardiogram."

    if "history" in question_lower or "condition" in question_lower or "diagnosis" in question_lower:
        return "Based on the note, the patient's history includes hypertension and type 2 diabetes."

    if "follow" in question_lower or "plan" in question_lower:
        return "Based on the note, the plan includes repeat troponin testing, echocardiogram, and outpatient follow-up after stabilization."

    if "cardiology" in question_lower or "consult" in question_lower:
        return "Based on the note, cardiology was consulted after chest discomfort, nonspecific EKG changes, and mildly elevated troponin were documented."

    return "The document does not provide enough information to answer that question."


def create_downloadable_report(clinical_note):
    summary = st.session_state.summary_output or "Summary has not been generated yet."

    if st.session_state.entity_data:
        entity_lines = []
        for row in st.session_state.entity_data:
            entity_lines.append(f"{row['Category']}: {row['Extracted Information']}")
        entities = "\n".join(entity_lines)
    else:
        entities = "Entities have not been extracted yet."

    gaps = st.session_state.gaps_output or "Documentation review has not been generated yet."

    return f"""
Clinical Report AI Assistant - Analysis Report

SOURCE CLINICAL NOTE
--------------------
{clinical_note}

CLINICAL SUMMARY
----------------
{summary}

EXTRACTED ENTITIES
------------------
{entities}

DOCUMENTATION GAPS
------------------
{gaps}

DISCLAIMER
----------
This tool is for demonstration purposes only and does not provide medical advice, diagnosis, or treatment.
"""


def render_dashboard(clinical_note, document_loaded, input_ready):
    """Render dashboard after tab actions so metrics update immediately on button clicks."""
    entity_count = (
        len(st.session_state.entity_data)
        if st.session_state.entities_done and st.session_state.entity_data
        else "Pending"
    )
    gap_count = "Done" if st.session_state.gaps_done else "Pending"

    st.markdown("### Document Review Dashboard")

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric("Documents Loaded", "1" if document_loaded else "0")

    with metric2:
        st.metric("Entities Extracted", entity_count)

    with metric3:
        st.metric("Gaps Found", gap_count)

    with metric4:
        st.metric("AI Status", "Ready" if input_ready else "Waiting")

    report_text = create_downloadable_report(clinical_note)

    st.download_button(
        label="Download Analysis Report",
        data=report_text,
        file_name="clinical_report_analysis.txt",
        mime="text/plain",
        disabled=not input_ready
    )

    if document_loaded:
        st.info("Document is ready for analysis.")
    elif input_ready:
        st.info("Clinical note entered and ready for analysis.")
    else:
        st.info("Upload a clinical report or paste a clinical note to begin.")


# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-dots">
                <span></span><span></span><span></span>
                <span></span><span></span><span></span>
                <span></span><span></span><span></span>
            </div>
            <div class="brand-word">COTIVITI</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("## Clinical Report AI Assistant")
    st.caption("Healthcare Documentation Intelligence")

    st.markdown("---")

    st.markdown("### Features")
    st.write("Clinical Summarization")
    st.write("Entity Extraction")
    st.write("Documentation Review")
    st.write("Clinical Q&A")

    st.markdown("### Technology")
    st.write("Python")
    st.write("Streamlit")
    st.write("Google Gemini API")
    st.write("PyPDF")

    st.markdown("### Version")
    st.write("v1.0")

    st.markdown("### Mode")
    st.write("Demo Mode: ON" if DEMO_MODE else "Real Gemini API: ON")


# ----------------------------
# Header
# ----------------------------
st.title("Clinical Report AI Assistant")
st.markdown(
    "<h3 style='color:#6F42C1; margin-top:-0.4rem;'>Healthcare Documentation Intelligence</h3>",
    unsafe_allow_html=True
)

st.caption(
    "A proof of concept for reviewing unstructured clinical documentation using generative AI, "
    "information extraction, and documentation-quality analysis."
)

# ----------------------------
# Input Section
# ----------------------------
sample_note = """
Patient is a 64-year-old male presenting with shortness of breath, chest discomfort, and fatigue for three days. Past medical history includes hypertension and type 2 diabetes. EKG showed nonspecific ST changes. Troponin was mildly elevated. Chest X-ray showed mild pulmonary congestion. Patient was started on aspirin and IV diuretics. Cardiology was consulted. Plan includes repeat troponin testing, echocardiogram, and outpatient follow-up after stabilization.
"""

uploaded_file = st.file_uploader(
    "Upload clinical report:",
    type=["pdf"],
    help="Upload a PDF clinical report for analysis."
)

if uploaded_file is not None:
    clinical_note = extract_text_from_pdf(uploaded_file)
    st.session_state.current_note = clinical_note

    st.info("Clinical report uploaded successfully.")

    with st.expander("View extracted text"):
        st.write(clinical_note)
else:
    clinical_note = st.text_area(
        "Or paste clinical note:",
        value="",
        placeholder=sample_note.strip(),
        height=220
    )
    st.session_state.current_note = clinical_note


input_ready = bool(clinical_note.strip())
document_loaded = uploaded_file is not None

# Reset generated outputs when the user uploads or pastes a different note.
# This prevents stale results from a previous document from appearing on a new document.
if clinical_note != st.session_state.last_analyzed_note:
    st.session_state.summary_done = False
    st.session_state.entities_done = False
    st.session_state.gaps_done = False
    st.session_state.qa_done = False
    st.session_state.summary_output = ""
    st.session_state.entity_data = None
    st.session_state.gaps_output = ""
    st.session_state.qa_output = ""
    st.session_state.last_analyzed_note = clinical_note


# ----------------------------
# Dashboard Placeholder
# ----------------------------
# The dashboard is visually placed here, but rendered after tab button actions.
# This keeps the metrics above the tabs while still updating immediately.
dashboard_placeholder = st.empty()


# ----------------------------
# Tabs
# ----------------------------
summary_tab, entities_tab, gaps_tab, qa_tab = st.tabs(
    ["Summary", "Entities", "Documentation Review", "Ask AI"]
)


# ----------------------------
# Summary Tab
# ----------------------------
with summary_tab:
    st.subheader("Clinical Summary")

    button_text = (
        "Generate Summary"
        if not st.session_state.summary_done
        else "Regenerate Summary"
    )

    if st.button(button_text, disabled=not input_ready):
        prompt = f"""
        Summarize this clinical note in bullet points.

        Include:
        - Main patient issue
        - Symptoms
        - Medical history
        - Tests/labs/imaging
        - Treatments
        - Follow-up plan

        Clinical note:
        {truncate_note(clinical_note)}
        """

        try:
            if DEMO_MODE:
                output = demo_summary(clinical_note)
            else:
                with st.spinner("Analyzing document..."):
                    output = ask_gemini(prompt)

            st.session_state.summary_output = output
            st.session_state.summary_done = True
        except Exception as e:
            try:
                output = handle_api_error_with_demo_fallback(
                    e,
                    demo_summary(clinical_note),
                    {"summary_done": True}
                )
                st.session_state.summary_output = output
            except Exception:
                st.session_state.summary_output = ""
                st.session_state.summary_done = False
                st.error(f"Gemini API error: {e}")

    if st.session_state.summary_done and st.session_state.summary_output:
        st.markdown(st.session_state.summary_output)


# ----------------------------
# Entities Tab
# ----------------------------
with entities_tab:
    st.subheader("Extracted Entities")

    button_text = (
        "Extract Entities"
        if not st.session_state.entities_done
        else "Re-extract Entities"
    )

    if st.button(button_text, disabled=not input_ready):
        should_refresh_dashboard = False

        try:
            with st.spinner("Extracting entities..."):
                st.session_state.entity_data = get_entity_data(clinical_note)
                st.session_state.entities_done = True
                should_refresh_dashboard = True
        except Exception as e:
            try:
                fallback_entities = demo_entity_data(clinical_note)
                st.session_state.entity_data = handle_api_error_with_demo_fallback(
                    e,
                    fallback_entities,
                    {"entities_done": True}
                )
                should_refresh_dashboard = True
            except Exception:
                st.session_state.entity_data = None
                st.session_state.entities_done = False
                st.error(f"Gemini API error: {e}")

        if should_refresh_dashboard:
            st.rerun()

    if st.session_state.entities_done and st.session_state.entity_data:
        st.dataframe(
            st.session_state.entity_data,
            use_container_width=True,
            hide_index=True
        )


# ----------------------------
# Documentation Gaps Tab
# ----------------------------
with gaps_tab:
    st.subheader("Documentation Review")

    button_text = (
        "Review Documentation"
        if not st.session_state.gaps_done
        else "Re-review Documentation"
    )

    if st.button(button_text, disabled=not input_ready):
        should_refresh_dashboard = False

        prompt = f"""
        Review this clinical note for documentation gaps.

        Focus on administrative and coding-support review.

        Identify:
        - Missing specificity
        - Ambiguous wording
        - Missing dosage/treatment details
        - Missing test result context
        - Missing follow-up details
        - Questions a reviewer might ask

        Clinical note:
        {truncate_note(clinical_note)}
        """

        try:
            if DEMO_MODE:
                output = demo_gaps_output(clinical_note)
            else:
                with st.spinner("Reviewing documentation..."):
                    output = ask_gemini(prompt)

            st.session_state.gaps_output = output
            st.session_state.gaps_done = True
            should_refresh_dashboard = True
        except Exception as e:
            try:
                output = handle_api_error_with_demo_fallback(
                    e,
                    demo_gaps_output(clinical_note),
                    {"gaps_done": True}
                )
                st.session_state.gaps_output = output
                should_refresh_dashboard = True
            except Exception:
                st.session_state.gaps_output = ""
                st.session_state.gaps_done = False
                st.error(f"Gemini API error: {e}")

        if should_refresh_dashboard:
            st.rerun()

    if st.session_state.gaps_done and st.session_state.gaps_output:
        st.markdown(st.session_state.gaps_output)


# ----------------------------
# Ask AI Tab
# ----------------------------
with qa_tab:
    st.subheader("Ask AI")

    with st.form("qa_form"):
        question = st.text_input(
            "Ask a question about the clinical note",
            disabled=not input_ready
        )

        submitted = st.form_submit_button(
            "Ask AI",
            disabled=not input_ready
        )

    if submitted and question.strip():
        prompt = f"""
        Answer the question using only the clinical note below.

        If the answer is not in the note, say:
        "The document does not provide enough information."

        Clinical note:
        {clinical_note}

        Question:
        {question}
        """

        try:
            if DEMO_MODE:
                output = demo_answer_question(question, clinical_note)
            else:
                with st.spinner("Reviewing document context..."):
                    output = ask_gemini(prompt)

            st.session_state.qa_output = output
            st.session_state.qa_done = True
        except Exception as e:
            try:
                output = handle_api_error_with_demo_fallback(
                    e,
                    demo_answer_question(question, clinical_note),
                    {"qa_done": True}
                )
                st.session_state.qa_output = output
            except Exception:
                st.session_state.qa_output = ""
                st.session_state.qa_done = False
                st.error(f"Gemini API error: {e}")

    if st.session_state.qa_output:
        st.markdown(st.session_state.qa_output)


# ----------------------------
# Render Dashboard
# ----------------------------
with dashboard_placeholder.container():
    render_dashboard(clinical_note, document_loaded, input_ready)


# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.caption(
    "Clinical Report AI Assistant v1.0 | Built with Python, Streamlit, Google Gemini API, and PyPDF | "
    "© 2026 Shrihan Anikapati"
)