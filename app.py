import streamlit as st
import os
from research_agent import get_company_data
from pdf_generator import create_styled_pdf

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Workshop ABM Generator", 
    page_icon="🚀",
    layout="centered"
)

# 2. HEADER & STYLE
# We inject some custom CSS to make it look branded (Workshop uses purple/pink)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
    .report-box {
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Account-Based One-Pager")
st.markdown("Generate a hyper-personalized BDR asset in seconds.")

# 3. SIDEBAR (API Status)
with st.sidebar:
    st.header("System Status")
    if os.environ.get("TAVILY_API_KEY"):
        st.success("Tavily Search: Active")
    else:
        st.error("Tavily Key Missing")
        
    if os.environ.get("ANTHROPIC_API_KEY"):
        st.success("Anthropic AI: Active")
    else:
        st.error("Anthropic Key Missing")
    
    st.info("This tool scans live news, tech stacks, and leadership changes to build a custom outreach strategy.")

# 4. INPUTS
col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input("Target Company", placeholder="e.g. Spotify")
with col2:
    website = st.text_input("Website URL", placeholder="e.g. spotify.com")

# 5. EXECUTION LOGIC
if st.button("Generate Strategy"):
    if not company_name or not website:
        st.warning("Please provide both a company name and website.")
    else:
        # Create a status container to show "Thinking" process
        status_box = st.status("Initializing Agent...", expanded=True)
        
        try:
            status_box.write("🕵️‍♂️ Searching live web data (News, Hiring, Tech Stack)...")
            # We call the function we wrote in Step 2
            report_markdown = get_company_data(company_name, website)
            
            status_box.write("🧠 Synthesizing insights into BDR format...")
            status_box.update(label="Analysis Complete!", state="complete", expanded=False)
            
            # Store in session state so it doesn't vanish
            st.session_state['report'] = report_markdown
            st.session_state['company_name'] = company_name
            
        except Exception as e:
            status_box.update(label="Error Occurred", state="error")
            st.error(f"Failed to generate report: {str(e)}")

# 6. DISPLAY RESULTS
if 'report' in st.session_state:
    st.divider()

    # --- PREVIEW SECTION ---
    st.subheader(f"Strategy for {st.session_state['company_name']}")

    # Tabs for better UX: View the Raw Text or Preview the Formatting
    tab1, tab2 = st.tabs(["📄 Read Report", "⚙️ System Logic"])

    with tab1:
        st.markdown(st.session_state['report'])

    with tab2:
        st.text("Context provided to LLM:")
        # If you want to show the raw JSON or context for the "Engineering" demo
        st.json({"company": st.session_state['company_name'], "status": "Analyzed"})

    # --- EXPORT SECTION ---
    st.divider()
    st.subheader("BDR Enablement")
    col_dl, col_info = st.columns([1, 2])

    with col_dl:
        # Generate the PDF on the fly when the page reloads/renders
        pdf_data = create_styled_pdf(st.session_state['report'], st.session_state['company_name'])

        st.download_button(
            label="📥 Download PDF One-Pager",
            data=pdf_data,
            file_name=f"Workshop_Strategy_{st.session_state['company_name']}.pdf",
            mime="application/pdf",
            type="primary"
        )

    with col_info:
        st.caption("✅ Ready for distribution. Formatted with Workshop branding guidelines.")
