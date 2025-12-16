from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from datetime import datetime
import base64
import os

# Import Workshop features matcher
try:
    from workshop_features import match_features_to_company
    FEATURES_AVAILABLE = True
except ImportError:
    FEATURES_AVAILABLE = False
    print("⚠️ workshop_features.py not found - feature matching disabled")

def create_styled_pdf(structured_data, company_name, logo_path=None):
    """
    Converts structured data into a branded Workshop PDF using WeasyPrint.
    """
    
    # Extract sections
    snapshot = structured_data.get('snapshot', {})
    why_now = structured_data.get('why_now', [])
    personas = structured_data.get('personas', [])
    angles = structured_data.get('angles', [])
    openers = structured_data.get('openers', [])
    metadata = structured_data.get('_metadata', {})
    
    # Create Source Map for Hyperlinking
    # Maps ID -> URL (e.g., {1: "https://nytimes.com/...", 2: "..."})
    source_map = {}
    if 'all_sources' in metadata:
        for idx, src in enumerate(metadata['all_sources'], 1):
            source_map[idx] = src.get('url', '#')

    # --- PREPARE ASSETS ---
    logo_img = ""
    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                logo_b64 = base64.b64encode(f.read()).decode()
            logo_img = f'<img src="data:image/png;base64,{logo_b64}" class="brand-logo"/>'
        except Exception:
            logo_img = '<div class="brand-text">Workshop</div>'
    else:
        logo_img = '<div class="brand-text">Workshop</div>'

    # --- HTML HELPERS ---
    
    def get_source_link(source_id, text):
        """Wraps text in an <a> tag if source_id exists in map"""
        if source_id and source_id in source_map:
            return f'<a href="{source_map[source_id]}" target="_blank" class="source-link">{text}</a>'
        return text

    def get_tech_ecosystem_html(stack):
        """Generates the Tech Zone with special Teams highlighting"""
        if not stack: return '<div class="empty-state">No tech data available</div>'
        
        # Check for Microsoft Teams (High Value Integration)
        stack_str = str(stack).lower()
        has_teams = "teams" in stack_str
        
        html = ""
        
        # 1. Integration Highlight
        if has_teams:
            html += """
            <div class="integration-highlight">
                <span class="highlight-icon">✓</span> 
                <strong>Microsoft Teams Ready</strong>
                <div class="highlight-sub">Workshop pushes directly to Teams channels</div>
            </div>
            """
            
        # 2. Tech Pills
        html += '<div class="tech-grid">'
        for item in stack[:8]: # Limit count
            tool = item.get("tool", item) if isinstance(item, dict) else item
            # Skip Teams in the grid if we already highlighted it
            if has_teams and "teams" in str(tool).lower():
                continue
            html += f'<span class="tech-pill">{tool}</span>'
        html += '</div>'
        
        return html

    def get_openers_html(openers_list):
        """Generates the Conversation Starters Zone"""
        if not openers_list: return '<div class="empty-state">No scripts generated</div>'
        html = ""
        for opener in openers_list[:2]:
            label = opener.get('label', 'Opener')
            script = opener.get('script', '')
            html += f"""
            <div class="opener-box">
                <div class="opener-label">{label}</div>
                <div class="opener-script">"{script}"</div>
            </div>
            """
        return html

    def get_solution_match_table():
        """Generates the Solution Match Table based on Pain Points"""
        if not FEATURES_AVAILABLE: return ""
        
        matches = match_features_to_company(structured_data)
        if not matches: return ""
        
        rows = ""
        for m in matches[:3]: # Top 3 matches
            # Format Pain Points (capitalize and join)
            pains = ", ".join([k.title() for k in m.get('matched_keywords', [])[:2]])
            if not pains: pains = "General Efficiency"
            
            # Use first feature bullet as Value Prop
            value_prop = m['features'][0] if m['features'] else "Streamline communications"
            
            rows += f"""
            <tr>
                <td class="col-pain"><strong>{pains}</strong></td>
                <td class="col-feature">{m['name']}</td>
                <td class="col-value">{value_prop}</td>
            </tr>
            """
            
        return f"""
        <div class="solution-section">
            <div class="section-title">🛠️ Workshop Solution Match</div>
            <table class="solution-table">
                <thead>
                    <tr>
                        <th width="25%">Detected Pain</th>
                        <th width="30%">Workshop Feature</th>
                        <th width="45%">Value Prop for Script</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    # --- CONTENT GENERATION ---
    
    # 1. Sidebar Data
    industry = snapshot.get('industry', 'Unknown')
    size = snapshot.get('size', 'Unknown')
    location = snapshot.get('location', 'Unknown')
    fiscal = snapshot.get('fiscal_year', 'Unknown')
    glassdoor = snapshot.get('glassdoor_score', 'N/A')
    
    tech_html = get_tech_ecosystem_html(snapshot.get('tech_stack', []))
    openers_html = get_openers_html(openers)
    
    # 2. Main Content Data
    
    # Why Now
    why_now_rows = ""
    for item in why_now[:3]:
        title = item.get('title', 'Why Now') if isinstance(item, dict) else 'Insight'
        desc = item.get('description', str(item)) if isinstance(item, dict) else str(item)
        source_id = item.get('source') if isinstance(item, dict) else None
        
        # Link the title if source exists
        display_title = get_source_link(source_id, title)
        
        why_now_rows += f'''
        <div class="why-now-item">
            <div class="why-now-icon">⚡</div>
            <div class="why-now-content">
                <strong>{display_title}</strong>
                <p>{desc}</p>
            </div>
        </div>
        '''

    # Personas (UPDATED STRUCTURE)
    personas_cards = ""
    for p in personas[:2]:
        # Handle new keys: name, role, email
        name = p.get('name', 'Internal Comms Lead')
        role = p.get('role', 'Decision Maker')
        email = p.get('email', 'Unknown')
        is_verified = p.get('is_named_person', False)
        
        verified_badge = '<span class="verified-badge">✓ Verified Contact</span>' if is_verified else ''
        email_html = f'<div class="persona-email">📧 {email}</div>' if email and email != 'Unknown' else ''
        
        goals = p.get('goals', [])
        fears = p.get('fears', [])
        
        goals_list = "".join([f"<li>{g}</li>" for g in goals[:2]])
        fears_list = "".join([f"<li>{f}</li>" for f in fears[:2]])
        
        personas_cards += f'''
        <div class="persona-card">
            <div class="persona-header">
                <div class="persona-top-row">
                    <span class="persona-icon">👤</span>
                    <div class="persona-identity">
                        <div class="persona-name">{name}</div>
                        <div class="persona-role">{role}</div>
                    </div>
                </div>
                {verified_badge}
                {email_html}
            </div>
            <div class="persona-body">
                <div class="persona-section">
                    <div class="persona-label" style="color:#10b981;">GOALS</div>
                    <ul>{goals_list}</ul>
                </div>
                <div class="persona-section">
                    <div class="persona-label" style="color:#ef4444;">PAINS</div>
                    <ul>{fears_list}</ul>
                </div>
            </div>
        </div>
        '''

    solution_table_html = get_solution_match_table()
    sources_count = len(metadata.get('all_sources', []))
    
    # --- CSS STYLING ---
    css_string = """
    @page { size: Letter; margin: 0; }
    @font-face { font-family: 'Inter'; src: local('Arial'); }

    body {
        font-family: 'Inter', sans-serif;
        margin: 0; padding: 0;
        background-color: #ffffff; color: #1f2937;
        font-size: 10px; line-height: 1.4;
    }
    
    a.source-link {
        color: #1e3a8a;
        text-decoration: none;
        border-bottom: 1px dotted #1e3a8a;
    }

    /* LAYOUT GRID */
    .container { display: flex; flex-direction: row; height: 100vh; }

    /* --- LEFT SIDEBAR DESIGN --- */
    .sidebar {
        flex: 0 0 34%;
        background-color: #1e3a8a; /* Workshop Blue */
        color: #ffffff;
        padding: 25px;
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .brand-logo { max-height: 30px; width: auto; filter: brightness(0) invert(1); }
    .brand-text { font-size: 24px; font-weight: 800; color: white; }

    /* Sidebar Boxes */
    .sidebar-box {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 15px;
    }

    .sidebar-title {
        color: #93c5fd;
        font-size: 9px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 5px;
    }

    /* Firmographic Grid */
    .stat-row { display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center; }
    .stat-label { font-size: 9px; opacity: 0.8; }
    .stat-val { font-size: 10px; font-weight: 600; text-align: right; }

    /* Tech Ecosystem */
    .tech-grid { display: flex; flex-wrap: wrap; gap: 5px; }
    .tech-pill { 
        background: rgba(0,0,0,0.2); 
        padding: 4px 8px; 
        border-radius: 4px; 
        font-size: 9px; 
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .integration-highlight {
        background: #eff6ff;
        color: #1e3a8a;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 10px;
        border-left: 3px solid #3b82f6;
    }
    .highlight-sub { font-size: 8px; opacity: 0.8; margin-top: 2px; }

    /* Openers */
    .opener-box { margin-bottom: 12px; }
    .opener-label { 
        font-size: 8px; 
        color: #60a5fa; 
        font-weight: 700; 
        text-transform: uppercase; 
        margin-bottom: 3px; 
    }
    .opener-script {
        font-style: italic;
        font-size: 10px;
        line-height: 1.4;
        background: rgba(0,0,0,0.2);
        padding: 8px;
        border-radius: 0 6px 6px 6px;
        border-left: 2px solid #60a5fa;
    }

    /* --- RIGHT CONTENT --- */
    .main-content { flex: 1; padding: 35px 45px; }
    
    .header { 
        border-bottom: 2px solid #f3f4f6; 
        padding-bottom: 15px; margin-bottom: 25px; 
        display: flex; justify-content: space-between; align-items: flex-end;
    }
    .company-name { font-size: 28px; font-weight: 800; color: #111827; line-height: 1; }
    .report-meta { text-align: right; color: #6b7280; font-size: 9px; }

    .section-title { 
        font-size: 14px; font-weight: 700; color: #1e3a8a; 
        text-transform: uppercase; letter-spacing: 0.5px; 
        margin-bottom: 15px; display: flex; align-items: center; gap: 8px;
    }

    /* Why Now */
    .why-now-item { 
        background: #f0f9ff; border-left: 4px solid #0ea5e9; 
        padding: 10px 12px; margin-bottom: 10px; 
        display: flex; gap: 10px; border-radius: 0 4px 4px 0;
    }
    .why-now-content p { margin: 2px 0 0 0; font-size: 10px; color: #374151; }
    
    /* Updated Persona Cards */
    .persona-grid { display: flex; gap: 15px; margin-bottom: 30px; }
    .persona-card { flex: 1; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
    .persona-header { background: #f9fafb; padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }
    
    .persona-top-row { display: flex; gap: 8px; align-items: center; margin-bottom: 5px; }
    .persona-name { font-weight: 800; color: #111827; font-size: 11px; }
    .persona-role { font-size: 9px; color: #6b7280; margin-top: 1px; }
    
    .verified-badge { 
        display: inline-block; background: #d1fae5; color: #059669; 
        padding: 2px 6px; border-radius: 10px; font-size: 8px; font-weight: 600; 
        margin-bottom: 4px;
    }
    .persona-email { font-family: monospace; font-size: 9px; color: #4b5563; background: #e5e7eb; padding: 2px 5px; border-radius: 3px; display: inline-block; }
    
    .persona-body { padding: 10px; }
    .persona-body ul { margin: 0; padding-left: 12px; }
    .persona-body li { margin-bottom: 2px; font-size: 9px; color: #4b5563; }

    /* SOLUTION TABLE */
    .solution-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 9px;
        margin-bottom: 30px;
    }
    .solution-table th {
        text-align: left;
        background-color: #f3f4f6;
        padding: 8px;
        border-bottom: 2px solid #e5e7eb;
        color: #4b5563;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 8px;
    }
    .solution-table td {
        padding: 10px 8px;
        border-bottom: 1px solid #e5e7eb;
        vertical-align: top;
    }
    .col-pain { color: #ef4444; }
    .col-feature { color: #2563eb; font-weight: 600; }
    .col-value { color: #374151; }

    .footer { 
        margin-top: auto; border-top: 1px solid #e5e7eb; padding-top: 10px; 
        font-size: 8px; color: #9ca3af; display: flex; justify-content: space-between; 
    }
    """

    # --- HTML ASSEMBLY ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body>
        <div class="container">
            <div class="sidebar">
                <div class="brand-area" style="margin-bottom:10px;">
                    {logo_img}
                </div>

                <div class="sidebar-box">
                    <div class="sidebar-title">Quick Stats</div>
                    <div class="stat-row">
                        <span class="stat-label">Industry</span>
                        <span class="stat-val">{industry}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">HQ Location</span>
                        <span class="stat-val">{location}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Employees</span>
                        <span class="stat-val">{size}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Fiscal Year</span>
                        <span class="stat-val">{fiscal}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Glassdoor</span>
                        <span class="stat-val">{glassdoor}</span>
                    </div>
                </div>

                <div class="sidebar-box">
                    <div class="sidebar-title">Tech Ecosystem</div>
                    {tech_html}
                </div>

                <div class="sidebar-box" style="flex-grow: 1;">
                    <div class="sidebar-title">⚡ Call Scripts</div>
                    {openers_html}
                </div>
                
                <div style="font-size:8px; opacity:0.5; margin-top:auto;">
                    Internal Use Only • Generated {datetime.now().strftime("%Y-%m-%d")}
                </div>
            </div>

            <div class="main-content">
                <div class="header">
                    <div class="company-name">{company_name}</div>
                    <div class="report-meta">ACCOUNT INTELLIGENCE BRIEF</div>
                </div>

                <div class="section-title">🚀 Why Reach Out Now</div>
                <div class="why-now-container">
                    {why_now_rows}
                </div>

                <div class="section-title">👥 Key Decision Makers</div>
                <div class="persona-grid">
                    {personas_cards}
                </div>

                {solution_table_html}
                
                <div class="footer">
                    <div>AI Research Agent v2.1 • Internal Use Only</div>
                    <div>{sources_count} Sources Analyzed</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Render PDF to BytesIO buffer
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    result_file = BytesIO()
    html.write_pdf(result_file, stylesheets=[CSS(string=css_string, font_config=font_config)])
    result_file.seek(0)
    return result_file
