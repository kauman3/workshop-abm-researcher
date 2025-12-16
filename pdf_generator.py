from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from datetime import datetime
import base64
import os

# Import Workshop features matcher
try:
    from workshop_features import match_features_to_company, get_competitor_displacement_angle
    FEATURES_AVAILABLE = True
except ImportError:
    FEATURES_AVAILABLE = False
    print("⚠️ workshop_features.py not found - feature matching disabled")

def create_styled_pdf(structured_data, company_name, logo_path=None):
    """
    Converts structured data into a branded Workshop PDF using WeasyPrint.
    Layout: Split-Screen Strategist (Sidebar for data, Main area for narrative).
    """
    
    # Extract sections
    snapshot = structured_data.get('snapshot', {})
    why_now = structured_data.get('why_now', [])
    personas = structured_data.get('personas', [])
    angles = structured_data.get('angles', [])
    metadata = structured_data.get('_metadata', {})
    
    # --- PREPARE ASSETS ---
    
    # Logo Handling (Convert to base64 for embedding)
    logo_img = ""
    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                logo_b64 = base64.b64encode(f.read()).decode()
            mime_type = 'image/png' # Assume png for safety
            # We use a filter to make the logo white if it's in the dark sidebar, 
            # but for this design, let's keep the logo in the top white area or sidebar.
            # Let's put a white version in the sidebar if possible, otherwise standard.
            logo_img = f'<img src="data:{mime_type};base64,{logo_b64}" class="brand-logo"/>'
        except Exception:
            logo_img = '<div class="brand-text">Workshop</div>'
    else:
        logo_img = '<div class="brand-text">Workshop</div>'

    # --- HTML HELPERS ---
    
    def get_tech_stack_html(stack):
        if not stack: return '<div class="empty-state">No tech stack data</div>'
        html = '<div class="tag-container">'
        for item in stack:
            tool = item.get("tool", item) if isinstance(item, dict) else item
            html += f'<span class="tag tag-tech">{tool}</span>'
        html += '</div>'
        return html

    def get_change_events_html(events):
        if not events: return '<div class="empty-state">No recent changes found</div>'
        html = '<ul class="event-list">'
        for item in events[:4]:
            text = item.get('event', str(item)) if isinstance(item, dict) else str(item)
            html += f'<li>{text}</li>'
        html += '</ul>'
        return html

    # --- CONTENT GENERATION ---
    
    # 1. Sidebar Content (The "Facts")
    industry = snapshot.get('industry', 'Unknown')
    size = snapshot.get('size', 'Unknown')
    location = snapshot.get('location', 'Unknown')
    tech_stack_html = get_tech_stack_html(snapshot.get('tech_stack', []))
    change_events_html = get_change_events_html(snapshot.get('change_events', []))
    
    # 2. Main Content (The "Story")
    
    # Why Now
    why_now_rows = ""
    for item in why_now[:3]:
        title = item.get('title', 'Why Now') if isinstance(item, dict) else 'Insight'
        desc = item.get('description', str(item)) if isinstance(item, dict) else str(item)
        why_now_rows += f'''
        <div class="why-now-item">
            <div class="why-now-icon">⚡</div>
            <div class="why-now-content">
                <strong>{title}</strong>
                <p>{desc}</p>
            </div>
        </div>
        '''

    # Personas
    personas_cards = ""
    for p in personas[:2]:
        name = p.get('title', 'Decision Maker') if isinstance(p, dict) else str(p)
        is_verified = p.get('is_named_person', False) if isinstance(p, dict) else False
        verified_badge = '<span class="verified-badge">✓ Verified</span>' if is_verified else ''
        
        goals = p.get('goals', []) if isinstance(p, dict) else []
        fears = p.get('fears', []) if isinstance(p, dict) else []
        
        goals_list = "".join([f"<li>{g}</li>" for g in goals[:2]])
        fears_list = "".join([f"<li>{f}</li>" for f in fears[:2]])
        
        personas_cards += f'''
        <div class="persona-card">
            <div class="persona-header">
                <span class="persona-icon">👤</span>
                <div class="persona-title">{name} {verified_badge}</div>
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

    # Angles / Value Props
    angles_html = ""
    for angle in angles[:2]:
        title = angle.get('title', 'Approach') if isinstance(angle, dict) else 'Strategy'
        desc = angle.get('description', '') if isinstance(angle, dict) else ''
        metric = angle.get('metric', '') if isinstance(angle, dict) else ''
        
        angles_html += f'''
        <div class="angle-box">
            <div class="angle-header">{title}</div>
            <div class="angle-desc">{desc}</div>
            <div class="angle-metric">
                <span class="metric-label">PROOF POINT:</span> {metric}
            </div>
        </div>
        '''

    # Workshop Feature Matching
    features_html = ""
    if FEATURES_AVAILABLE:
        matches = match_features_to_company(structured_data)
        if matches:
            feature_items = ""
            for f in matches[:3]:
                feature_items += f'<span class="tag tag-feature">{f["name"]}</span>'
            
            features_html = f'''
            <div class="sidebar-section">
                <div class="sidebar-label">Platform Fit</div>
                <div class="tag-container">
                    {feature_items}
                </div>
            </div>
            '''
            
    # Sources (Footer)
    sources_count = len(metadata.get('all_sources', []))
    date_str = datetime.now().strftime("%B %d, %Y")

    # --- CSS STYLING ---
    css_string = """
    @page {
        size: Letter;
        margin: 0; /* We handle margins in the body for the full-bleed sidebar */
    }
    
    @font-face {
        font-family: 'Inter';
        src: local('Arial'); /* Fallback for offline/no-font environments */
    }

    body {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #ffffff;
        color: #1f2937;
        font-size: 10px; /* Base size */
        line-height: 1.4;
    }

    /* LAYOUT GRID */
    .container {
        display: flex;
        flex-direction: row;
        height: 100vh; /* Full page height */
    }

    /* LEFT SIDEBAR (DARK) */
    .sidebar {
        flex: 0 0 32%; /* 32% Width */
        background-color: #1e3a8a; /* Workshop Blue */
        color: #ffffff;
        padding: 25px;
        box-sizing: border-box;
    }

    /* RIGHT CONTENT (LIGHT) */
    .main-content {
        flex: 1;
        padding: 30px 40px;
        background-color: #ffffff;
    }

    /* SIDEBAR STYLES */
    .brand-area { margin-bottom: 40px; }
    .brand-text { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
    .brand-logo { max-height: 35px; width: auto; filter: brightness(0) invert(1); } /* Make logo white */

    .sidebar-section { margin-bottom: 30px; }
    .sidebar-label { 
        text-transform: uppercase; 
        font-size: 9px; 
        font-weight: 700; 
        opacity: 0.7; 
        margin-bottom: 8px; 
        letter-spacing: 0.5px;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 4px;
    }

    .data-point { margin-bottom: 12px; }
    .data-label { font-size: 9px; opacity: 0.7; }
    .data-value { font-size: 12px; font-weight: 600; }

    .tag-container { display: flex; flex-wrap: wrap; gap: 4px; }
    .tag { 
        padding: 3px 8px; 
        border-radius: 4px; 
        font-size: 9px; 
        font-weight: 500; 
    }
    .tag-tech { background-color: rgba(255,255,255,0.15); color: white; }
    .tag-feature { background-color: #3b82f6; color: white; border: 1px solid rgba(255,255,255,0.2); }

    .event-list { list-style: none; padding: 0; margin: 0; }
    .event-list li { 
        font-size: 9px; 
        margin-bottom: 8px; 
        padding-left: 10px; 
        border-left: 2px solid #60a5fa;
        opacity: 0.9;
    }

    /* MAIN CONTENT STYLES */
    .header { 
        border-bottom: 2px solid #f3f4f6; 
        padding-bottom: 15px; 
        margin-bottom: 25px; 
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }
    .company-name { font-size: 28px; font-weight: 800; color: #111827; line-height: 1; }
    .report-meta { text-align: right; color: #6b7280; font-size: 9px; }

    .section-title { 
        font-size: 14px; 
        font-weight: 700; 
        color: #1e3a8a; 
        text-transform: uppercase; 
        letter-spacing: 0.5px;
        margin-bottom: 15px; 
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* WHY NOW BOXES */
    .why-now-container { margin-bottom: 30px; }
    .why-now-item { 
        background: #f0f9ff; 
        border-left: 4px solid #0ea5e9; 
        padding: 10px 12px; 
        margin-bottom: 10px; 
        display: flex; 
        gap: 10px; 
        border-radius: 0 4px 4px 0;
    }
    .why-now-icon { font-size: 14px; }
    .why-now-content p { margin: 2px 0 0 0; font-size: 10px; color: #374151; }

    /* PERSONA CARDS (GRID) */
    .persona-grid { 
        display: flex; 
        gap: 15px; 
        margin-bottom: 30px; 
    }
    .persona-card { 
        flex: 1; 
        border: 1px solid #e5e7eb; 
        border-radius: 6px; 
        overflow: hidden; 
    }
    .persona-header { 
        background: #f9fafb; 
        padding: 8px 12px; 
        border-bottom: 1px solid #e5e7eb; 
        font-weight: 700; 
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .verified-badge { 
        background: #d1fae5; color: #059669; 
        font-size: 8px; padding: 1px 4px; border-radius: 2px; text-transform: uppercase; 
    }
    .persona-body { padding: 10px; }
    .persona-section { margin-bottom: 8px; }
    .persona-label { font-size: 8px; font-weight: 700; text-transform: uppercase; margin-bottom: 2px; }
    .persona-body ul { margin: 0; padding-left: 12px; }
    .persona-body li { margin-bottom: 2px; font-size: 9px; color: #4b5563; }

    /* ANGLES */
    .angle-box { 
        border: 1px solid #e5e7eb; 
        border-radius: 6px; 
        padding: 12px; 
        margin-bottom: 12px; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .angle-header { font-weight: 700; color: #111827; margin-bottom: 4px; font-size: 11px; }
    .angle-desc { color: #4b5563; margin-bottom: 8px; font-size: 10px; }
    .angle-metric { 
        background: #fff7ed; color: #9a3412; 
        display: inline-block; padding: 4px 8px; 
        border-radius: 4px; font-weight: 600; font-size: 9px; 
        border: 1px solid #ffedd5;
    }

    .footer { 
        margin-top: 40px; 
        border-top: 1px solid #e5e7eb; 
        padding-top: 10px; 
        font-size: 8px; 
        color: #9ca3af; 
        display: flex;
        justify-content: space-between;
    }
    """

    # --- FULL HTML ASSEMBLY ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <div class="brand-area">
                    {logo_img}
                </div>
                
                <div class="sidebar-section">
                    <div class="sidebar-label">Firmographic</div>
                    <div class="data-point">
                        <div class="data-label">Industry</div>
                        <div class="data-value">{industry}</div>
                    </div>
                    <div class="data-point">
                        <div class="data-label">Size</div>
                        <div class="data-value">{size}</div>
                    </div>
                    <div class="data-point">
                        <div class="data-label">Headquarters</div>
                        <div class="data-value">{location}</div>
                    </div>
                </div>

                <div class="sidebar-section">
                    <div class="sidebar-label">Tech Stack</div>
                    {tech_stack_html}
                </div>

                <div class="sidebar-section">
                    <div class="sidebar-label">Recent Signals</div>
                    {change_events_html}
                </div>
                
                {features_html}
            </div>

            <div class="main-content">
                <div class="header">
                    <div class="company-name">{company_name}</div>
                    <div class="report-meta">
                        <div>ACCOUNT INTELLIGENCE BRIEF</div>
                        <div>Generated: {date_str}</div>
                    </div>
                </div>

                <div class="section-title">🚀 Why Reach Out Now</div>
                <div class="why-now-container">
                    {why_now_rows}
                </div>

                <div class="section-title">👥 Key Decision Makers</div>
                <div class="persona-grid">
                    {personas_cards}
                </div>

                <div class="section-title">🎯 Recommended Strategy</div>
                {angles_html}
                
                <div class="footer">
                    <div>AI Research Agent v2.1 • Internal Use Only</div>
                    <div>{sources_count} Sources Analyzed</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # --- GENERATE PDF ---
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    
    # Render PDF to BytesIO buffer
    result_file = BytesIO()
    html.write_pdf(result_file, stylesheets=[CSS(string=css_string, font_config=font_config)])
    
    result_file.seek(0)
    return result_file
