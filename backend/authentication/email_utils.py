import os
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import base64
from django.conf import settings
import re
import PyPDF2

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for development!

def extract_resume_highlights(resume_path):
    """Extract key information from resume PDF."""
    highlights = []
    try:
        with open(resume_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text()

            # Extract key sections (this is a simple example - can be enhanced)
            skills_match = re.search(r'Skills:(.*?)(?:\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
            experience_match = re.search(r'Experience:(.*?)(?:\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
            
            if skills_match:
                highlights.append(f"Skills: {skills_match.group(1).strip()}")
            if experience_match:
                highlights.append(f"Experience: {experience_match.group(1).strip()}")

        return highlights
    except Exception as e:
        print(f"Error extracting resume highlights: {str(e)}")
        return []

def generate_personalized_email(recipient_data, sender_data, resume_highlights):
    """
    Generate personalized cold email using Gemini AI.
    
    Args:
        recipient_data (dict): Contains recipient's name, title, company
        sender_data (dict): Contains sender's name, position applying for, and other details
        resume_highlights (list): Key points extracted from resume
    """
    genai.configure(api_key=os.getenv('GOOGLE_CLOUD_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
    
    # Create a detailed prompt for Gemini
    prompt = f"""
    Generate a personalized cold email for a job application with these details:

    RECIPIENT:
    - Name: {recipient_data['name']}
    - Title: {recipient_data['title']}
    - Company: {recipient_data['company']}

    SENDER:
    - Name: {sender_data['name']}
    - Position Applying For: {sender_data['position']}

    RESUME HIGHLIGHTS:
    {' '.join(resume_highlights)}

    Requirements:
    1. Keep it concise (150 words max)
    2. Personalize based on recipient's role and company
    3. Reference 1-2 relevant resume highlights that match the position
    4. Include a clear call to action for a meeting/discussion
    5. Maintain professional tone while being engaging
    6. Mention the attached resume
    7. Show genuine interest in {recipient_data['company']}

    Return only the email body text.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating email: {str(e)}")
        # Fallback to a basic template if Gemini fails
        return f"""
        Dear {recipient_data['name']},

        I hope this email finds you well. I am writing to express my strong interest in the {sender_data['position']} position at {recipient_data['company']}. With my background and skills, I believe I would be a valuable addition to your team.

        I have attached my resume for your review. I would greatly appreciate the opportunity to discuss how my skills align with your needs.

        Thank you for considering my application.

        Best regards,
        {sender_data['name']}
        """

def send_bulk_emails(user, contacts, resume_path):
    """
    Send personalized emails to all contacts in CSV.
    
    Args:
        user: Django user object
        contacts: List of CompanyContact objects
        resume_path: Path to user's resume
    
    Returns:
        tuple: (success_count, failed_count, errors)
    """
    success_count = 0
    failed_count = 0
    errors = []
    
    # Extract resume highlights once
    resume_highlights = extract_resume_highlights(resume_path)
    
    for contact in contacts:
        try:
            # Prepare recipient data
            recipient_data = {
                'name': contact.name,
                'title': contact.title,
                'company': contact.company,
                'email': contact.email
            }
            
            # Prepare sender data
            sender_data = {
                'name': user.get_full_name() or user.email,
                'position': user.userresume.position
            }
            
            # Generate personalized email
            email_body = generate_personalized_email(recipient_data, sender_data, resume_highlights)
            
            # Create email message
            subject = f"Application for {sender_data['position']} position at {recipient_data['company']}"
            message = create_mail_message(
                sender_email=user.email,
                to_email=recipient_data['email'],
                subject=subject,
                body=email_body,
                resume_path=resume_path
            )
            
            # Send email using Gmail API
            gmail_creds = user.gmailcredentials
            credentials = Credentials.from_authorized_user_info({
                'refresh_token': gmail_creds.refresh_token,
                'token': gmail_creds.access_token,
                'token_expiry': gmail_creds.token_expiry.isoformat(),
                'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
            })
            
            service = build('gmail', 'v1', credentials=credentials)
            service.users().messages().send(userId='me', body=message).execute()
            
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            errors.append(f"Failed to send email to {contact.email}: {str(e)}")
    
    return success_count, failed_count, errors

def get_oauth_flow():
    return Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=['https://www.googleapis.com/auth/gmail.send'],
        redirect_uri='http://localhost:8000/api/gmail-auth'
    )

def generate_email(recipient_name, company, position, sender_name):
    genai.configure(api_key=os.getenv('GOOGLE_CLOUD_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    Write a professional cold email for a job application:
    - To: {recipient_name} at {company}
    - Position: {position}
    - From: {sender_name}
    
    Make it:
    - Professional and concise (max 150 words)
    - Mention specific interest in {company}
    - Reference attached resume
    - Request to discuss further
    
    Return only the email body.
    """
    
    response = model.generate_content(prompt)
    return response.text

def create_mail_message(sender_email, to_email, subject, body, resume_path):

    message = MIMEMultipart()
    message['to'] = to_email
    message['from'] = sender_email
    message['subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    with open(resume_path, 'rb') as f:
        resume = MIMEApplication(f.read(), _subtype='pdf')
        resume.add_header('Content-Disposition', 'attachment', filename='resume.pdf')
        message.attach(resume)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')}