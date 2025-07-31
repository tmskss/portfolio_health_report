# Project Portfolio Health Report Blueprint

## Overview of PoC

### Step 1: Data Ingestion
First step is to parse all emails, extract the metadata (from, to, subject, date), and the content of the email. The emails are uploaded to a vector database, including the metadata so filtering can be done in later steps.

### Step 2: Thread Analysis
The AI powered analytical sub-system analyzes the emails thread-by-thread. This is done by using the filtering provided by the metadata. The LLM receives the content of the whole thread, ordered by date, and analyzes the content and pinpoints risks, inconsistencies, and unresolved issues. The LLM will also receive additional context from other threads, if relevant, to provide a more comprehensive analysis. These outputs are stored for the next step.

### Step 3: Summarizing the Analysis
In this last step, the LLM receives the outputs from the previous step and generates a summary of the analysis. This summary will include the identified risks, inconsistencies, and unresolved issues.

---
# Further Techniques, Ideas

## Data Ingestion
The system parses the emails using regular expressions to extract the metadata and content. The emails are then uploaded to a vector database, which allows for efficient filtering and retrieval based on the metadata.

![Data Ingestion Flowchart](./img/dataIngestion.png)

This approach can handle large-scale data, since the vector database is designed for high performance and scalability. The metadata extraction ensures that the system can filter emails based on various criteria, such as sender, recipient, date, and subject. This also allows the system to filter emails not just by the thread, but also by the semantic content of the emails, which can be used to get rid of irrelevant emails in later steps (i.e. emails about a birthday party), which drastically reduces the amount of data that needs to be processed by LLMs in the next steps.

---

## The Analytical Engine
The analytical engine is built on a multi-stage RAG pipeline. The pipeline is designed to process massive volumes of communication efficiently, ensuring only the most relevant content reaches the expensive LLM layers.

### **Attention Flags**
The system detects two primary categories of issues that demand a Director’s attention:

1. **Unresolved High-Priority Action Items**  
   - Indicators: Tasks with owners and due dates that have no follow-up or confirmation after a threshold period.  
   - Example:  
     > “Security review pending approval since June 10 – no updates from compliance team.”

2. **Emerging Risks & Blockers**  
   - Indicators: References to delays, dependencies, budget overruns, or external blockers without clear mitigation plans.  
   - Example:  
     > “API integration at risk due to vendor timeline slippage.”
    
---

### **RAG Process (Thread-Level Retrieval)**

#### **1. Indexing & Storage**
- Each parsed email is stored as a chunk in a vector database (Chroma in PoC).  
- Metadata schema:
  - `from`
  - `to`
  - `subject`
  - `date`
  - `thread_id`
  - `thread_summary` 
  - `project`
- If the project is specified for every email/thread, the system can go project-by-project, which is crucial for the next steps. This can be done by using an LLM to classify the emails into a set of pre-defined projects (if available), or by using a simple keyword matching algorithm to identify the project based on the subject or content of the email.
- If a thread summary is specified, it can be used to achieve hieararchical retrieval in the next steps.

#### **2. Project Analysis**
- The system analyzes emails project-by-project, using the metadata to filter emails relevant to the current project.

#### **2.1. Thread Analysis**
- An Agentic LLM processes one thread at a time in chronological order:
  - Identifies risks, overdue tasks, inconsistencies.
  - Agent can work well, because it can interact with the vector database to retrieve relevant emails from other threads if needed.
  - Retrieves additional context from other threads if needed.
    - **Hierarchical Retrieval** is applied:
      - **Level 1**: Retrieve threads relevant to custom queries using semantic search + metadata filter (e.g., only last quarter).
      - **Level 2**: Retrieve relevant messages inside selected threads.
  - Produces structured JSON:
    ```json
    {
      "project": "test_project",
      "summary": "Summary of the thread",
      "unresolved_problems": [ "List of problems" ],
      "emerging_risks_blockers": [ "List of risks/blockers" ],
      "issues_needing_attention": [
        {
          "issue": "Issue description",
          "priority": 1
        }
      ]
    }
    ```
