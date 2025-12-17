"""
Workshop Features Database - Maps pain points to specific platform capabilities

Save this file as: workshop_features.py in your project root directory
"""

WORKSHOP_FEATURES = {
    # Core platform capabilities organized by use case
    'leadership_communication': {
        'name': 'Leadership Communication Hub',
        'features': [
            'Drag-and-drop functionality',
            'Template library',
            'Ghostwriting',
            'Scheduling',
            'Custom built email templates'
        ],
        'pain_points': ['leadership transition', 'new ceo', 'executive communication', 'vision alignment', 'change management'],
        'tier': 'Essential'
    },
    'frontline_mobile': {
        'name': 'Mobile-First Frontline Reach',
        'features': [
            'Mobile/responsive design',
            'SMS',
            'Pages',
            'QR codes',
            'Additional phone numbers for SMS'
        ],
        'pain_points': ['frontline', 'deskless', 'shift workers', 'clinical staff', 'field employees', 'mobile workforce'],
        'tier': 'Essential + SMS Add-on'
    },
    'audience_segmentation': {
        'name': 'Intelligent Audience Targeting',
        'features': [
            'Audience segmentation',
            'Dynamic distribution lists',
            'Filter by department, role, location, etc.',
            'Filter by custom properties',
            'Automated time zone sending'
        ],
        'pain_points': ['multiple locations', 'distributed workforce', 'multi-site', 'geographic spread', 'targeted messaging'],
        'tier': 'Enhanced'
    },
    'hybrid_workforce': {
        'name': 'Hybrid Workforce Suite',
        'features': [
            'Microsoft Teams',
            'Slack',
            'Sharepoint',
            'Workvivo',
            'Shareable URL',
            'Campaign archives'
        ],
        'pain_points': ['hybrid work', 'remote', 'work from home', 'distributed teams', 'flexible work'],
        'tier': 'Essential'
    },
    'integration_ecosystem': {
        'name': 'HR System Integration',
        'features': [
            'Workday',
            'UKG Pro',
            'ADP Workforce Now',
            'SAP SuccessFactors',
            'Oracle',
            'Ceridian Dayforce',
            'Azure Active Directory',
            'Okta',
            'Single Sign On (SSO)'
        ],
        'pain_points': ['workday', 'adp', 'hris integration', 'employee data', 'sso', 'active directory'],
        'tier': 'Premium (HRIS) / Essential (Directory)'
    },
    'analytics_roi': {
        'name': 'Engagement Analytics & ROI',
        'features': [
            'Open, click, read time, and device analytics',
            'Click maps',
            'Account-wide analytics',
            'Campaign tagging & analytics',
            'Monthly email performance summaries',
            'Individual recipient engagement data',
            'Downloadable PDF reports'
        ],
        'pain_points': ['engagement metrics', 'roi', 'analytics', 'measurement', 'reporting', 'data-driven'],
        'tier': 'Essential'
    },
    'multilingual': {
        'name': 'Global Team Communication',
        'features': [
            'Language translation',
            'US/EU/CA-based servers',
            'Automated time zone sending'
        ],
        'pain_points': ['international', 'global', 'multilingual', 'multiple languages', 'language barriers'],
        'tier': 'Premium'
    },
    'change_management': {
        'name': 'Change Management Toolkit',
        'features': [
            'Communications calendar',
            'Campaign management',
            'Template management',
            'Blackout dates'
        ],
        'pain_points': ['acquisition', 'merger', 'reorganization', 'transformation', 'change initiative'],
        'tier': 'Essential (Blackout dates is Premium)'
    },
    'employee_engagement': {
        'name': 'Employee Engagement Tools',
        'features': [
            'Embedded surveys',
            'AI-assisted features',
            'AI content tools',
            'GIPHY integration',
            'Unsplash photo integration'
        ],
        'pain_points': ['engagement', 'retention', 'turnover', 'culture', 'employee experience'],
        'tier': 'Enhanced'
    },
    'rapid_deployment': {
        'name': 'Fast Implementation',
        'features': [
            'Onboarding management',
            'Software training for new users',
            'Dedicated account management',
            'Email support'
        ],
        'pain_points': ['quick setup', 'fast deployment', 'time to value', 'ease of use'],
        'tier': 'Essential'
    },
    'security_compliance': {
        'name': 'Enterprise Security',
        'features': [
            'SOC 2 Type II',
            'GDPR compliant',
            'Penetration testing',
            'Access control',
            'Automatic encrypted backups',
            'Disaster recovery'
        ],
        'pain_points': ['security', 'compliance', 'data protection', 'healthcare', 'financial services', 'regulated'],
        'tier': 'Essential'
    },
    'scale_enterprise': {
        'name': 'Enterprise Scale',
        'features': [
            'Unlimited storage',
            'Unlimited admins',
            'User roles management',
            'Permission management',
            'Unlimited user licenses'
        ],
        'pain_points': ['large organization', '5000+', '10000+', 'enterprise', 'scale'],
        'tier': 'Enhanced/Premium'
    }
}


