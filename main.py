import os
import base64
import pickle
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(filename='gmail_image_downloader.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Define scopes and credentials
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
creds = None

# Define the email address to filter
from_email = 'mitansh13fb@gmail.com'

try:
    # Authenticate with Gmail API
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Connect to Gmail API
    service = build('gmail', 'v1', credentials=creds)

    # Load processed emails
    processed_emails = set()
    if os.path.exists('processed_emails.pickle'):
        with open('processed_emails.pickle', 'rb') as f:
            processed_emails = pickle.load(f)

    # Define folder path for saving images
    images_folder = 'images'
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)

    # Search for emails from the specified email address
    result = service.users().messages().list(userId='me', q=f'from:{from_email}').execute()
    logging.info(f"Processing email from {from_email}")
    messages = result.get('messages', [])

    # Process new emails
    for message in messages:
        if message['id'] not in processed_emails:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            for part in msg['payload']['parts']:
                if part.get('filename') and part['filename'].endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId='me', messageId=message['id'], id=att_id).execute()
                    data = base64.urlsafe_b64decode(att['data'].encode('UTF-8'))
                    image_path = os.path.join(images_folder, part['filename'])
                    with open(image_path, 'wb') as f:
                        f.write(data)
                    logging.info(f"Downloaded image '{part['filename']}' from email ID {message['id']}")
            processed_emails.add(message['id'])
    # Save processed emails
    with open('processed_emails.pickle', 'wb') as f:
        pickle.dump(processed_emails, f)
    logging.info("Processed emails saved successfully.")

except Exception as e:
    logging.error(f"An error occurred: {str(e)}")
