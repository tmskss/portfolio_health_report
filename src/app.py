import os
import chromadb

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv, find_dotenv
from pprint import pprint

from utils import parse_multiple_emails, analyze_emails_with_llm, analyze_reports

def main():
    email_files = os.listdir(os.getenv("EMAILS_DIR"))
    email_files.remove('Colleagues.txt')
    
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(
        name="emails",
        embedding_function=OpenAIEmbeddingFunction(
            model_name="text-embedding-ada-002",
            api_key=os.getenv("OPENAI_API_KEY")
        )
    )
    
    parsed_emails = []

    for email_file in email_files:
        file_path = os.path.join(os.getenv("EMAILS_DIR"), email_file)
        with open(file_path, "r") as file:
            file_content = file.read()
        
        parsed_emails.extend(parse_multiple_emails(file_content, email_file))

    for i, (metadata, body) in enumerate(parsed_emails):
        collection.add(
            ids=[str(i)],
            documents=[body],
            metadatas=[metadata]
        )

    print(f"Uploaded {len(parsed_emails)} emails to ChromaDB.")

    thread_reports = []
    for email_file in email_files:
        results_thread = collection.get(
            where={"email_file": email_file}
        )

        emails_for_analysis = []
        for doc, metadata in zip(results_thread['documents'], results_thread['metadatas']):
            email_content = f"From: {metadata['from']}\nTo: {metadata['to']}\nDate: {metadata['date']}\nSubject: {metadata['subject']}\n\n{doc}"
            emails_for_analysis.append(email_content)

        # Analyze emails with OpenAI LLM
        thread_reports.append(analyze_emails_with_llm(emails_for_analysis))
    
    thread_reports_formatted = []
    for report in thread_reports:
        print(report)
        formatted_report = f"Project: {report['project']}\n\nSummary:\n{report['short_summary']}\n\nUnresolved Problems:\n{report['unresolved_problems']}\n\nEmerging Risks/Blockers:\n{report['emerging_risks_blockers']}\n\nIssues Needing Attention:\n{report['issues_needing_attention']}\n{'-'*40}\n"
        
        thread_reports_formatted.append(formatted_report)

    final_report = analyze_reports(thread_reports_formatted)
    print("Final report:")
    print(final_report)

if __name__ == "__main__":
    load_dotenv(find_dotenv(), override=True)
    main()