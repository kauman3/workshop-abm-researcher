import os
import json
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

tavily_api_key = os.environ.get("TAVILY_API_KEY")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY not found in environment variables.")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables.")

tavily = TavilyClient(api_key=tavily_api_key)
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.0,  # Zero temperature for maximum factuality
    max_tokens=5000,
)


def get_company_data(company_name, website_url):
    """
    Orchestrates comprehensive research with source citations.
    Returns structured JSON with embedded links to sources.
    """
    
    print(f"🕵️ Starting deep research on {company_name}...")
    
    # Updated queries: Split "contacts" into specific targeted searches to improve hit rate
    queries = {
        'general': f"""
            {company_name} company profile headquarters employee count
            fiscal year end date financial calendar investor relations
        """,
        'changes': f"""
            {company_name} leadership changes hiring acquisitions
            expansion new initiatives 2024 2025
        """,
        'tech': f"""
            {company_name} technology stack HRIS Workday ADP UKG
            internal communications tools Microsoft Teams SharePoint Slack
        """,
        'culture': f"""
            {company_name} glassdoor rating culture score reviews
            employee sentiment benefits perks "best places to work"
        """,
        # SPLIT 1: Focus on Internal/Employee specific titles
        'people_internal': f"""
            {company_name} "Director of Internal Communications" 
            "Head of Internal Comms" "Manager of Employee Communications"
            "Director of Employee Experience" "Internal Communications Manager"
        """,
        # SPLIT 2: Focus on Corporate/Executive titles (often covering Internal)
        'people_corporate': f"""
            {company_name} "VP of Corporate Communications" 
            "Chief Communications Officer" "Director of Corporate Affairs"
            "VP of Communications" "Head of Corporate Communications"
        """,
        # SPLIT 3: LinkedIn specific targeting
        'people_linkedin': f"""
            site:linkedin.com/in/ {company_name} "internal communications" OR "corporate communications"
        """
    }
    
    all_sources = []
    
    try:
        for query_type, query in queries.items():
            print(f"  📡 Searching: {query_type}...")
            # Increased result count slightly for people searches to dig deeper
            max_res = 7 if 'people' in query_type else 5
            
            results = tavily.search(
                query=query, 
                search_depth="advanced",
                max_results=max_res,
                include_raw_content=False
            )
            
            if results and 'results' in results:
                # Collect all sources with URLs
                for r in results['results']:
                    all_sources.append({
                        'title': r.get('title', 'N/A'),
                        'url': r.get('url', ''),
                        'content': r.get('content', ''),
                        'query_type': query_type
                    })
        
        # Build comprehensive context with source tracking
        context_with_sources = ""
        for idx, source in enumerate(all_sources, 1):
            context_with_sources += f"\n\n[SOURCE {idx}]\n"
            context_with_sources += f"URL: {source['url']}\n"
            context_with_sources += f"Title: {source['title']}\n"
            context_with_sources += f"Type: {source['query_type']}\n"
            context_with_sources += f"Content: {source['content']}\n"
        
    except Exception as e:
        print(f"⚠️ Error during research: {e}")
        context_with_sources = f"Limited information available for {company_name}."
        all_sources = []
    
    # Enhanced prompt with strict Role targeting and Anti-Hallucination
    system_prompt = """You are an expert Account-Based Marketing researcher for Workshop, an internal communications platform.

CRITICAL RULES - READ CAREFULLY:
1. **NO HALLUCINATIONS**: If you cannot find a specific fact (like Fiscal Year or a specific Name), return "Unknown". DO NOT GUESS.
2. **SOURCE CITATION**: For EVERY fact, you must include the source number in a "source" field.
3. **EMAIL PRECISION**: Only provide an email if you find it explicitly OR find a clear company email pattern (e.g. "first.last@domain.com") to apply. Mark as "Unknown" otherwise.

SPECIFIC DATA EXTRACTION TASKS:

1. **FISCAL YEAR**: Look for "Fiscal year ends in..." or financial report dates.
2. **GLASSDOOR/CULTURE**: Look for specific 0-5 ratings or "Best Place to Work" awards.
3. **TECH STACK**: Specifically look for HRIS (Workday, UKG), Intranets (SharePoint), and Comms (Teams, Slack).
4. **TARGET BUYERS (Crucial)**: 
    - **DO NOT** target the CEO or COO unless the company is very small (<100 employees).
    - **FIND** roles that are responsible for internal communications.
    - **PRIORITY ORDER**:
        1. Director/VP of Internal Communications
        2. Internal Comms Manager / Lead
        3. Director/VP of Corporate Communications (if no dedicated Internal role found)
        4. Chief Communications Officer (CCO)
        5. Head of Employee Experience
    - If you find a name, list it. If not, list the *Job Title* as the name and set 'is_named_person' to false.

OUTPUT STRUCTURE (JSON ONLY):
{{
  "snapshot": {{
    "industry": "string [40 chars]",
    "size": "string [30 chars]",
    "location": "string [40 chars]",
    "fiscal_year": "string (e.g., 'Ends Dec 31') or 'Unknown'",
    "glassdoor_score": "string (e.g., '3.8/5') or 'Unknown'",
    "tech_stack": [
      {{"tool": "Workday", "category": "HRIS", "source": 3}},
      {{"tool": "Microsoft Teams", "category": "Comms", "source": 5}}
    ],
    "change_events": [
      {{
        "event": "Event description [130 chars]",
        "source": 2,
        "source_url": "https://..."
      }}
    ]
  }},
  "openers": [
    {{
        "label": "The Leadership Hook",
        "script": "Script connecting a recent leader change to comms strategy..."
    }},
    {{
        "label": "The Integration Hook",
        "script": "Script connecting their specific Tech Stack to Workshop..."
    }}
  ],
  "why_now": [
    {{
      "title": "Title [30 chars]",
      "description": "Description [160 chars]",
      "source": 1,
      "source_url": "https://..."
    }}
  ],
  "personas": [
    {{
      "name": "Jane Doe OR 'Director of Internal Comms'",
      "role": "Job Title",
      "email": "jane.doe@company.com OR 'Unknown'",
      "is_named_person": true,
      "goals": ["goal 1", "goal 2"],
      "fears": ["fear 1", "fear 2"],
      "source": 4
    }}
  ],
  "angles": [
    {{
      "title": "Angle Title [40 chars]",
      "description": "How Workshop solves their specific challenge",
      "metric": "Target outcome [60 chars]",
      "sources": [1, 3]
    }}
  ]
}}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", """Target Company: {company_name}
Website: {website}

