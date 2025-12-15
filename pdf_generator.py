from xhtml2pdf import pisa
from io import BytesIO
import re

def create_styled_pdf(structured_data, company_name):
    """
    Converts structured data into a branded Workshop PDF using xhtml2pdf.
    
    Args:
        structured_data: Dict with keys: snapshot, why_now, personas, angles
        company_name: String name of the target company
    """
    
    # Extract sections from structured data
    snapshot = structured_data.get('snapshot', {})
    why_now = structured_data.get('why_now', [])
    personas = structured_data.get('personas', [])
    angles = structured_data.get('angles', [])
    
    # Build snapshot HTML
    snapshot_html = f"""
        <table style="width: 100%; margin-bottom: 12px;">
            <tr>
                <td style="width: 48%; padding-right: 8px; vertical-align: top;">
                    <span style="color: #666; font-size: 10px;">Industry:</span><br/>
                    <span style="font-weight: 600; color: #1a1a1a;">{snapshot.get('industry', 'N/A')}</span>
                </td>
                <td style="width: 48%; padding-left: 8px; vertical-align: top;">
                    <span style="color: #666; font-size: 10px;">Size:</span><br/>
                    <span style="font-weight: 600; color: #1a1a1a;">{snapshot.get('size', 'N/A')}</span>
                </td>
            </tr>
            <tr>
                <td style="width: 48%; padding-right: 8px; padding-top: 8px; vertical-align: top;">
                    <span style="color: #666; font-size: 10px;">Location:</span><br/>
                    <span style="font-weight: 600; color: #1a1a1a;">{snapshot.get('location', 'N/A')}</span>
                </td>
                <td style="width: 48%; padding-left: 8px; padding-top: 8px; vertical-align: top;">
                    <span style="color: #666; font-size: 10px;">Footprint:</span><br/>
                    <span style="font-weight: 600; color: #1a1a1a;">{snapshot.get('footprint', 'N/A')}</span>
                </td>
            </tr>
        </table>
        
        <div style="border-top: 1px solid #e5e5e5; padding-top: 8px; margin-bottom: 8px;">
            <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 6px;">CURRENT TECH STACK</div>
            <div style="font-size: 10px;">
                {' '.join([f'<span style="background-color: #f3f4f6; padding: 3px 8px; margin-right: 4px; border-radius: 3px; display: inline-block; margin-bottom: 3px;">{tech}</span>' for tech in snapshot.get('tech_stack', [])])}
            </div>
        </div>
        
        <div style="border-top: 1px solid #e5e5e5; padding-top: 8px;">
            <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 6px;">RECENT CHANGE EVENTS</div>
            <ul style="margin: 0; padding-left: 15px; font-size: 10px; line-height: 1.4;">
                {''.join([f'<li style="margin-bottom: 3px; color: #374151;">{event}</li>' for event in snapshot.get('change_events', [])])}
            </ul>
        </div>
    """
    
    # Build Why Now HTML
    why_now_html = '<ul style="margin: 0; padding-left: 0; list-style: none; font-size: 11px;">'
    for item in why_now[:3]:  # Max 3 items
        why_now_html += f'''
            <li style="margin-bottom: 10px; padding-left: 18px; position: relative; line-height: 1.5;">
                <span style="position: absolute; left: 0; top: 2px; color: #FF6B35; font-weight: bold;">›</span>
                <span style="font-weight: 600; color: #1a1a1a;">{item.get('title', '')}:</span>
                <span style="color: #4b5563;"> {item.get('description', '')}</span>
            </li>
        '''
    why_now_html += '</ul>'
    
    # Build Personas HTML
    personas_html = ''
    for persona in personas[:2]:  # Max 2 personas
        goals_html = ''.join([f'<li style="margin-bottom: 2px;">• {goal}</li>' for goal in persona.get('goals', [])])
        fears_html = ''.join([f'<li style="margin-bottom: 2px;">• {fear}</li>' for fear in persona.get('fears', [])])
        
        personas_html += f'''
            <div style="background-color: #EFF6FF; border-left: 4px solid #2D5BFF; padding: 10px; margin-bottom: 10px; border-radius: 4px;">
                <div style="font-weight: 600; color: #1a1a1a; font-size: 11px; margin-bottom: 6px;">{persona.get('title', '')}</div>
                <div style="font-size: 10px;">
                    <span style="color: #666; font-weight: 600;">Goals:</span>
                    <ul style="margin: 3px 0 6px 0; padding-left: 15px; color: #374151;">
                        {goals_html}
                    </ul>
                    <span style="color: #666; font-weight: 600;">Fears:</span>
                    <ul style="margin: 3px 0 0 0; padding-left: 15px; color: #374151;">
                        {fears_html}
                    </ul>
                </div>
            </div>
        '''
    
    # Build Angles HTML
    angles_html = ''
    for angle in angles[:2]:  # Max 2 angles
        angles_html += f'''
            <div style="border-left: 4px solid #2D5BFF; padding-left: 10px; margin-bottom: 12px;">
                <div style="font-weight: 600; color: #1a1a1a; font-size: 11px; margin-bottom: 4px;">{angle.get('title', '')}</div>
                <p style="font-size: 10px; color: #374151; line-height: 1.5; margin: 0 0 6px 0;">{angle.get('description', '')}</p>
                <div style="font-size: 9px;">
                    <span style="font-weight: 600; color: #666;">Key metric:</span>
                    <span style="color: #374151;"> {angle.get('metric', '')}</span>
                </div>
            </div>
        '''
    
    # Add proof point if provided
    proof = structured_data.get('proof_point', {})
    if proof:
        angles_html += f'''
            <div style="background-color: #f9fafb; border: 1px solid #e5e7eb; padding: 10px; margin-top: 12px; border-radius: 4px;">
                <div style="color: #666; font-size: 9px; font-weight: 600; margin-bottom: 4px;">SIMILAR CUSTOMER</div>
                <div style="font-weight: 600; color: #1a1a1a; font-size: 11px; margin-bottom: 2px;">{proof.get('company', '')}</div>
                <div style="font-size: 9px; color: #666; margin-bottom: 4px;">{proof.get('context', '')}</div>
                <div style="font-size: 10px; color: #374151; font-style: italic;">"{proof.get('quote', '')}"</div>
            </div>
        '''
    
    # Complete HTML template
    source_html = f"""
    <html>
    <head>
        <style>
            @page {{
                size: letter;
                margin: 0.75in;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 11px;
                color: #1a1a1a;
                line-height: 1.4;
            }}
            .header-border {{
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 12px;
                margin-bottom: 18px;
            }}
            .section-header {{
                color: #1a1a1a;
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 10px;
                display: block;
            }}
            .icon-header {{
                color: #2D5BFF;
                margin-right: 4px;
            }}
            .icon-header-orange {{
                color: #FF6B35;
                margin-right: 4px;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <div class="header-border">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 70%;">
                        <div style="color: #2D5BFF; font-size: 18px; font-weight: bold; margin-bottom: 8px;">Workshop</div>
                        <div style="font-size: 22px; font-weight: bold; color: #1a1a1a; margin-bottom: 4px;">{company_name}</div>
                        <div style="font-size: 11px; color: #666;">Account playbook for internal communications transformation</div>
                    </td>
                    <td style="width: 30%; text-align: right; vertical-align: bottom;">
                        <div style="font-size: 9px; color: #999;">Internal Use Only</div>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Two Column Layout -->
        <table style="width: 100%;">
            <tr>
                <td style="width: 48%; vertical-align: top; padding-right: 12px;">
                    <!-- LEFT COLUMN -->
                    
                    <!-- Section 1: Company Snapshot -->
                    <div style="margin-bottom: 20px;">
                        <span class="section-header">
                            <span class="icon-header">■</span> Company Snapshot
                        </span>
                        {snapshot_html}
                    </div>
                    
                    <!-- Section 3: Key Personas -->
                    <div style="margin-bottom: 20px;">
                        <span class="section-header">
                            <span class="icon-header">■</span> Key Personas
                        </span>
                        {personas_html}
                    </div>
                    
                </td>
                <td style="width: 48%; vertical-align: top; padding-left: 12px;">
                    <!-- RIGHT COLUMN -->
                    
                    <!-- Section 2: Why Now -->
                    <div style="margin-bottom: 20px;">
                        <span class="section-header">
                            <span class="icon-header-orange">■</span> Why Now
                        </span>
                        {why_now_html}
                    </div>
                    
                    <!-- Section 4: Recommended Angles -->
                    <div style="margin-bottom: 20px;">
                        <span class="section-header">
                            <span class="icon-header-orange">■</span> Recommended Angles
                        </span>
                        {angles_html}
                    </div>
                    
                </td>
            </tr>
        </table>

        <!-- Footer -->
        <div style="border-top: 2px solid #e5e7eb; padding-top: 10px; margin-top: 18px; text-align: center;">
            <div style="font-size: 9px; color: #999;">
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
    from datetime import datetime
    return datetime.now().strftime("%B %d, %Y")


# Example usage structure that matches the Nebraska Medicine data
def structure_research_output(raw_markdown_report):
    """
    Converts the LLM's markdown output into the structured format needed by create_styled_pdf.
    This should be called in your app.py after getting the report from get_company_data().
    
    You'll need to prompt your LLM to output in this structured format, or parse the markdown here.
    """
    
    # This is a template - you'll need to adjust based on your actual LLM output
    structured = {
        'snapshot': {
            'industry': 'Healthcare (Academic)',
            'size': '9,000-10,000 employees',
            'location': 'Metro Omaha, NE',
            'footprint': '2 hospitals, 70+ clinics',
            'tech_stack': ['Firstup', 'ServiceNow', 'Microsoft', 'Workday'],
            'change_events': [
                'New CEO (Jul 2024): Dr. Michael Ash, ex-Cerner/Oracle Health CMO',
                'New employer brand: "Together. Extraordinary." culture campaign',
                'Retention wins: 16% ↓ voluntary turnover, 22% ↑ external hires YoY'
            ]
        },
        'why_now': [
            {
                'title': 'Leadership transition urgency',
                'description': 'New CEO with healthcare tech background needs seamless comms to align 9,000+ employees'
            },
            {
                'title': 'Frontline reach gap',
                'description': '60% of staff lack regular computer access; Firstup adoption at 90% but integration gaps remain'
            },
            {
                'title': 'Retention momentum at risk',
                'description': 'Recent gains (16% ↓ turnover) need sustained engagement during org change'
            }
        ],
        'personas': [
            {
                'title': 'Internal Comms Lead',
                'goals': [
                    'Sustain 90% Firstup adoption momentum',
                    'Align workforce around new CEO vision'
                ],
                'fears': [
                    'Losing engagement during leadership transition',
                    "Can't reach 60% frontline workers effectively"
                ]
            },
            {
                'title': 'HR Communications Director',
                'goals': [
                    'Prove ROI on comms through analytics',
                    'Reduce silos across HR, Ops, Marketing'
                ],
                'fears': [
                    'Fragmented messaging across multiple platforms',
                    'Turnover gains reverse if comms fails to reinforce culture'
                ]
            }
        ],
        'angles': [
            {
                'title': 'Unified Frontline Engagement During Transition',
                'description': 'Consolidate fragmented comms into role-based messaging hub reaching all employees—including 60% frontline. Sustain turnover reduction and accelerate alignment as Dr. Ash\'s priorities roll out.',
                'metric': 'Maintain 16% voluntary turnover reduction during change'
            },
            {
                'title': 'Data-Driven Comms for Healthcare Scale',
                'description': 'Integrate with existing stack (Workday, ServiceNow) for analytics-backed messaging by role/location. New CEO\'s tech background means leadership values measurable comms impact on retention and onboarding.',
                'metric': 'Move from 90% adoption to measurable business outcomes'
            }
        ],
        'proof_point': {
            'company': '[Healthcare System Name]',
            'context': '12,000 employees, multi-state academic health network',
            'quote': 'Workshop helped us reach dispersed clinical teams and cut first-year turnover by 18% during our merger integration.'
        }
    }
    
    return structured
