import os
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables from .env file
load_dotenv()

# 1. SETUP: Load Keys (Ensure these are in your environment variables or .env file)
tavily_api_key = os.environ.get("TAVILY_API_KEY")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY not found in environment variables. Please set it in your .env file.")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables. Please set it in your .env file.")

tavily = TavilyClient(api_key=tavily_api_key)
llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0.2,
    max_tokens=2000,
    # timeout=None,
    # max_retries=2,
)


def get_company_data(company_name, website_url):
    """
    Orchestrates the research process:
    1. Search for recent news and firmographics.
    2. Search for tech stack specifically.
    3. Synthesize into the required JSON structure.
    """
    
    print(f"🕵️  Starting research on {company_name}...")
    
    # --- ACTION 1: GATHER CONTEXT (The "Eyes") ---
    # We perform two distinct searches to ensure we get depth.
    
    # Query A: General "Why Now" & Firmographics
    query_general = f"""
    Research {company_name} ({website_url}). 
    Find:
    1. Recent "change events" in the last 6 months (hiring spikes, leadership changes, acquisitions, expansions).
    2. Accurate headquarters location and employee count.
    3. Their core industry and value proposition.
    """
    
    # Query B: Tech Stack Specifics
    query_tech = f"""
    What software and tech stack does {company_name} use? 
    Look for HRIS, internal comms tools (Slack, Microsoft Teams, SharePoint), 
    or employee engagement platforms.
    """
    
    try:
        results_gen = tavily.search(query=query_general, search_depth="advanced")
        results_tech = tavily.search(query=query_tech, search_depth="advanced")
        
        # Extract relevant text from Tavily results
        # Tavily returns a dict with 'results' containing list of dicts with 'content'
        general_text = ""
        if results_gen and 'results' in results_gen:
            general_text = "\n\n".join([
                f"Source: {r.get('title', 'N/A')}\n{r.get('content', '')}" 
                for r in results_gen['results'][:5]  # Limit to top 5 results
            ])
        
        tech_text = ""
        if results_tech and 'results' in results_tech:
            tech_text = "\n\n".join([
                f"Source: {r.get('title', 'N/A')}\n{r.get('content', '')}" 
                for r in results_tech['results'][:5]  # Limit to top 5 results
            ])
        
        raw_context = f"GENERAL INFO:\n{general_text}\n\nTECH STACK CLUES:\n{tech_text}"
        
    except Exception as e:
        print(f"⚠️  Error during research: {e}")
        raw_context = f"Limited information available for {company_name}. Error: {str(e)}"
    
    # --- ACTION 2: ANALYZE & FORMAT (The "Brain") ---
    # We prompt the LLM to map this chaos into the 4 rigid sections required by the brief.
    system_prompt = """
    You are an expert Account-Based Marketing strategist. 
    Analyze the provided search results for the target company and generate a structured profile.
    
    Your output must perfectly map to these 4 sections:
    1. SNAPSHOT: Industry, Size, Location, Tech Stack Hints, Notable Change Events.
    2. WHY NOW: 2-3 bullets connecting their recent news/changes to internal communication challenges.
    3. PERSONA MAP: Identify the "Internal Comms" or "HR" leader. Guess their goals and fears based on the company context.
    4. ANGLES: 2 specific value propositions for "Workshop" (an internal email/comms platform) that address their specific situation.
    Return valid Markdown. Use bolding for key metrics.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Target Company: {company_name}\n\nContext Found:\n{context}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    print("🧠 Synthesizing report...")
    report = chain.invoke({"company_name": company_name, "context": raw_context})
    
    return report


# Quick Test (Uncomment to test in terminal)
# if __name__ == "__main__":
#     print(get_company_data("Kiewit", "https://www.kiewit.com/"))