def match_features_to_company(structured_data):
    """
    Analyzes company data and returns top 3-4 most relevant Workshop features.
    
    Args:
        structured_data: Company research data
        
    Returns:
        List of matched feature dictionaries
    """
    
    # Extract text to analyze
    text_to_analyze = []
    
    # Add snapshot data
    snapshot = structured_data.get('snapshot', {})
    text_to_analyze.append(snapshot.get('industry', '').lower())
    text_to_analyze.append(snapshot.get('size', '').lower())
    text_to_analyze.append(snapshot.get('footprint', '').lower())
    
    for event in snapshot.get('change_events', []):
        if isinstance(event, dict):
            text_to_analyze.append(event.get('event', '').lower())
        else:
            text_to_analyze.append(str(event).lower())
    
    for tech in snapshot.get('tech_stack', []):
        if isinstance(tech, dict):
            text_to_analyze.append(tech.get('tool', '').lower())
        else:
            text_to_analyze.append(str(tech).lower())
    
    # Add why_now data
    for item in structured_data.get('why_now', []):
        if isinstance(item, dict):
            text_to_analyze.append(item.get('title', '').lower())
            text_to_analyze.append(item.get('description', '').lower())
        else:
            text_to_analyze.append(str(item).lower())
    
    # Add persona data
    for persona in structured_data.get('personas', []):
        if isinstance(persona, dict):
            text_to_analyze.append(persona.get('title', '').lower())
            for goal in persona.get('goals', []):
                text_to_analyze.append(str(goal).lower())
            for fear in persona.get('fears', []):
                text_to_analyze.append(str(fear).lower())
    
    # Combine all text
    combined_text = ' '.join(text_to_analyze)
    
    # Score each feature
    feature_scores = {}
    for feature_key, feature_data in WORKSHOP_FEATURES.items():
        score = 0
        matched_keywords = []
        
        for pain_point in feature_data['pain_points']:
            if pain_point in combined_text:
                score += 1
                matched_keywords.append(pain_point)
        
        if score > 0:
            feature_scores[feature_key] = {
                'score': score,
                'data': feature_data,
                'matched_keywords': matched_keywords
            }
    
    # Sort by score and return top matches
    sorted_features = sorted(feature_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    
    # Return top 3-4 features
    top_features = []
    for feature_key, feature_info in sorted_features[:4]:
        top_features.append({
            'key': feature_key,
            'name': feature_info['data']['name'],
            'features': feature_info['data']['features'],
            'tier': feature_info['data']['tier'],
            'relevance_score': feature_info['score'],
            'matched_keywords': feature_info['matched_keywords']
        })
    
    return top_features


def get_competitor_displacement_angle(tech_stack):
    """
    Generates competitive displacement angle if using inferior tools.
    
    Args:
        tech_stack: List of current tools
        
    Returns:
        String with displacement angle or None
    """
    
    displacement_messages = {
        'outlook': 'Replace basic Outlook emails with purpose-built internal comms platform',
        'sharepoint': 'Move beyond SharePoint intranet to engaging, measurable employee communications',
        'teams': 'Complement Microsoft Teams chat with structured, archived company-wide announcements',
        'slack': 'Enhance Slack with formal communications that reach all employees reliably',
        'gmail': 'Upgrade from basic Gmail to professional internal communications platform',
        'mailchimp': 'Replace marketing tools with employee-specific communication platform',
        'constant contact': 'Replace marketing tools with employee-specific communication platform'
    }
    
    if not tech_stack:
        return None
    
    tech_lower = [str(t).lower() if isinstance(t, str) else str(t.get('tool', '')).lower() 
                  for t in tech_stack]
    combined = ' '.join(tech_lower)
    
    for tool, message in displacement_messages.items():
        if tool in combined:
            return message
    
    return None
