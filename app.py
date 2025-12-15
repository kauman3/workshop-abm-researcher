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
    st.info("**How it works:**\n\n1. Searches live web for news, tech stack, and leadership changes\n2. Identifies internal comms pain points\n3. Generates formatted PDF one-pager")
    
    st.divider()
    st.caption("v2.0 - Clean Minimal Template")

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
            status_box.write("🕵️ Searching live web data (news, hiring, tech stack)...")
            
            # Get structured data from research agent
            structured_data = get_company_data(company_name, website)
            
            status_box.write("🧠 Synthesizing insights into BDR format...")
            status_box.write("📄 Generating PDF with Workshop branding...")
            
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
            with col2:
                st.markdown(f"**Size:** {snapshot.get('size', 'N/A')}")
                st.markdown(f"**Footprint:** {snapshot.get('footprint', 'N/A')}")
            
            if snapshot.get('tech_stack'):
                st.markdown("**Current Tech Stack:**")
                st.markdown(" • ".join(snapshot['tech_stack']))
            
            if snapshot.get('change_events'):
                st.markdown("**Recent Changes:**")
                for event in snapshot['change_events']:
                    st.markdown(f"- {event}")
        
        # Section 2: Why Now
        with st.expander("⚡ Why Now", expanded=True):
            why_now = data.get('why_now', [])
            for item in why_now:
                st.markdown(f"**{item.get('title', '')}:** {item.get('description', '')}")
        
        # Section 3: Personas
        with st.expander("👥 Key Personas", expanded=True):
            personas = data.get('personas', [])
            for persona in personas:
                st.markdown(f"**{persona.get('title', '')}**")
                st.markdown("*Goals:*")
                for goal in persona.get('goals', []):
                    st.markdown(f"- {goal}")
                st.markdown("*Fears:*")
                for fear in persona.get('fears', []):
                    st.markdown(f"- {fear}")
                st.markdown("---")
        
        # Section 4: Angles
        with st.expander("🎯 Recommended Angles", expanded=True):
            angles = data.get('angles', [])
            for angle in angles:
                st.markdown(f"**{angle.get('title', '')}**")
                st.markdown(angle.get('description', ''))
                st.info(f"📊 Key metric: {angle.get('metric', 'N/A')}")
                st.markdown("")
            
            # Proof point
            if 'proof_point' in data and data['proof_point']:
                proof = data['proof_point']
                st.markdown("**Social Proof:**")
                st.markdown(f"*{proof.get('company', '')}* ({proof.get('context', '')})")
                st.markdown(f'> "{proof.get("quote", "")}"')
    
    with tab2:
        st.subheader("Raw Structured Data")
        st.json(data)
        
        # Data quality checks
        st.subheader("Quality Checks")
        checks = {
            "Has snapshot data": bool(data.get('snapshot')),
            "Has why_now reasons": len(data.get('why_now', [])) > 0,
            "Has personas": len(data.get('personas', [])) > 0,
            "Has angles": len(data.get('angles', [])) > 0,
            "Has tech stack": len(data.get('snapshot', {}).get('tech_stack', [])) > 0,
            "Has change events": len(data.get('snapshot', {}).get('change_events', [])) > 0
        }
        
        for check, passed in checks.items():
            if passed:
                st.success(f"✓ {check}")
            else:
                st.warning(f"⚠ {check}")
    
    with tab3:
        st.subheader("📥 Export Options")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **Ready to share with your BDR team:**
            - Professional Workshop branding
            - Optimized for quick scanning
            - Print-ready (8.5" x 11")
            """)
        
        with col2:
            # Generate PDF
            try:
                pdf_data = create_styled_pdf(data, company)
                
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name=f"Workshop_ABM_{company.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
                st.success("✅ PDF ready!")
                
            except Exception as e:
                st.error(f"PDF generation failed: {str(e)}")
                st.exception(e)
        
        st.divider()
        
        # JSON export option
        st.subheader("💾 Export Raw Data")
        json_str = json.dumps(data, indent=2)
        st.download_button(
            label="📊 Download JSON",
            data=json_str,
            file_name=f"Workshop_ABM_{company.replace(' ', '_')}.json",
            mime="application/json"
        )

# FOOTER
st.divider()
st.caption("Built by Workshop AI Operations Team • For internal BDR enablement use only")
