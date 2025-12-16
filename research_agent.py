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
    
    # Updated queries: Added 'strategy' to find the high-quality BDR angles
    queries = {
        'general': f"""
            {company_name} company profile headquarters employee count
            fiscal year end date financial calendar investor relations
        """,
        # NEW: Specifically hunting for high-level business drivers
        'strategy': f"""
            {company_name} strategic plan 2025 "digital transformation" 
            "new markets" restructuring expansion "major projects" 
            "capital expenditure" strategy
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
        # SPLIT 2: Focus on Corporate/Executive titles
        'people_corporate': f"""
            {company_name} "VP of Corporate Communications" 
            "Chief Communications Officer" "Director of Corporate Affairs"
            "VP of Communications" "Head of Corporate Communications"
        """,
        'people_linkedin': f"""
            site:linkedin.com/in/ {company_name} "internal communications" OR "corporate communications"
        """
    }
    
    all_sources = []
    
    try:
        for query_type, query in queries.items():
            print(f"  📡 Searching: {query_type}...")
            # Use 5 results normally, 7 for people to ensure we find contacts
            max_res = 7 if 'people' in query_type else 5
            
            results = tavily.search(
                query=query, 
                search_depth="advanced",
                max_results=max_res,
                include_raw_content=False
            )
            
            if results and 'results' in results:
                for r in results['results']:
                    all_sources.append({
                        'title': r.get('title', 'N/A'),
                        'url': r.get('url', ''),
                        'content': r.get('content', ''),
                        'query_type': query_type
                    })
        
        # Build context
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
    
    # SYSTEM PROMPT UPDATED:
    # 1. Prioritize STRATEGIC "Why Now" over trivial news
    # 2. Strict Link/Source URL requirement
    # 3. Targeted Buyer Roles
    
    system_prompt = """You are an expert Account-Based Marketing researcher for Workshop.

    CRITICAL RULES:
    1. **NO HALLUCINATIONS**: If a specific fact isn't found, return "Unknown".
    2. **SOURCE LINKS**: You MUST provide the `source_url` for every data point found.
    
    DATA EXTRACTION TASKS:

    1. **WHY NOW (Strategic Focus)**: 
       - IGNORE: Generic awards, minor conference attendance, or small PR news.
       - PRIORITIZE: 
         * Strategic Shifts (Digital Transformation, Rebranding, M&A)
         * Operational Changes (Return to Office, Layoffs, Hiring Sprees)
         * Market Expansion (New Locations, Major Project Wins)
       - The "Description" must explain *why* this creates a need for Internal Comms (e.g., "Requires aligning distributed teams").

    2. **TARGET BUYERS**: 
       - Find specific Internal Comms or Employee Experience leaders.
       - If no specific Internal Comms role exists, look for VP Corporate Comms or HR Leaders.
       - **Do not** target the CEO unless <100 employees.

    3. **TECH STACK**: 
       - Hunt for Microsoft Teams, SharePoint, Workday, UKG.

    OUTPUT STRUCTURE (JSON ONLY):
    {{
      "snapshot": {{
        "industry": "string",
        "size": "string",
        "location": "string",
        "fiscal_year": {{ "value": "e.g. Ends Dec 31", "source_url": "https://..." }},
        "glassdoor_score": {{ "value": "e.g. 4.2/5", "source_url": "https://..." }},
        "tech_stack": [
          {{ "tool": "Workday", "category": "HRIS", "source_url": "https://..." }}
        ],
        "change_events": [
          {{ "event": "...", "source_url": "https://..." }}
        ]
      }},
      "openers": [
        {{ "label": "The Strategy Hook", "script": "..." }},
        {{ "label": "The Tech Hook", "script": "..." }}
      ],
      "why_now": [
        {{
          "title": "Title (e.g. 'Nuclear Market Expansion')",
          "description": "Description relating to comms needs...",
          "source_url": "https://..."
        }}
      ],
      "personas": [
        {{
          "name": "Jane Doe",
          "role": "Director of Internal Comms",
          "email": "jane.doe@company.com OR 'Unknown'",
          "linkedin_url": "https://linkedin.com/in/...",
          "is_named_person": true,
          "goals": ["..."],
          "fears": ["..."]
        }}
      ],
      "angles": [
        {{
          "title": "Angle Title",
          "description": "...",
          "metric": "..."
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
        return get_fallback_data(company_name, website_url)


def get_default_section(section_name):
    defaults = {
        'snapshot': {
            'industry': 'Unknown', 'size': 'Unknown', 'location': 'Unknown',
            'fiscal_year': {'value': 'Unknown', 'source_url': None},
            'glassdoor_score': {'value': 'Unknown', 'source_url': None},
            'tech_stack': [], 'change_events': []
        },
        'openers': [], 'why_now': [], 'personas': [], 'angles': []
    }
    return defaults.get(section_name, {})


def get_fallback_data(company_name, website_url):
    return {
        'snapshot': {
            'industry': 'Research in progress',
            'size': 'Unknown',
            'location': 'Unknown',
            'fiscal_year': {'value': 'Unknown', 'source_url': None},
            'glassdoor_score': {'value': 'Unknown', 'source_url': None},
            'tech_stack': [],
            'change_events': [{'event': 'Limited info', 'source_url': website_url}]
        },
        'openers': [{'label': 'General', 'script': f'How is {company_name} scaling internal comms?'}],
        'why_now': [{'title': 'Research Needed', 'description': 'Manual check recommended.', 'source_url': website_url}],
        'personas': [{'name': 'Director of Internal Comms', 'role': 'Internal Comms Lead', 'email': 'Unknown', 'is_named_person': False}],
        'angles': [],
        '_metadata': {'company_name': company_name, 'website': website_url, 'sources_count': 0, 'all_sources': []}
    }