Research with Sources:
{context}

Generate the structured JSON profile with accurate source citations:""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    print("🧠 Synthesizing research with citations...")
    json_output = chain.invoke({
        "company_name": company_name,
        "website": website_url,
        "context": context_with_sources
    })
    
    # Parse and validate JSON
    try:
        clean_json = json_output.strip()
        if clean_json.startswith('```'):
            lines = clean_json.split('\n')
            clean_json = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
        
        structured_data = json.loads(clean_json)
        
        # Validate required fields
        required_keys = ['snapshot', 'why_now', 'personas', 'angles']
        for key in required_keys:
            if key not in structured_data:
                print(f"⚠️ Missing required key: {key}")
                structured_data[key] = get_default_section(key)
        
        # Add metadata
        structured_data['_metadata'] = {
            'company_name': company_name,
            'website': website_url,
            'sources_count': len(all_sources),
            'all_sources': all_sources
        }
        
        print(f"✅ Research complete - {len(all_sources)} sources analyzed")
        return structured_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Raw output preview: {json_output[:300]}...")
        return get_fallback_data(company_name, website_url)


def get_default_section(section_name):
    """Returns default empty structure for missing sections"""
    defaults = {
        'snapshot': {
            'industry': 'Unknown',
            'size': 'Unknown',
            'location': 'Unknown',
            'fiscal_year': 'Unknown',
            'glassdoor_score': 'Unknown',
            'tech_stack': [],
            'change_events': []
        },
        'openers': [],
        'why_now': [],
        'personas': [],
        'angles': []
    }
    return defaults.get(section_name, {})


def get_fallback_data(company_name, website_url):
    """Returns minimal valid structure if parsing fails completely"""
    return {
        'snapshot': {
            'industry': 'Research in progress',
            'size': 'Unknown',
            'location': 'Unknown',
            'fiscal_year': 'Unknown',
            'glassdoor_score': 'Unknown',
            'tech_stack': [],
            'change_events': [
                {
                    'event': 'Limited public information available',
                    'source': None,
                    'source_url': website_url
                }
            ]
        },
        'openers': [
            {
                'label': 'General Outreach',
                'script': f'I noticed {company_name} is growing—how are you scaling your internal comms?'
            }
        ],
        'why_now': [
            {
                'title': 'Additional research needed',
                'description': f'Manual research recommended for {company_name}',
                'source': None,
                'source_url': website_url
            }
        ],
        'personas': [
            {
                'name': 'Director of Internal Communications',
                'role': 'Internal Comms Lead',
                'email': 'Unknown',
                'is_named_person': False,
                'goals': ['Improve engagement', 'Streamline tools'],
                'fears': ['Low adoption', 'Noise'],
                'source': None
            }
        ],
        'angles': [],
        '_metadata': {
            'company_name': company_name,
            'website': website_url,
            'sources_count': 0,
            'all_sources': []
        }
    }
