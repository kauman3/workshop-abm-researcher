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
    temperature=0.1,  # Lower temperature for more factual output
    max_tokens=5000,
)


def get_company_data(company_name, website_url):
    """
    Orchestrates comprehensive research with source citations.
    Returns structured JSON with embedded links to sources.
    """
    
    print(f"🕵️ Starting deep research on {company_name}...")
    
    # Multiple targeted searches for better coverage
    queries = {
        'general': f"""
            {company_name} company profile recent news 2024 2025
            headquarters location employee count size
        """,
        'changes': f"""
            {company_name} leadership changes hiring acquisitions
            expansion new initiatives 2024 2025
        """,
        'tech': f"""
            {company_name} technology stack HRIS communication tools
            Workday Slack Microsoft Teams internal communications
        """,
        'linkedin': f"""
            {company_name} LinkedIn company employees job postings
            recent updates organizational changes
        """,
        'culture': f"""
            {company_name} employee experience workplace culture
            internal communications engagement retention
        """
    }
    
    all_sources = []
    search_results = {}
    
    try:
        for query_type, query in queries.items():
            print(f"  📡 Searching: {query_type}...")
            results = tavily.search(
                query=query, 
                search_depth="advanced",
                max_results=5,
                include_raw_content=False
            )
            
            if results and 'results' in results:
                search_results[query_type] = results['results']
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
    
    # Enhanced prompt with strict citation requirements
    system_prompt = """You are an expert Account-Based Marketing researcher for Workshop, an internal communications platform.

CRITICAL RULES - READ CAREFULLY:
1. ONLY include information you can directly cite from the provided sources
2. DO NOT make up or infer information not explicitly stated in sources
3. For EVERY fact, you must include the source number in a "source" field
4. If information is not available, use "Not publicly available" or "Unknown"
5. Return ONLY valid JSON - no markdown, no code blocks

PERSONA INSTRUCTIONS:
- Look for actual named individuals in leadership roles (CEO, CHRO, Head of HR, Head of Internal Comms, Chief People Officer)
- Check LinkedIn mentions, press releases, company announcements
- If you find specific names, use their actual title
- If no specific person found, use generic title like "Head of Internal Communications"

TECH STACK INSTRUCTIONS:
- Only include tools explicitly mentioned in sources
- Look for mentions of: HRIS (Workday, ADP, SuccessFactors), comms tools (Slack, Teams, Firstup), intranets

CHANGE EVENTS:
- Must be from last 12 months
- Include specific dates/timeframes when available
- Focus on: leadership changes, hiring spikes, acquisitions, expansions, funding rounds

WHY NOW:
- Connect real company changes to internal comms challenges
- Be specific about how Workshop helps with their actual situation
- Include metrics or scale indicators when available

CHARACTER LIMITS:
- snapshot.industry: 50 chars
- snapshot.size: 35 chars  
- snapshot.location: 50 chars
- snapshot.footprint: 70 chars
- snapshot.change_events: max 4 items, 130 chars each (include source)
- why_now items: max 3, description 160 chars (include source)
- persona: 1-2 personas with specific titles
- persona goals/fears: 2-3 each, 70-90 chars
- angles: 2 angles, description 220 chars max

OUTPUT STRUCTURE:
{{
  "snapshot": {{
    "industry": "string [40-50 chars]",
    "size": "string [30-35 chars]",
    "location": "string [40-50 chars]",
    "footprint": "string [60-70 chars]",
    "tech_stack": [
      {{"tool": "Workday", "source": 3}},
      {{"tool": "Microsoft Teams", "source": 5}}
    ],
    "change_events": [
      {{
        "event": "Event description [130 chars]",
        "source": 2,
        "source_url": "https://..."
      }}
    ]
  }},
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
      "title": "Actual Name & Title (e.g., 'Jane Smith, VP Internal Comms') OR Generic Title",
      "is_named_person": true/false,
      "goals": ["goal 1 [70-90 chars]", "goal 2"],
      "fears": ["fear 1 [70-90 chars]", "fear 2"],
      "source": 4
    }}
  ],
  "angles": [
    {{
      "title": "Angle Title [40 chars]",
      "description": "How Workshop solves their specific challenge [220 chars]",
      "metric": "Target outcome [60 chars]",
      "sources": [1, 3]
    }}
  ]
}}

REMEMBER: If you cannot find information, mark it as "Not publicly available" rather than making something up."""

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
            'footprint': 'Unknown',
            'tech_stack': [],
            'change_events': []
        },
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
            'footprint': 'Unknown',
            'tech_stack': [],
            'change_events': [
                {
                    'event': 'Limited public information available',
                    'source': None,
                    'source_url': website_url
                }
            ]
        },
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
                'title': 'Head of Internal Communications',
                'is_named_person': False,
                'goals': [
                    'Improve employee engagement and reach',
                    'Streamline internal messaging platforms'
                ],
                'fears': [
                    'Low adoption of communication tools',
                    'Fragmented employee experience'
                ],
                'source': None
            }
        ],
        'angles': [
            {
                'title': 'Unified Internal Communications',
                'description': 'Workshop provides a single platform for all internal communications, replacing fragmented tools and improving employee reach and engagement.',
                'metric': 'Typical customers see 40%+ increase in message engagement',
                'sources': []
            }
        ],
        '_metadata': {
            'company_name': company_name,
            'website': website_url,
            'sources_count': 0,
            'all_sources': []
        }
    }
