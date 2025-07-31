# Project Portfolio Health Report

This tool analyzes email threads to generate comprehensive project health reports for Directors of Engineering, highlighting risks, inconsistencies, and unresolved issues across projects.

## Overview of PoC

### Step 1: Data Ingestion
First step is to parse all emails, extract the metadata (from, to, subject, date), and the content of the email. The emails are uploaded to a vector database, including the metadata so filtering can be done in later steps.

### Step 2: Thread Analysis
The AI powered analytical sub-system analyzes the emails thread-by-thread. This is done by using the filtering provided by the metadata. The LLM receives the content of the whole thread, ordered by date, and analyzes the content and pinpoints risks, inconsistencies, and unresolved issues. The LLM will also receive additional context from other threads, if relevant, to provide a more comprehensive analysis. These outputs are stored for the next step.

### Step 3: Summarizing the Analysis
In this last step, the LLM receives the outputs from the previous step and generates a summary of the analysis. This summary will include the identified risks, inconsistencies, and unresolved issues.

## How It Works

The system detects two primary categories of issues that demand a Director's attention:

1. **Unresolved High-Priority Action Items**  
   - Tasks with owners and due dates that have no follow-up or confirmation after a threshold period.
   - Example: "Security review pending approval since June 10 – no updates from compliance team."

2. **Emerging Risks & Blockers**  
   - References to delays, dependencies, budget overruns, or external blockers without clear mitigation plans.
   - Example: "API integration at risk due to vendor timeline slippage."
  
The system also generates an ordered list of action items for the Director to follow up on, based on the identified risks and unresolved issues.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/tmskss/portfolio_health_report.git
cd portfolio_health_report
```

2. Create a `.env` file based on the `.env.sample` file

## Usage

### Basic Usage

1. Run the application with:

```bash
docker-compose up --build
```
2. The backend will start at:

```bash
http://localhost:5001
```

3. The frontend will start at:
```bash
http://localhost:7860
```

- You can upload txt files on the frontend and see the generated report at the bottom of the page after the backend is finished (might take a few minutes).
- You also need to upload a `Colleagues.txt` file along with the email files.

## Requirements

- OpenAI API key
- Docker
- Python 3.10+