# Workshop ABM One-Pager Generator

A proof-of-concept system that generates branded Account-Based Marketing one-pagers for target companies. Built for Business Development Representatives (BDRs) to quickly create personalized outreach materials.

## Architecture

This project is built in 3 logical layers:

1. **The Engine** (`research_agent.py`): Web research and data synthesis using Tavily and LLM
2. **The Interface** (`app.py`): Streamlit frontend for BDRs
3. **The Output** (`generator.py`): PDF generation with branding

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Get your API keys:
   - **Tavily API**: Sign up at [tavily.com](https://tavily.com) (free tier available)
   - **Anthropic API**: Get a key at [console.anthropic.com](https://console.anthropic.com)

3. Add your keys to `.env`:
   ```
   TAVILY_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   ```

### 3. Test the Research Engine

```bash
python research_agent.py
```

(Uncomment the test code at the bottom of `research_agent.py` first)

## Usage

### Run the Streamlit App

```bash
streamlit run app.py
```

## Project Structure

```
workshop_abm_gen/
├── requirements.txt
├── .env.example
├── README.md
├── research_agent.py    # Research engine (Step 2)
├── app.py              # Streamlit interface (Step 3 - TODO)
└── generator.py        # PDF generator (Step 4 - TODO)
```

## Features

- **Real-time Research**: Uses Tavily to gather current company information
- **Intelligent Synthesis**: LLM processes raw data into structured ABM insights
- **Branded Output**: Generates polished PDFs ready for BDR outreach

## Requirements

- Python 3.8+
- Tavily API key
- Anthropic API key (or OpenAI API key as alternative)

