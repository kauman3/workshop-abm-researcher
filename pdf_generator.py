from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime

def create_styled_pdf(structured_data, company_name):
    """
    Converts structured data into a branded Workshop PDF using xhtml2pdf.
    Optimized for xhtml2pdf's limitations while maintaining visual appeal.
    """
    
    # Extract sections from structured data
    snapshot = structured_data.get('snapshot', {})
    why_now = structured_data.get('why_now', [])
    personas = structured_data.get('personas', [])
    angles = structured_data.get('angles', [])
    
    # Build snapshot HTML - More compact, information-dense
    tech_stack_items = snapshot.get('tech_stack', [])
    tech_stack_html = ' '.join([
        f'<span style="background-color: #f3f4f6; padding: 2px 6px; margin-right: 3px; font-size: 9px; border-radius: 2px; display: inline-block;">{tech}</span>'
        for tech in tech_stack_items
    ]) if tech_stack_items else '<span style="color: #999; font-size: 9px;">Not publicly available</span>'
    
    change_events_html = ''.join([
        f'<tr><td style="padding: 2px 0; font-size: 10px; color: #374151; line-height: 1.3;"><span style="color: #FF6B35; font-weight: bold; margin-right: 4px;">•</span>{event}</td></tr>'
        for event in snapshot.get('change_events', [])
    ])
    
    snapshot_html = f"""
        <table style="width: 100%; margin-bottom: 10px; border-collapse: collapse;">
            <tr>
                <td style="width: 23%; padding-right: 6px; vertical-align: top; padding-bottom: 6px;">
                    <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 2px;">INDUSTRY</div>
                    <div style="font-size: 10px; font-weight: 600; color: #1a1a1a; line-height: 1.2;">{snapshot.get('industry', 'N/A')}</div>
                </td>
                <td style="width: 23%; padding-right: 6px; vertical-align: top; padding-bottom: 6px;">
                    <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 2px;">SIZE</div>
                    <div style="font-size: 10px; font-weight: 600; color: #1a1a1a; line-height: 1.2;">{snapshot.get('size', 'N/A')}</div>
                </td>
                <td style="width: 27%; padding-right: 6px; vertical-align: top; padding-bottom: 6px;">
                    <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 2px;">LOCATION</div>
                    <div style="font-size: 10px; font-weight: 600; color: #1a1a1a; line-height: 1.2;">{snapshot.get('location', 'N/A')}</div>
                </td>
                <td style="width: 27%; vertical-align: top; padding-bottom: 6px;">
                    <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 2px;">FOOTPRINT</div>
                    <div style="font-size: 10px; font-weight: 600; color: #1a1a1a; line-height: 1.2;">{snapshot.get('footprint', 'N/A')}</div>
                </td>
            </tr>
        </table>
        
        <div style="border-top: 1px solid #e5e5e5; padding-top: 7px; margin-bottom: 7px;">
            <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 4px; letter-spacing: 0.3px;">CURRENT TECH STACK</div>
            <div style="line-height: 1.6;">
                {tech_stack_html}
            </div>
        </div>
        
        <div style="border-top: 1px solid #e5e5e5; padding-top: 7px;">
            <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 4px; letter-spacing: 0.3px;">RECENT CHANGE EVENTS</div>
            <table style="width: 100%; border-collapse: collapse;">
                {change_events_html}
            </table>
        </div>
    """
    
    # Build Why Now HTML - More compact
    why_now_html = '<table style="width: 100%; border-collapse: collapse;">'
    for idx, item in enumerate(why_now[:3]):
        margin_bottom = '8px' if idx < len(why_now[:3]) - 1 else '0'
        why_now_html += f'''
            <tr>
                <td style="padding-bottom: {margin_bottom}; vertical-align: top;">
                    <div style="line-height: 1.4;">
                        <span style="color: #FF6B35; font-weight: bold; font-size: 13px; margin-right: 4px;">›</span>
                        <span style="font-weight: 600; color: #1a1a1a; font-size: 10px;">{item.get('title', '')}:</span>
                        <span style="color: #4b5563; font-size: 10px;"> {item.get('description', '')}</span>
                    </div>
                </td>
            </tr>
        '''
    why_now_html += '</table>'
    
    # Build Personas HTML - Denser layout
    personas_html = ''
    for idx, persona in enumerate(personas[:2]):
        margin_bottom = '8px' if idx < len(personas[:2]) - 1 else '0'
        
        goals_html = ''.join([
            f'<tr><td style="padding: 1px 0; font-size: 9px; color: #374151; line-height: 1.3;">• {goal}</td></tr>'
            for goal in persona.get('goals', [])[:2]
        ])
        
        fears_html = ''.join([
            f'<tr><td style="padding: 1px 0; font-size: 9px; color: #374151; line-height: 1.3;">• {fear}</td></tr>'
            for fear in persona.get('fears', [])[:2]
        ])
        
        personas_html += f'''
            <div style="background-color: #EFF6FF; border-left: 3px solid #2D5BFF; padding: 8px 10px; margin-bottom: {margin_bottom}; border-radius: 3px;">
                <div style="font-weight: 700; color: #1a1a1a; font-size: 10px; margin-bottom: 4px;">{persona.get('title', '')}</div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding-right: 8px; vertical-align: top; width: 50%;">
                            <div style="color: #666; font-weight: 600; font-size: 8px; margin-bottom: 2px; text-transform: uppercase;">Goals</div>
                            <table style="width: 100%; border-collapse: collapse;">
                                {goals_html}
                            </table>
                        </td>
                        <td style="vertical-align: top; width: 50%;">
                            <div style="color: #666; font-weight: 600; font-size: 8px; margin-bottom: 2px; text-transform: uppercase;">Fears</div>
                            <table style="width: 100%; border-collapse: collapse;">
                                {fears_html}
                            </table>
                        </td>
                    </tr>
                </table>
            </div>
        '''
    
    # Build Angles HTML - More information density
    angles_html = ''
    for idx, angle in enumerate(angles[:2]):
        margin_bottom = '10px' if idx < len(angles[:2]) - 1 else '0'
        angles_html += f'''
            <div style="border-left: 3px solid #2D5BFF; padding-left: 8px; margin-bottom: {margin_bottom};">
                <div style="font-weight: 700; color: #1a1a1a; font-size: 10px; margin-bottom: 3px;">{angle.get('title', '')}</div>
                <div style="font-size: 9px; color: #374151; line-height: 1.4; margin-bottom: 4px;">{angle.get('description', '')}</div>
                <div style="font-size: 8px; background-color: #f9fafb; padding: 3px 6px; display: inline-block; border-radius: 2px;">
                    <span style="font-weight: 600; color: #666;">Key metric:</span>
                    <span style="color: #1a1a1a;"> {angle.get('metric', '')}</span>
                </div>
            </div>
        '''
    
    # Add proof point if provided
    proof = structured_data.get('proof_point', {})
    if proof and proof.get('company'):
        angles_html += f'''
            <div style="background-color: #f9fafb; border: 1px solid #e5e7eb; padding: 8px; margin-top: 10px; border-radius: 3px;">
                <div style="color: #666; font-size: 8px; font-weight: 600; margin-bottom: 3px; letter-spacing: 0.3px;">SIMILAR CUSTOMER</div>
                <div style="font-weight: 700; color: #1a1a1a; font-size: 10px; margin-bottom: 1px;">{proof.get('company', '')}</div>
                <div style="font-size: 8px; color: #666; margin-bottom: 3px;">{proof.get('context', '')}</div>
                <div style="font-size: 9px; color: #374151; font-style: italic; line-height: 1.3;">"{proof.get('quote', '')}"</div>
            </div>
        '''
    
    # Complete HTML template with better spacing and typography
    source_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: letter;
                margin: 0.65in 0.75in;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 10px;
                color: #1a1a1a;
                line-height: 1.3;
                margin: 0;
                padding: 0;
            }}
            .header-section {{
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 10px;
                margin-bottom: 14px;
            }}
            .section-title {{
                color: #1a1a1a;
                font-size: 11px;
                font-weight: 700;
                margin-bottom: 8px;
                padding-bottom: 3px;
                border-bottom: 1px solid #e5e7eb;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
            .section-title-blue {{
                border-left: 3px solid #2D5BFF;
                padding-left: 6px;
                border-bottom: none;
            }}
            .section-title-orange {{
                border-left: 3px solid #FF6B35;
                padding-left: 6px;
                border-bottom: none;
            }}
            .footer-section {{
                border-top: 2px solid #e5e7eb;
                padding-top: 8px;
                margin-top: 14px;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <div class="header-section">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 75%; vertical-align: bottom;">
                        <div style="color: #2D5BFF; font-size: 16px; font-weight: 700; margin-bottom: 4px;">Workshop</div>
                        <div style="font-size: 20px; font-weight: 700; color: #1a1a1a; margin-bottom: 2px; line-height: 1.1;">{company_name}</div>
                        <div style="font-size: 9px; color: #666;">Account playbook for internal communications transformation</div>
                    </td>
                    <td style="width: 25%; text-align: right; vertical-align: bottom;">
                        <div style="font-size: 8px; color: #999; font-weight: 500;">INTERNAL USE ONLY</div>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Two Column Layout -->
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="width: 48%; vertical-align: top; padding-right: 10px;">
                    <!-- LEFT COLUMN -->
                    
                    <!-- Section 1: Company Snapshot -->
                    <div style="margin-bottom: 16px;">
                        <div class="section-title section-title-blue">Company Snapshot</div>
                        {snapshot_html}
                    </div>
                    
                    <!-- Section 3: Key Personas -->
                    <div style="margin-bottom: 16px;">
                        <div class="section-title section-title-blue">Key Personas</div>
                        {personas_html}
                    </div>
                    
                </td>
                <td style="width: 48%; vertical-align: top; padding-left: 10px;">
                    <!-- RIGHT COLUMN -->
                    
                    <!-- Section 2: Why Now -->
                    <div style="margin-bottom: 16px;">
                        <div class="section-title section-title-orange">Why Now</div>
                        {why_now_html}
                    </div>
                    
                    <!-- Section 4: Recommended Angles -->
                    <div style="margin-bottom: 16px;">
                        <div class="section-title section-title-orange">Recommended Angles</div>
                        {angles_html}
                    </div>
                    
                </td>
            </tr>
        </table>

        <!-- Footer -->
        <div class="footer-section">
            <div style="font-size: 8px; color: #999; text-align: center; font-weight: 500;">
                For BDR internal use only • Generated {_get_date_string()}
            </div>
        </div>
    </body>
    </html>
    """

    # Render PDF to Memory
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
