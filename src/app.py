import os
import chromadb
from flask import Flask, jsonify, request, logging

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv, find_dotenv

from utils import parse_multiple_emails, analyze_emails_with_llm, analyze_reports

app = Flask(__name__)
logger = logging.create_logger(app)

@app.route('/analyze', methods=['POST'])
def analyze_emails():
    """
    The main API endpoint that performs the following steps:
    1. Read all the txt files in the EMAILS_DIR and parse them into a list of tuples containing the metadata and body of each email.
    2. Add the parsed emails to the ChromaDB collection.
    3. Analyze each email thread using the OpenAI LLM and generate a report for each thread.
    4. Format the reports into a string.
    5. Analyze the formatted reports and generate an overall report.
    """
    try:
        # Get all the email files from the EMAILS_DIR
        email_files = os.listdir(os.getenv("EMAILS_DIR"))
        if 'Colleagues.txt' in email_files:
            email_files.remove('Colleagues.txt')

        # Create a ChromaDB client and a collection with the OpenAI LLM
        chroma_client = chromadb.Client()
        collection = chroma_client.get_or_create_collection(
            name="emails",
            embedding_function=OpenAIEmbeddingFunction(
                model_name="text-embedding-ada-002",
                api_key=os.getenv("OPENAI_API_KEY")
            )
        )
        
        # Parse the emails and add them to the ChromaDB collection
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

        # Read the content of the Colleagues.txt file
        with open(os.getenv("EMAILS_DIR") + '/Colleagues.txt', 'r') as file:
            colleagues_content = file.read()

        # Analyze each email thread
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
            thread_reports.append(analyze_emails_with_llm(emails_for_analysis, colleagues_content))
        
        # Format the reports
        formatted_reports = []
        for report in thread_reports:
            formatted_report = f"Project: {report['project']}\nSummary: {report['short_summary']}\nUnresolved Problems: {report['unresolved_problems']}\nEmerging Risks/Blockers: {report['emerging_risks_blockers']}\nIssues Needing Attention: {report['issues_needing_attention']}" + "-" * 40
        
            formatted_reports.append(formatted_report)
        
        # Analyze the reports
        overall_analysis = analyze_reports(formatted_reports)
        
        return jsonify({
            "success": True,
            "report": overall_analysis,
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    load_dotenv(find_dotenv(), override=True)
    app.run(host="0.0.0.0", port=5001, debug=True)