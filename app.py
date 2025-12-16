import streamlit as st
import os
import json
from research_agent import get_company_data
from pdf_generator import create_styled_pdf

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Workshop ABM Generator", 
    page_icon="🚀",
    layout="centered"
)

# CUSTOM STYLING
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #2D5BFF;
        color: white;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #1E40AF;
    }
    .section-card {
        border: 1px solid #e5e7eb;
        padding: 20px;
        border-radius: 10px;
        background-color: #f9fafb;
        margin-bottom: 15px;
    }
    .metric-box {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2D5BFF;
    }
    </style>
""", unsafe_allow_html=True)

# HELPER FOR RICH OBJECTS
def get_clean_val(data, default="Unknown"):
    """Extracts string value from potential {value, url} object"""
    if isinstance(data, dict):
        return data.get('value', default)
    return str(data) if data else default

st.title("🚀 Workshop ABM One-Pager Generator")
st.markdown("Generate hyper-personalized BDR assets powered by live research + AI")

# SIDEBAR
with st.sidebar:
    st.header("🔧 System Status")
    if os.environ.get("TAVILY_API_KEY"):
        st.success("✓ Tavily Search Active")
    else:
        st.error("✗ Tavily Key Missing")
        
    if os.environ.get("ANTHROPIC_API_KEY"):
        st.success("✓ Claude AI Active")
    else:
        st.error("✗ Anthropic Key Missing")
    
    st.divider()
    st.info("**How it works:**\n\n1. Deep searches for Fiscal Year, Tech Stack, & Strategic Shifts\n2. Finds Internal Comms leaders & Verified Emails\n3. Generates clickable PDF with Source Links")
    
    st.divider()
    st.caption("v2.1 - Targeted BDR Edition")

# INPUTS
col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input("🏢 Target Company", placeholder="e.g., Nebraska Medicine")
with col2:
    website = st.text_input("🌐 Website URL", placeholder="e.g., nebraskamed.com")

# GENERATE BUTTON
if st.button("🔍 Generate Strategy", type="primary"):
    if not company_name or not website:
        st.warning("⚠️ Please provide both company name and website URL")
    else:
        status_box = st.status("Initializing research agent...", expanded=True)
        
        try:
            status_box.write("🕵️ Hunting for strategic initiatives & fiscal data...")
            
            # Get structured data from research agent
            structured_data = get_company_data(company_name, website)
            
            status_box.write("👤 Verifying internal comms decision makers...")
            status_box.write("🧠 Synthesizing 'Why Now' hooks...")
            status_box.write("📄 Rendering interactive PDF...")
            
            # Store in session state
            st.session_state['structured_data'] = structured_data
            st.session_state['company_name'] = company_name
            
            status_box.update(label="✅ Analysis Complete!", state="complete", expanded=False)
            
        except Exception as e:
            status_box.update(label="❌ Error Occurred", state="error")
            st.error(f"Failed to generate report: {str(e)}")
            st.exception(e)

# DISPLAY RESULTS
if 'structured_data' in st.session_state:
    st.divider()
    data = st.session_state['structured_data']
    company = st.session_state['company_name']
    
    st.subheader(f"📊 Strategy Preview: {company}")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📄 Preview", "🔍 Data Inspection", "📥 Export"])
    
    with tab1:
        # Section 1: Snapshot
        with st.expander("🏢 Company Snapshot", expanded=True):
            snapshot = data.get('snapshot', {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Industry:** {snapshot.get('industry', 'N/A')}")
                st.markdown(f"**Location:** {snapshot.get('location', 'N/A')}")
                # Handle Rich Objects
                st.markdown(f"**Fiscal Year:** {get_clean_val(snapshot.get('fiscal_year'))}")
            with col2:
                st.markdown(f"**Size:** {snapshot.get('size', 'N/A')}")
                st.markdown(f"**Glassdoor:** {get_clean_val(snapshot.get('glassdoor_score'))}")
            
            if snapshot.get('tech_stack'):
                st.markdown("**Tech Stack:**")
                # Extract tool names from list of dicts
                tools = []
                for item in snapshot['tech_stack']:
                    if isinstance(item, dict):
                        tools.append(item.get('tool', ''))
                    else:
                        tools.append(str(item))
                st.markdown(" • ".join(tools))
        
        # Section 2: Call Scripts (NEW)
        with st.expander("⚡ Call Scripts (Openers)", expanded=True):
            openers = data.get('openers', [])
            for op in openers:
                st.markdown(f"**{op.get('label', 'Opener')}**")
                st.info(f'"{op.get("script", "")}"')

        # Section 3: Why Now
        with st.expander("🚀 Why Now (Strategic)", expanded=True):
            why_now = data.get('why_now', [])
            for item in why_now:
                title = item.get('title', 'Insight')
                desc = item.get('description', '')
                url = item.get('source_url')
                
                link_icon = "🔗" if url else ""
                st.markdown(f"**{title}** {link_icon}")
                st.markdown(desc)
                st.markdown("---")
        
        # Section 4: Personas
        with st.expander("👥 Key Decision Makers", expanded=True):
            personas = data.get('personas', [])
            for p in personas:
                name = p.get('name', 'Unknown')
                role = p.get('role', 'Role')
                is_verified = p.get('is_named_person', False)
                email = p.get('email', 'Unknown')
                
                header = f"**{name}** - *{role}*"
                if is_verified:
                    header += " ✅ (Verified)"
                
                st.markdown(header)
                if email and email != 'Unknown':
                    st.caption(f"📧 {email}")
                
                st.markdown("*Goals:* " + ", ".join(p.get('goals', [])[:2]))
                st.markdown("*Pains:* " + ", ".join(p.get('fears', [])[:2]))
                st.markdown("")
    
    with tab2:
        st.subheader("Raw Structured Data")
        st.json(data)
    
    with tab3:
        st.subheader("📥 Export Options")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **Ready to share with your BDR team:**
            - Professional Workshop branding
            - Clickable Source Links
            - Single Page Format
            """)
        
        with col2:
            # Generate PDF
            try:
                # Look for logo file in current directory or assets folder
                logo_path = None
                possible_paths = [
                    'workshop_logo.png',
                    'assets/workshop_logo.png',
                    'workshop_logo_full.png'
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        logo_path = path
                        break
                
                pdf_data = create_styled_pdf(data, company, logo_path=logo_path)
                
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name=f"Workshop_ABM_{company.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"PDF generation failed: {str(e)}")
                st.exception(e)

# FOOTER
st.divider()
st.caption("Built by Workshop AI Operations Team • Internal Use Only")
