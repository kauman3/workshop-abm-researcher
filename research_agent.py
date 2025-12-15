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
    model="claude-sonnet-4-20250514",  # Using Sonnet for better structured output
    temperature=0.2,
    max_tokens=4000,
)


def get_company_data(company_name, website_url):
    """
    Orchestrates research and returns structured JSON for PDF generation.
    """
    
    print(f"🕵️ Starting research on {company_name}...")
    
    # Search queries
    query_general = f"""
    Research {company_name} ({website_url}). 
    Find:
    1. Recent "change events" in the last 6 months (hiring spikes, leadership changes, acquisitions, expansions, new initiatives).
    2. Accurate headquarters location, employee count, and geographic footprint.
    3. Their core industry and business model.
    4. Any recent challenges, growth signals, or organizational changes.
    """
    
    query_tech = f"""
    What internal communication tools and HR technology does {company_name} use? 
    Look for: HRIS (Workday, ADP, etc.), communication platforms (Slack, Microsoft Teams, SharePoint, Firstup), 
    employee engagement tools, or intranet solutions.
    """
    
    try:
        results_gen = tavily.search(query=query_general, search_depth="advanced")
        results_tech = tavily.search(query=query_tech, search_depth="advanced")
        
        general_text = ""
        if results_gen and 'results' in results_gen:
            general_text = "\n\n".join([
                f"Source: {r.get('title', 'N/A')}\n{r.get('content', '')}" 
                for r in results_gen['results'][:6]
            ])
        
        tech_text = ""
        if results_tech and 'results' in results_tech:
            tech_text = "\n\n".join([
                f"Source: {r.get('title', 'N/A')}\n{r.get('content', '')}" 
                for r in results_tech['results'][:4]
            ])
        
        raw_context = f"COMPANY INFO:\n{general_text}\n\nTECH STACK:\n{tech_text}"
        
    except Exception as e:
        print(f"⚠️ Error during research: {e}")
        raw_context = f"Limited information available for {company_name}."
    
    # Structured prompt for JSON output
    system_prompt = """You are an expert Account-Based Marketing researcher for Workshop, an internal communications platform.

Analyze the provided research and create a structured profile for BDR outreach.

OUTPUT RULES:
1. Return ONLY valid JSON - no markdown formatting, no code blocks, no extra text
2. Follow the exact structure provided in the example
3. Be concise - respect character limits for each field
4. Focus on internal communications pain points and Workshop relevance
5. If information is missing, make educated inferences based on industry/size

CHARACTER LIMITS (STRICT):
- snapshot.industry: 40 chars
- snapshot.size: 30 chars  
- snapshot.location: 50 chars
- snapshot.footprint: 60 chars
- snapshot.change_events: max 3 items, 120 chars each
- why_now items: max 3, description 140 chars each
- persona goals/fears: 2 each, 60-80 chars
- angle descriptions: 200 chars max
- proof quote: 100 chars max

STRUCTURE EXAMPLE:
{{
  "snapshot": {{
    "industry": "Healthcare (Academic)",
    "size": "9,000-10,000 employees",
    "location": "Metro Omaha, NE",
    "footprint": "2 hospitals, 70+ clinics",
    "tech_stack": ["Firstup", "ServiceNow", "Microsoft"],
    "change_events": [
      "New CEO (Jul 2024): Dr. Michael Ash, ex-Cerner CMO",
      "Employer brand refresh: 'Together. Extraordinary.' campaign",
      "16% decrease voluntary turnover YoY"
    ]
  }},
  "why_now": [
    {{
      "title": "Leadership transition urgency",
      "description": "New CEO with healthcare tech background needs seamless comms to align 9,000+ employees"
    }},
    {{
      "title": "Frontline reach gap",
      "description": "60% of staff lack regular computer access; existing tools show integration gaps"
    }}
  ],
  "personas": [
    {{
      "title": "Internal Comms Lead",
      "goals": ["Sustain adoption momentum", "Align workforce around new vision"],
      "fears": ["Losing engagement during transition", "Can't reach frontline workers"]
    }}
  ],
  "angles": [
    {{
      "title": "Unified Frontline Engagement",
      "description": "Consolidate fragmented comms into role-based hub reaching all employees. Sustain retention gains during organizational change.",
      "metric": "Maintain 16% voluntary turnover reduction"
    }}
  ],
  "proof_point": {{
    "company": "[Similar Healthcare System]",
    "context": "10,000 employees, regional network",
    "quote": "Cut first-year turnover by 18% during merger integration"
  }}
}}

Remember: Output ONLY the JSON object, nothing else."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Target Company: {company_name}\n\nResearch Findings:\n{context}\n\nGenerate the structured JSON profile:")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    print("🧠 Synthesizing structured profile...")
    json_output = chain.invoke({"company_name": company_name, "context": raw_context})
    
    # Parse and validate JSON
    try:
        # Remove any markdown code blocks if present
        clean_json = json_output.strip()
        if clean_json.startswith('```'):
            clean_json = '\n'.join(clean_json.split('\n')[1:-1])
        
        structured_data = json.loads(clean_json)
        
        # Validate required fields exist
        required_keys = ['snapshot', 'why_now', 'personas', 'angles']
        for key in required_keys:
            if key not in structured_data:
                print(f"⚠️ Missing required key: {key}")
                structured_data[key] = get_default_section(key)
        
        print("✅ Structured data generated successfully")
        return structured_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Raw output: {json_output[:200]}...")
        return get_fallback_data(company_name)


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
        'angles': [],
        'proof_point': {}
    }
    return defaults.get(section_name, {})


def get_fallback_data(company_name):
    """Returns minimal valid structure if parsing fails"""
    return {
        'snapshot': {
            'industry': 'Research in progress',
            'size': 'Unknown',
            'location': 'Unknown',
            'footprint': 'Unknown',
            'tech_stack': [],
            'change_events': ['Limited public information available']
        },
        'why_now': [
            {
                'title': 'Research needed',
                'description': f'Additional research required for {company_name}'
            }
        ],
        'personas': [
            {
                'title': 'Internal Communications Leader',
                'goals': ['Improve employee engagement', 'Streamline internal messaging'],
                'fears': ['Scattered tools and platforms', 'Low adoption rates']
            }
        ],
        'angles': [
            {
                'title': 'Unified Communications Platform',
                'description': 'Workshop provides a single platform for all internal communications, replacing fragmented tools and improving reach.',
                'metric': 'Typical customers see 40%+ increase in engagement'
            }
        ],
        'proof_point': {
            'company': 'Similar Enterprise',
            'context': 'Multi-location organization',
            'quote': 'Workshop transformed how we reach our distributed workforce'
        }
    }
