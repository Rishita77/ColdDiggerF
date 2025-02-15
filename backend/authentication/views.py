from django.http import FileResponse
import mimetypes
import os
from wsgiref.util import FileWrapper
from django.shortcuts import get_object_or_404
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import json

from .models import UserResume, CompanyContact, EmailHistory, ApplicationHistory, GmailCredentials
from .utils import process_csv_file

from django.contrib.auth.decorators import login_required

from .email_utils import get_oauth_flow, generate_email, create_mail_message, send_bulk_emails, extract_resume_highlights, generate_personalized_email
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'message': 'CSRF cookie set'})

@login_required
def get_contacts(request):
    """Fetch all contacts from the database"""
    try:
        contacts = CompanyContact.objects.all().values(
            'id', 'name', 'email', 'title', 'company'
        )
        return JsonResponse({'contacts': list(contacts)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def check_gmail_auth(request):
    try:
        GmailCredentials.objects.get(user=request.user)
        return JsonResponse({'isAuthorized': True})
    except GmailCredentials.DoesNotExist:
        flow = get_oauth_flow()
        auth_url, state = flow.authorization_url()
        request.session['gmail_state'] = state
        return JsonResponse({
            'isAuthorized': False,
            'authUrl': auth_url
        })


@login_required
def gmail_auth_callback(request):
    try:
        flow = get_oauth_flow()

        # Get the authorization code from the request
        code = request.GET.get('code')
        state = request.GET.get('state')

        if not code or not state:
            return JsonResponse({'error': 'Missing authorization code or state'}, status=400)

        if state != request.session.get('gmail_state'):
            return JsonResponse({'error': 'Invalid state parameter'}, status=400)

        # Exchange the authorization code for credentials
        flow.fetch_token(code=code)

        creds = flow.credentials
        GmailCredentials.objects.update_or_create(
            user=request.user,
            defaults={
                'refresh_token': creds.refresh_token,
                'access_token': creds.token,
                'token_expiry': creds.expiry
            }
        )

        return redirect('http://localhost:5173/dashboard')

    except Exception as e:
        return JsonResponse({
            'error': f'Authorization failed: {str(e)}'
        }, status=400)

@csrf_exempt
@login_required
def send_email(request):
    try:
        data = json.loads(request.body)
        send_to_all = data.get('sendToAll', False)

        try:
            user_resume = UserResume.objects.get(user=request.user)
        except UserResume.DoesNotExist:
            return JsonResponse({'error': 'Please upload your resume first'}, status=400)

        if send_to_all:
            # Send to all contacts
            contacts = CompanyContact.objects.all()
            if not contacts:
                return JsonResponse({'error': 'No contacts found'}, status=400)
                
            success_count, failed_count, errors = send_bulk_emails(
                user=request.user,
                contacts=contacts,
                resume_path=user_resume.resume.path
            )

            return JsonResponse({
                'message': f'Sent {success_count} emails successfully. {failed_count} failed.',
                'errors': errors if errors else None
            })
        else:
            # Single contact email sending
            contact_id = data.get('contactId')
            if not contact_id:
                return JsonResponse({'error': 'Contact ID is required for single email'}, status=400)

            contact = CompanyContact.objects.get(id=contact_id)
            recipient_data = {
                'name': contact.name,
                'title': contact.title,
                'company': contact.company,
                'email': contact.email
            }

            sender_data = {
                'name': request.user.get_full_name() or request.user.email,
                'position': user_resume.position
            }

            resume_highlights = extract_resume_highlights(user_resume.resume.path)
            email_body = generate_personalized_email(recipient_data, sender_data, resume_highlights)

            subject = f"Application for {sender_data['position']} position at {recipient_data['company']}"
            message = create_mail_message(
                sender_email=request.user.email,
                to_email=recipient_data['email'],
                subject=subject,
                body=email_body,
                resume_path=user_resume.resume.path
            )

            gmail_creds = GmailCredentials.objects.get(user=request.user)
            credentials = Credentials.from_authorized_user_info({
                'refresh_token': gmail_creds.refresh_token,
                'token': gmail_creds.access_token,
                'token_expiry': gmail_creds.token_expiry.isoformat(),
                'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
            })

            service = build('gmail', 'v1', credentials=credentials)
            service.users().messages().send(userId='me', body=message).execute()

            return JsonResponse({'message': 'Email sent successfully'})

    except UserResume.DoesNotExist:
        return JsonResponse({'error': 'Please upload your resume first'}, status=400)
    except GmailCredentials.DoesNotExist:
        return JsonResponse({'error': 'Gmail authorization required'}, status=401)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug log
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        # Create user
        user = User.objects.create_user(
            username=email,  # Using email as username
            email=email,
            password=password
        )
        user.first_name = name
        user.save()

        return JsonResponse({'message': 'User registered successfully'})

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        user = authenticate(username=email, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({
                'message': 'Login successful',
                'user': {
                    'name': user.first_name,
                    'email': user.email
                }
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'})

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def check_auth(request):
    if request.user.is_authenticated:
        return JsonResponse({
            'isAuthenticated': True,
            'user': {
                'name': request.user.first_name,
                'email': request.user.email
            }
        })
    return JsonResponse({'isAuthenticated': False})


@csrf_exempt
def upload_files(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        new_contacts_count = 0
        resume_file = request.FILES.get('resume')
        position = request.POST.get('position', '')
        csv_file = request.FILES.get('csv_file')

        # Update or create current UserResume
        if resume_file or position:
            defaults = {}
            if resume_file:
                defaults['resume'] = resume_file
            if position:
                defaults['position'] = position

            UserResume.objects.update_or_create(
                user=request.user,
                defaults=defaults
            )

        # Create new application history entry
        application = ApplicationHistory(
            user=request.user,
            position=position
        )

        if resume_file:
            application.resume = resume_file

        if csv_file:
            application.contacts_csv = csv_file
            try:
                new_contacts_count = process_csv_file(csv_file)
            except ValueError as e:
                return JsonResponse({'error': str(e)}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Error processing CSV: {str(e)}'}, status=400)

        application.save()

        return JsonResponse({
            'message': 'Upload successful',
            'new_contacts_added': new_contacts_count
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# Add new view to get position
@csrf_exempt
def get_user_position(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        user_resume = UserResume.objects.get(user=request.user)
        return JsonResponse({
            'position': user_resume.position,
            'updated_at': user_resume.updated_at
        })
    except UserResume.DoesNotExist:
        return JsonResponse({'error': 'No position found'}, status=404)


@csrf_exempt
def get_user_resume(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        resume = UserResume.objects.get(user=request.user)
        return JsonResponse({
            'resume_url': resume.resume.url,
            'updated_at': resume.updated_at
        })
    except UserResume.DoesNotExist:
        return JsonResponse({'error': 'No resume found'}, status=404)


@login_required
def get_email_history(request):
    if request.method == 'GET':
        history = EmailHistory.objects.filter(user=request.user).values(
            'id', 'recipient', 'subject', 'sent_date', 'status'
        )
        return JsonResponse({'history': list(history)})
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def download_file(request, application_id, file_type):
    """
    Download a file (resume or CSV) from an application history entry
    """
    application = get_object_or_404(
        ApplicationHistory, id=application_id, user=request.user)

    if file_type == 'resume':
        file_field = application.resume
        content_type = 'application/pdf'
        filename = f'resume_{application_id}.pdf'
    elif file_type == 'csv':
        file_field = application.contacts_csv
        content_type = 'text/csv'
        filename = f'contacts_{application_id}.csv'
    else:
        return JsonResponse({'error': 'Invalid file type'}, status=400)

    if not file_field:
        return JsonResponse({'error': 'File not found'}, status=404)

    try:
        file_path = file_field.path
        file_wrapper = FileWrapper(open(file_path, 'rb'))
        response = FileResponse(file_wrapper, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_application_history(request):
    if request.method == 'GET':
        history = ApplicationHistory.objects.filter(user=request.user).values(
            'id',
            'position',
            'resume',
            'contacts_csv',
            'application_date'
        )
        return JsonResponse({'history': list(history)})
    return JsonResponse({'error': 'Invalid request method'}, status=400)
