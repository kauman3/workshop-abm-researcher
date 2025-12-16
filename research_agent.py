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
    temperature=0.0,
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
        'strategy': f"""
            {company_name} strategic plan 2025 "digital transformation" 
            "new markets" restructuring expansion "major projects" 
            "capital expenditure" strategy
        """,
        # UPDATED TECH QUERY: Focuses on evidence (jobs, blogs, case studies) to avoid generic links
        'tech': f"""
            "{company_name}" "uses" "tech stack" (Workday OR "Microsoft Teams" OR SharePoint OR Slack OR UKG)
            site:lever.co OR site:greenhouse.io OR site:workday.com OR site:{website_url} OR site:stackshare.io "careers" "job description"
        """,
        'culture': f"""
            {company_name} glassdoor rating culture score reviews
            employee sentiment benefits perks "best places to work"
        """,
        'people_internal': f"""
            {company_name} "Director of Internal Communications" 
            "Head of Internal Comms" "Manager of Employee Communications"
            "Director of Employee Experience" "Internal Communications Manager"
        """,
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
    
    # SYSTEM PROMPT UPDATED WITH LIMITS AND SOURCE RULES
    system_prompt = """You are an expert Account-Based Marketing researcher for Workshop.

    CRITICAL RULES:
    1. **NO HALLUCINATIONS**: If a specific fact isn't found, return "Unknown".
    2. **SOURCE LINKS**: You MUST provide the `source_url` for every data point found.
    
    DATA EXTRACTION TASKS:

    1. **WHY NOW (Strategic Focus)**: 
       - **LIMIT**: Output exactly TWO (2) high-impact strategic reasons. No more.
       - **CRITERIA**: Prioritize Strategic Shifts, M&A, or Major Projects over awards.

    2. **TARGET BUYERS**: 
       - Find specific Internal Comms or Employee Experience leaders.
       - **Do not** target the CEO unless <100 employees.

    3. **TECH STACK VERIFICATION**: 
       - **STRICT SOURCE RULE**: The `source_url` for a tool MUST be a specific page proving usage (e.g., a Job Listing for "HRIS Admin", a Case Study, or an Engineering Blog post).
       - **REJECT**: Generic homepages (e.g., "www.slack.com") or generic software directories.
       - **SEARCH**: Look for Microsoft Teams, SharePoint, Workday, UKG.

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
        }},
        {{
          "title": "Title 2",
          "description": "...",
          "source_url": "..."
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