- This structured output is useful for guiding the LLM, and also it allows for easy processing in the next step.
- The structured output contains a field for the action items that need attention, which is crucial for the final report generation.
- **Solution in PoC:**
  ```python
    prompt = (
        f"""You are an AI assistant that specializes in analyzing email threads. Analyze the content and pinpoint any risks, inconsistencies, and unresolved issues. Give a concise report of your findings, including any potential risks to the project timeline or quality, inconsistencies in communication, and unresolved issues that need attention. This report should help a Director of Engineering understand the current state of the project and any potential problems. Only include the problems if they have not been resolved, or require attention from the director.\n\n

        Here is the content of the emails:\n
        {combined_emails}\n\n

        Here are the people involved in the emails:\n{colleagues_content}\n\n
            """
        )
  ```
  - This prompt is designed to guide the LLM to focus on the key issues that need attention, while also providing the necessary context from the emails and colleagues involved.
  - The prompt also has information about the recipients of the report (Director of Engineering), which helps the LLM to tailor the output to the audience.

#### **2.2. Aggregation**
- Outputs from all analyzed threads are aggregated by an LLM.
- Aggregator prompt generates a project-level summary.
- **Solution in PoC:**
```python
system_prompt = """
    You are a helpful assistant that receives project health reports created by analyzing email threads. Your task is to analyze these reports and provide a concise summary of the overall project health, including any potential risks, inconsistencies, and unresolved issues that need attention. This summary should help a Director of Engineering understand the current state of the project and any potential problems. It should also help the Director of Engineering to prioritize issues that need attention. Different email threads could be talking about the same project. There is a 'Project' field in the report. Only decide that threads are about the same project if there is a match in names. The threads could be about different projects, so you should not assume that they are all about the same project unless the 'Project' field matches up to a certain degree.
    """

prompt = "Analyze these reports and create a final project portfolio health report:\n" + "\n".join(reports)
```
- This prompt is designed to guide the LLM to focus on the key issues that need attention, while also providing the necessary context from the aggregated reports.
- In the PoC, the classification by projects is not implemented, so the prompt has guidance to not assume that all threads are about the same project unless the 'Project' field matches up to a certain degree.

#### **3. Final Report Generation**
- The final report is generated by an LLM using the aggregated project-level reports.

---

### **LLM Usage**
- **Chunk-level analysis**: `gpt-4o-mini` (low cost, deterministic, temperature=0).  
- **Final aggregation**: `gpt-4o` (clear, concise summary for the Director).  
- All calls use retrieved snippets only, not every email in every thread, to avoid context overflow.

---

## Cost & Robustness

### **Robustness**
- **Noise filtering**: Non-project communications (e.g., social or HR announcements) can be excluded before LLM processing using:
  - Metadata filtering (subject, recipients, keywords)
  - Optional lightweight classifier (fine-tuned or zero-shot LLM)
- **Cross-verification**: The final report includes references to original emails:
  - Each detected “Attention Flag” links to the original email excerpt.
  - This traceability ensures the Director can verify AI conclusions.

### **Cost Management**
- **Embedding reuse**: Once embedded, emails do not require reprocessing unless updated. In the PoC, the embeddings are stored in memory.
- **Selective retrieval**: Only threads within the QBR period are processed.  
- **Tiered LLM approach**: Small models for extraction, larger models only for the final summary.  
- **Batch processing**: Thread analysis can be parallelized across workers.

---

## Monitoring & Trust

### **Metrics Tracked**
- Since the user can provide feedback on the generated report, the system can track the following metrics:
- **Precision & Recall of Attention Flags**:
  - Compare AI outputs against manually identified risks/action items during pilot.
- **False Positive Rate**:
  - Number of incorrect risks flagged, tracked via feedback.
- **Operational Metrics**:
  - Model cost per QBR cycle
  - Latency of analysis pipeline

### **Monitoring Tools**
- **Prompt & Output Logging**:
  - Store each model call with input + output for audit.
- **Feedback Loops**:
  - Director feedback stored for fine-tuning prompts or filtering.

---

## Architectural Risk & Mitigation

### **Biggest Risk**
- **LLM Misinterpretation of Thread Context**:
  - If retrieval fails to bring in the right subset of emails, the model might miss key context, leading to incomplete or misleading reports.

### **Mitigation**
- **Retrieval Cross-Validation**:
  - Retrieve with multiple query strategies (e.g., “risks”, “blockers”, “delays”) and merge results.
- **Fail-Safe Aggregation**:
  - If relevant threads are too fragmented, the system flags the project for manual review rather than producing a misleading report.
