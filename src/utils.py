import re
import json

from openai import OpenAI

THREAD_OUTPUT_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "email_thread_risk_analysis",
        "schema": {
            "type": "object",
            "properties": {
            "short_summary": {
                "type": "string",
                "description": "A concise summary of the main points from the email thread.",
                "minLength": 1
            },
            "project": {
                "type": "string",
                "description": "The name of the project being discussed in the email thread. This is usually mentioned in the subject of the email.",
                "minLength": 1
            },
            "unresolved_problems": {
                "type": "array",
                "description": "A list of problems mentioned in the thread that have not yet been resolved.",
                "items": {
                "type": "string",
                "minLength": 1
                }
            },
            "emerging_risks_blockers": {
                "type": "array",
                "description": "Newly identified or developing risks or blockers within the email thread.",
                "items": {
                "type": "string",
                "minLength": 1
                }
            },
            "issues_needing_attention": {
                "type": "array",
                "description": "List of issues that need attention, ranked in order of priority (highest priority first).",
                "items": {
                "type": "object",
                "properties": {
                    "issue": {
                    "type": "string",
                    "description": "Description of the issue requiring attention.",
                    "minLength": 1
                    },
                    "priority": {
                    "type": "integer",
                    "description": "The ranking of the issue (1 = highest priority, increasing numbers = lower priority).",
                    "minimum": 1
                    }
                },
                "required": [
                    "issue",
                    "priority"
                ],
                "additionalProperties": False
                }
            }
            },
            "required": [
            "short_summary",
            "project",
            "unresolved_problems",
            "emerging_risks_blockers",
            "issues_needing_attention"
            ],
            "additionalProperties": False
        },
        "strict": True
        }
}

def analyze_reports(reports: list) -> str:
    system_prompt = """
    You are a helpful assistant that receives project health reports created by analyzing email threads. Your task is to analyze these reports and provide a concise summary of the overall project health, including any potential risks, inconsistencies, and unresolved issues that need attention. This summary should help a Director of Engineering understand the current state of the project and any potential problems. It should also help the Director of Engineering to prioritize issues that need attention. Different email threads could be talking about the same project. There is a 'Project' field in the report. Only decide that threads are about the same project if there is a match in names. The threads could be about different projects, so you should not assume that they are all about the same project unless the 'Project' field matches up to a certain degree.
    """

    prompt = "Analyze these reports and create a final project portfolio health report:\n" + "\n".join(reports)

    openai_client = OpenAI()
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
    )

    return response.choices[0].message.content

def analyze_emails_with_llm(emails: dict) -> dict:
    """
    Analyze a list of emails with an OpenAI LLM.

    Args:
        emails: List of emails to analyze.

    Returns:
        A dictionary containing a concise report of the analysis,
        including any potential risks to the project timeline or quality, inconsistencies in communication, and unresolved issues that need attention. The report should help a Director of Engineering understand the current state of the project and any potential problems.
    """
    combined_emails = "\n\n".join(email for email in emails)
    
    prompt = (
        f"""You are an AI assistant that specializes in analyzing email threads. Analyze the content and pinpoint any risks, inconsistencies, and unresolved issues. Give a concise report of your findings, including any potential risks to the project timeline or quality, inconsistencies in communication, and unresolved issues that need attention. This report should help a Director of Engineering understand the current state of the project and any potential problems. Only include the problems if they have not been resolved, or require attention from the director.\n\n

        Here is the content of the emails:\n
        {combined_emails}\n\n

        Here are the people involved in the emails:\n
        Project Manager (PM): Péter Kovács (kovacs.peter@kisjozsitech.hu)
        Business Analyst (BA): Zsuzsa Varga (varga.zsuzsa@kisjozsitech.hu)
        Senior Developer: István Nagy (nagy.istvan@kisjozsitech.hu)
        Frontend Developer: Anna Kiss (kiss.anna@kisjozsitech.hu)
        Junior Developer: Gábor Horváth (horvath.gabor@kisjozsitech.hu)
        Account Manager (AM): Eszter Szabó (szabo.eszter@kisjozsitech.hu)
        Project Manager (PM): Gábor Nagy (gabor.nagy@kisjozsitech.hu)
        Business Analyst (BA): Eszter Varga (eszter.varga@kisjozsitech.hu)
        Developer 1 (Senior): Péter Kovács (peter.kovacs@kisjozsitech.hu)
        Developer 2 (Medior): Bence Tóth (bence.toth@kisjozsitech.hu)
        Developer 3 (Junior): Anna Horváth (anna.horvath@kisjozsitech.hu)
        Account Manager (AM): Zoltán Kiss (zoltan.kiss@kisjozsitech.hu)
        Project Manager (PM): Péter Kovács (peter.kovacs@kisjozsitech.hu)
        Business Analyst (BA): Anna Nagy (anna.nagy@kisjozsitech.hu)
        Developer 1 (Backend): Gábor Kiss (gabor.kiss@kisjozsitech.hu)
        Developer 2 (Frontend): Bence Szabó (bence.szabó@kisjozsitech.hu)
        Developer 3 (Full-stack): Zsófia Varga (zsofia.varga@kisjozsitech.hu)
        Client Relationship Manager: Eszter Horváth (eszter.horvath@kisjozsitech.hu)
        """
    )
    
    openai_client = OpenAI()
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        response_format=THREAD_OUTPUT_FORMAT,
    )

    return json.loads(response.choices[0].message.content)

def parse_email(content):
    metadata = {}
    
    # Extract metadata
    metadata["from"] = re.search(r"^From: (.+)$", content, re.MULTILINE).group(1)
    metadata["to"] = re.search(r"^To: (.+)$", content, re.MULTILINE).group(1)
    metadata["date"] = re.search(r"^Date: (.+)$", content, re.MULTILINE).group(1)
    metadata["subject"] = re.search(r"^Subject: (.+)$", content, re.MULTILINE).group(1)
    
    # Find where the subject line ends
    subject_match = re.search(r"^Subject: (.+)$", content, re.MULTILINE)
    subject_end_pos = subject_match.end()
    
    # Extract email body by either finding the first empty line after subject
    # or by taking everything after the subject line if no empty line exists
    body_start = content.find("\n\n", subject_end_pos)
    if body_start != -1:
        body = content[body_start + 2:]
    else:
        # No empty line found, take everything after the subject line
        # Find the next line after subject
        next_line_start = content.find("\n", subject_end_pos) + 1
        body = content[next_line_start:]
    
    return metadata, body

def parse_multiple_emails(file_content: str, email_file: str):
    # Files either start with "From" or "Subject", so we determine the split string accordingly
    split_string = "From" if file_content.startswith("From") else "Subject"

    emails = file_content.strip().split("\n\n"+split_string+": ")
    parsed_emails = []
    
    for i, email in enumerate(emails):
        if i != 0:
            email = split_string + ": " + email
        metadata, body = parse_email(email)
        metadata["email_file"] = email_file
        parsed_emails.append((metadata, body))
    
    return parsed_emails