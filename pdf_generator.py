from xhtml2pdf import pisa
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
    Converts structured data into a branded Workshop PDF with embedded links.
    
    Args:
        structured_data: Dict with keys: snapshot, why_now, personas, angles
        company_name: String name of the target company
        logo_path: Optional path to Workshop logo image file
    """
    
    # Extract sections
    snapshot = structured_data.get('snapshot', {})
    why_now = structured_data.get('why_now', [])
    personas = structured_data.get('personas', [])
    angles = structured_data.get('angles', [])
    metadata = structured_data.get('_metadata', {})
    
    # Logo embedding (if provided)
    logo_html = ""
    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode()
            # Determine image type
            ext = logo_path.lower().split('.')[-1]
            mime_type = f'image/{ext}' if ext in ['png', 'jpg', 'jpeg'] else 'image/png'
            logo_html = f'<img src="data:{mime_type};base64,{logo_data}" style="height: 28px; width: auto; display: block;"/>'
        except Exception as e:
            print(f"⚠️ Could not load logo: {e}")
            logo_html = '<div style="color: #2D5BFF; font-size: 18px; font-weight: 700;">Workshop</div>'
    else:
        logo_html = '<div style="color: #2D5BFF; font-size: 18px; font-weight: 700;">Workshop</div>'
    
    # Build snapshot HTML with more detail
    tech_stack_items = snapshot.get('tech_stack', [])
    if tech_stack_items:
        tech_stack_html = ' '.join([
            f'<span style="background-color: #EFF6FF; color: #2D5BFF; padding: 2px 7px; margin-right: 3px; margin-bottom: 3px; font-size: 9px; border-radius: 2px; display: inline-block; font-weight: 600; border: 1px solid #DBEAFE;">{item.get("tool", item) if isinstance(item, dict) else item}</span>'
            for item in tech_stack_items
        ])
    else:
        tech_stack_html = '<span style="color: #999; font-size: 9px; font-style: italic;">Not publicly available</span>'
    
    # Change events with links
    change_events_items = snapshot.get('change_events', [])
    if change_events_items:
        change_events_html = ''
        for item in change_events_items[:4]:  # Max 4 events
            if isinstance(item, dict):
                event_text = item.get('event', str(item))
                source_url = item.get('source_url', '')
                if source_url:
                    change_events_html += f'<tr><td style="padding: 2px 0; font-size: 9px; color: #374151; line-height: 1.4;"><span style="color: #FF6B35; font-weight: bold; margin-right: 4px;">•</span><a href="{source_url}" style="color: #374151; text-decoration: none;">{event_text}</a></td></tr>'
                else:
                    change_events_html += f'<tr><td style="padding: 2px 0; font-size: 9px; color: #374151; line-height: 1.4;"><span style="color: #FF6B35; font-weight: bold; margin-right: 4px;">•</span>{event_text}</td></tr>'
            else:
                change_events_html += f'<tr><td style="padding: 2px 0; font-size: 9px; color: #374151; line-height: 1.4;"><span style="color: #FF6B35; font-weight: bold; margin-right: 4px;">•</span>{item}</td></tr>'
    else:
        change_events_html = '<tr><td style="padding: 2px 0; font-size: 9px; color: #999; font-style: italic;">Limited public information available</td></tr>'
    
    snapshot_html = f"""
        <table style="width: 100%; margin-bottom: 8px; border-collapse: collapse;">
            <tr>
                <td style="width: 23%; padding-right: 5px; vertical-align: top; padding-bottom: 5px;">
                    <div style="color: #666; font-size: 8px; font-weight: 700; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Industry</div>
                    <div style="font-size: 9px; font-weight: 600; color: #1a1a1a; line-height: 1.2;">{snapshot.get('industry', 'Unknown')}</div>
                </td>
                <td style="width: 23%; padding-right: 5px; vertical-align: top; padding-bottom: 5px;">
                    <div style="color: #666; font-size: 8px; font-weight: 700; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Size</div>
                    <div style="font-size: 9px; font-weight: 600; color: #1a1a1a; line-height: 1.2;">{snapshot.get('size', 'Unknown')}</div>
                </td>
                <td style="width: 27%; padding-right: 5px; vertical-align: top; padding-bottom: 5px;">
                    <div style="color: #666; font-size: 8px; font-weight: 700; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Location</div>
                    <div style="font-size: 9px; font-weight: 600; color: #1a1a1a; line-height: 1.2;">{snapshot.get('location', 'Unknown')}</div>
                </td>
                <td style="width: 27%; vertical-align: top; padding-bottom: 5px;">
                    <div style="color: #666; font-size: 8px; font-weight: 700; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Footprint</div>
                    <div style="font-size: 9px; font-weight: 600; color: #1a1a1a; line-height: 1.2;">{snapshot.get('footprint', 'Unknown')}</div>
                </td>
            </tr>
        </table>
        
        <div style="border-top: 1px solid #e5e5e5; padding-top: 6px; margin-bottom: 6px;">
            <div style="color: #666; font-size: 8px; font-weight: 700; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.5px;">Current Tech Stack</div>
            <div style="line-height: 1.7;">
                {tech_stack_html}
            </div>
        </div>
        
        <div style="border-top: 1px solid #e5e5e5; padding-top: 6px;">
            <div style="color: #666; font-size: 8px; font-weight: 700; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.5px;">Recent Change Events</div>
            <table style="width: 100%; border-collapse: collapse;">
                {change_events_html}
            </table>
        </div>
    """
    
    # Why Now with links
    why_now_html = '<table style="width: 100%; border-collapse: collapse;">'
    for idx, item in enumerate(why_now[:3]):
        margin_bottom = '7px' if idx < len(why_now[:3]) - 1 else '0'
        title = item.get('title', '') if isinstance(item, dict) else 'Point'
        description = item.get('description', str(item)) if isinstance(item, dict) else str(item)
        source_url = item.get('source_url', '') if isinstance(item, dict) else ''
        
        if source_url:
            desc_html = f'<a href="{source_url}" style="color: #4b5563; text-decoration: none;">{description}</a>'
        else:
            desc_html = description
            
        why_now_html += f'''
            <tr>
                <td style="padding-bottom: {margin_bottom}; vertical-align: top;">
                    <div style="line-height: 1.4;">
                        <span style="color: #FF6B35; font-weight: bold; font-size: 12px; margin-right: 3px;">›</span>
                        <span style="font-weight: 700; color: #1a1a1a; font-size: 9px;">{title}:</span>
                        <span style="color: #4b5563; font-size: 9px;"> {desc_html}</span>
                    </div>
                </td>
            </tr>
        '''
    why_now_html += '</table>'
    
    # Personas - Enhanced with more detail
    personas_html = ''
    for idx, persona in enumerate(personas[:2]):
        margin_bottom = '7px' if idx < len(personas[:2]) - 1 else '0'
        title = persona.get('title', 'Unknown') if isinstance(persona, dict) else str(persona)
        is_named = persona.get('is_named_person', False) if isinstance(persona, dict) else False
        
        # Add visual indicator for actual named person
        title_badge = ''
        if is_named:
            title_badge = '<span style="background-color: #10B981; color: white; font-size: 7px; padding: 1px 4px; border-radius: 2px; margin-left: 4px; font-weight: 600;">VERIFIED</span>'
        
        goals = persona.get('goals', []) if isinstance(persona, dict) else []
        fears = persona.get('fears', []) if isinstance(persona, dict) else []
        
        goals_html = ''.join([
            f'<tr><td style="padding: 1px 0; font-size: 8px; color: #374151; line-height: 1.3;">• {goal}</td></tr>'
            for goal in goals[:3]
        ])
        
        fears_html = ''.join([
            f'<tr><td style="padding: 1px 0; font-size: 8px; color: #374151; line-height: 1.3;">• {fear}</td></tr>'
            for fear in fears[:3]
        ])
        
        personas_html += f'''
            <div style="background-color: #EFF6FF; border-left: 3px solid #2D5BFF; padding: 7px 9px; margin-bottom: {margin_bottom}; border-radius: 2px;">
                <div style="font-weight: 700; color: #1a1a1a; font-size: 9px; margin-bottom: 4px;">{title}{title_badge}</div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding-right: 6px; vertical-align: top; width: 50%;">
                            <div style="color: #666; font-weight: 700; font-size: 7px; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Goals</div>
                            <table style="width: 100%; border-collapse: collapse;">
                                {goals_html}
                            </table>
                        </td>
                        <td style="vertical-align: top; width: 50%;">
                            <div style="color: #666; font-weight: 700; font-size: 7px; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Fears</div>
                            <table style="width: 100%; border-collapse: collapse;">
                                {fears_html}
                            </table>
                        </td>
                    </tr>
                </table>
            </div>
        '''
    
    # Angles with source links and Workshop features
    angles_html = ''
    
    # Get Workshop feature matches
    workshop_features_matches = []
    if FEATURES_AVAILABLE:
        try:
            workshop_features_matches = match_features_to_company(structured_data)
        except Exception as e:
            print(f"⚠️ Feature matching error: {e}")
    
    for idx, angle in enumerate(angles[:2]):
        margin_bottom = '9px' if idx < len(angles[:2]) - 1 else '0'
        title = angle.get('title', '') if isinstance(angle, dict) else 'Approach'
        description = angle.get('description', str(angle)) if isinstance(angle, dict) else str(angle)
        metric = angle.get('metric', 'N/A') if isinstance(angle, dict) else 'N/A'
        sources = angle.get('sources', []) if isinstance(angle, dict) else []
        
        # Add source indicators
        source_badges = ''
        if sources:
            source_badges = '<div style="margin-top: 3px;">'
            for src in sources[:3]:
                source_badges += f'<span style="background-color: #f3f4f6; color: #666; font-size: 6px; padding: 1px 3px; border-radius: 2px; margin-right: 2px; display: inline-block;">SOURCE {src}</span>'
            source_badges += '</div>'
        
        angles_html += f'''
            <div style="border-left: 3px solid #2D5BFF; padding-left: 7px; margin-bottom: {margin_bottom};">
                <div style="font-weight: 700; color: #1a1a1a; font-size: 9px; margin-bottom: 2px;">{title}</div>
                <div style="font-size: 8px; color: #374151; line-height: 1.4; margin-bottom: 3px;">{description}</div>
                <div style="font-size: 7px; background-color: #FFF7ED; padding: 3px 5px; display: inline-block; border-radius: 2px; border: 1px solid #FFEDD5;">
                    <span style="font-weight: 700; color: #EA580C;">Target:</span>
                    <span style="color: #1a1a1a;"> {metric}</span>
                </div>
                {source_badges}
            </div>
        '''
    
    # Workshop Features Section
    workshop_features_html = ''
    competitor_displacement = None
    
    if FEATURES_AVAILABLE:
        # Check for competitive displacement opportunity
        tech_stack = snapshot.get('tech_stack', [])
        competitor_displacement = get_competitor_displacement_angle(tech_stack)
    
    if workshop_features_matches:
        workshop_features_html = '<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #e5e5e5;">'
        workshop_features_html += '<div style="color: #666; font-size: 8px; font-weight: 700; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px;">Workshop Platform Fit</div>'
        
        for idx, feature in enumerate(workshop_features_matches[:3]):  # Show top 3
            bg_color = '#F0FDF4' if idx == 0 else '#FFF7ED' if idx == 1 else '#EFF6FF'
            border_color = '#10B981' if idx == 0 else '#FB923C' if idx == 1 else '#3B82F6'
            
            features_list = ''.join([
                f'<tr><td style="padding: 1px 0; font-size: 7px; color: #374151; line-height: 1.3;">✓ {feat}</td></tr>'
                for feat in feature['features'][:3]  # Show top 3 features
            ])
            
            workshop_features_html += f'''
                <div style="background-color: {bg_color}; border-left: 2px solid {border_color}; padding: 5px 6px; margin-bottom: 5px; border-radius: 2px;">
                    <div style="margin-bottom: 2px;">
                        <span style="font-weight: 700; color: #1a1a1a; font-size: 8px;">{feature['name']}</span>
                        <span style="background-color: white; color: {border_color}; font-size: 6px; padding: 1px 3px; border-radius: 2px; margin-left: 3px; font-weight: 600; border: 1px solid {border_color};">{feature['tier']}</span>
                    </div>
                    <table style="width: 100%; border-collapse: collapse;">
                        {features_list}
                    </table>
                </div>
            '''
        
        # Add competitive displacement if relevant
        if competitor_displacement:
            workshop_features_html += f'''
                <div style="background-color: #FEF3C7; border: 1px solid #FCD34D; padding: 5px 6px; margin-top: 5px; border-radius: 2px;">
                    <div style="font-size: 7px; color: #92400E; line-height: 1.3;">
                        <span style="font-weight: 700;">💡 Opportunity:</span> {competitor_displacement}
                    </div>
                </div>
            '''
        
        workshop_features_html += '</div>'
    
    # Sources reference section (more compact)
    sources_html = ''
    all_sources = metadata.get('all_sources', [])
    if all_sources:
        sources_html = '<div style="margin-top: 10px; padding-top: 6px; border-top: 1px solid #e5e5e5;">'
        sources_html += '<div style="color: #666; font-size: 7px; font-weight: 700; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Research Sources</div>'
        sources_html += '<table style="width: 100%; border-collapse: collapse;">'
        for idx, source in enumerate(all_sources[:8], 1):  # Increased to 8 sources
            url = source.get('url', '')
            title = source.get('title', 'Source')
            # Truncate title if too long
            if len(title) > 50:
                title = title[:47] + '...'
            sources_html += f'<tr><td style="padding: 0.5px 0;"><span style="color: #666; font-weight: 700; font-size: 6px;">[{idx}]</span> <a href="{url}" style="color: #2D5BFF; text-decoration: none; font-size: 6px; line-height: 1.3;">{title}</a></td></tr>'
        sources_html += '</table></div>'
    
    # Complete HTML
    source_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: letter;
                margin: 0.5in 0.6in;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 9px;
                color: #1a1a1a;
                line-height: 1.3;
                margin: 0;
                padding: 0;
            }}
            a {{
                color: #2D5BFF;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .header-section {{
                border-bottom: 2px solid #2D5BFF;
                padding-bottom: 8px;
                margin-bottom: 11px;
                background: linear-gradient(to right, #EFF6FF 0%, #ffffff 100%);
                padding: 8px;
                margin: -8px -8px 11px -8px;
            }}
            .section-title {{
                color: #1a1a1a;
                font-size: 10px;
                font-weight: 700;
                margin-bottom: 7px;
                padding-bottom: 2px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .section-title-blue {{
                border-left: 3px solid #2D5BFF;
                padding-left: 5px;
            }}
            .section-title-orange {{
                border-left: 3px solid #FF6B35;
                padding-left: 5px;
            }}
            .footer-section {{
                border-top: 1px solid #e5e5e5;
                padding-top: 6px;
                margin-top: 11px;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <div class="header-section">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 70%; vertical-align: middle;">
                        {logo_html}
                        <div style="font-size: 17px; font-weight: 700; color: #1a1a1a; margin-top: 3px; margin-bottom: 1px; line-height: 1.1;">{company_name}</div>
                        <div style="font-size: 8px; color: #666;">Account Intelligence Brief • Internal Communications Strategy</div>
                    </td>
                    <td style="width: 30%; text-align: right; vertical-align: middle;">
                        <div style="font-size: 7px; color: #999; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Internal Use Only</div>
                        <div style="font-size: 7px; color: #999; margin-top: 2px;">{_get_date_string()}</div>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Two Column Layout -->
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 48%; vertical-align: top; padding-right: 8px;">
                    <!-- LEFT COLUMN -->
                    
                    <!-- Section 1: Company Snapshot -->
                    <div style="margin-bottom: 13px;">
                        <div class="section-title section-title-blue">Company Snapshot</div>
                        {snapshot_html}
                    </div>
                    
                    <!-- Section 3: Key Personas -->
                    <div style="margin-bottom: 13px;">
                        <div class="section-title section-title-blue">Key Decision Makers</div>
                        {personas_html}
                    </div>
                    
                </td>
                <td style="width: 48%; vertical-align: top; padding-left: 8px;">
                    <!-- RIGHT COLUMN -->
                    
                    <!-- Section 2: Why Now -->
                    <div style="margin-bottom: 13px;">
                        <div class="section-title section-title-orange">Why Now</div>
                        {why_now_html}
                    </div>
                    
                    <!-- Section 4: Recommended Angles -->
                    <div style="margin-bottom: 13px;">
                        <div class="section-title section-title-orange">Recommended Approach</div>
                        {angles_html}
                    </div>
                    
                    <!-- Workshop Features -->
                    {workshop_features_html}
                    
                    <!-- Sources -->
                    {sources_html}
                    
                </td>
            </tr>
        </table>

        <!-- Footer -->
        <div class="footer-section">
            <div style="font-size: 7px; color: #999; text-align: center; font-weight: 500;">
                Workshop ABM Intelligence • For BDR Use Only • Generated by AI Research Agent
            </div>
        </div>
    </body>
    </html>
    """

    # Render PDF
    result_file = BytesIO()
    pisa_status = pisa.CreatePDF(source_html, dest=result_file)
    
    if pisa_status.err:
        print(f"PDF generation error: {pisa_status.err}")
        return None
        
    result_file.seek(0)
    return result_file


def _get_date_string():
    """Helper to get formatted date string"""
    return datetime.now().strftime("%B %d, %Y")
