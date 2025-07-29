import re
import os
import chromadb

from openai import OpenAI
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv, find_dotenv
from pprint import pprint

def main():
    with open("/Users/tmskss/Development/portfolio_health_report/data/AI_Developer/email1.txt", "r") as file:
        file_content = file.read()

    parsed_emails = parse_multiple_emails(file_content)

    chroma_client = chromadb.Client()

    # Upload emails to ChromaDB
    collection = chroma_client.get_or_create_collection(
        name="emails",
        embedding_function=OpenAIEmbeddingFunction(
            model_name="text-embedding-ada-002",
            api_key=os.getenv("OPENAI_API_KEY")
        )
    )

    for i, (metadata, body) in enumerate(parsed_emails):
        collection.add(
            ids=[str(i)],
            documents=[body],
            metadatas=[metadata]
        )

    print(f"Uploaded {len(parsed_emails)} emails to ChromaDB.")

    results = collection.get(
        where={"subject": "Project Phoenix - New Login Page Specification"}
    )

    print(f"Retrieved {len(results)} emails with subject 'test' from ChromaDB.")

    emails_for_analysis = []
    for doc, metadata in zip(results['documents'], results['metadatas']):
        email_content = f"From: {metadata['from']}\nTo: {metadata['to']}\nDate: {metadata['date']}\nSubject: {metadata['subject']}\n\n{doc}"
        emails_for_analysis.append(email_content)

    # Analyze emails with OpenAI LLM
    analysis = analyze_emails_with_llm(emails_for_analysis)

    print("LLM receives the following emails for analysis:")
    print("\n\n".join(emails_for_analysis))

    print("LLM Analysis Results:")
    pprint(analysis)

    

def analyze_emails_with_llm(emails):
    # Combine email bodies for the LLM context
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
    response = openai_client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        temperature=0.7
    )

    return response.output_text


def parse_email(content):
    metadata = {}
    
    # Extract metadata
    metadata["from"] = re.search(r"^From: (.+)$", content, re.MULTILINE).group(1)
    metadata["to"] = re.search(r"^To: (.+)$", content, re.MULTILINE).group(1)
    metadata["date"] = re.search(r"^Date: (.+)$", content, re.MULTILINE).group(1)
    metadata["subject"] = re.search(r"^Subject: (.+)$", content, re.MULTILINE).group(1)
    
    # Extract email body by finding the first empty line, then taking the remainder of the content.
    body_start = content.find("\n\n")
    if body_start != -1:
        body = content[body_start + 2:]
    else:
        body = ""
    
    return metadata, body

def parse_multiple_emails(file_content):
    # Files either start with "From" or "Subject", so we determine the split string accordingly
    split_string = "From" if file_content.startswith("From") else "Subject"

    emails = file_content.strip().split("\n\n"+split_string+": ")
    parsed_emails = []
    
    for i, email in enumerate(emails):
        if i != 0:
            email = split_string + ": " + email
        metadata, body = parse_email(email)
        parsed_emails.append((metadata, body))
    
    return parsed_emails

if __name__ == "__main__":
    load_dotenv(find_dotenv(), override=True)
    main()