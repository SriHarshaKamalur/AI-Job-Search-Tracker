import os.path
import base64
import csv
from datetime import date
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from transformers import pipeline

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_email_body(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                return base64.urlsafe_b64decode(data).decode('utf-8')
            elif 'parts' in part: 
                return get_email_body(part)
    elif payload.get('mimeType') == 'text/plain':
        data = payload['body'].get('data', '')
        return base64.urlsafe_b64decode(data).decode('utf-8')
    return "Could not find plain text."

def get_or_create_label(service, label_name):
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        for label in labels:
            if label['name'] == label_name:
                return label['id']
        
        label_object = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        created_label = service.users().labels().create(userId='me', body=label_object).execute()
        return created_label['id']
    except Exception as e:
        print(f"Error getting/creating label: {e}")
        return None

def main():
    print("🧠 Waking up the AI Brain...")
    brain = pipeline("text-classification", model="Rashmi000/Gmail_Label", truncation=True, max_length=512)

    creds = None
    if os.path.exists('auth/token.json'):
        creds = Credentials.from_authorized_user_file('auth/token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('auth/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('auth/token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        
        translation_dictionary = {
            "LABEL_0": "Job_Application_Confirmation",
            "LABEL_1": "Job_Rejected",
            "LABEL_2": "Job_Uncertain"
        }
        
        # 🔎 SMART QUERY: Look for emails from the last 24hrs that don't have our labels yet
        search_query = "newer_than:1d -label:Job_Application_Confirmation -label:Job_Rejected -label:Job_Uncertain -label:Job_Assessment -label:Job_Alert"
        print("\n🔎 Searching inbox for recent job emails...")
        
        messages = []
        request = service.users().messages().list(userId='me', q=search_query, maxResults=500)
        
        while request is not None:
            response = request.execute()
            if 'messages' in response:
                messages.extend(response['messages'])
            request = service.users().messages().list_next(previous_request=request, previous_response=response)

        if not messages:
            print("No new emails found! You are all caught up for today.")
            return

        print(f"\n🚀 FOUND {len(messages)} EMAILS TO PROCESS!")
        print("=" * 50)
        
        # 📊 Metrics Counters
        session_apps = 0
        session_rejects = 0
        session_assessments = 0
        session_uncertain = 0

        count = 1
        for msg in messages:
            try:
                msg_id = msg['id']
                msg_data = service.users().messages().get(userId='me', id=msg_id).execute()
                payload = msg_data['payload']
                headers = payload['headers']
                
                subject = "No Subject"
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                        break
                
                body = get_email_body(payload)
                text_to_read = f"Subject: {subject}\n\nBody: {body[:400]}"
                text_lower = text_to_read.lower()
                
                # 🛡️ THE TRIPLE SCANNER
                
                # 1. Catch Automated Job Alerts (Do not count these in metrics)
                if any(phrase in text_lower for phrase in ["job alert", "talent community", "matched the following jobs", "you are receiving this email because"]):
                    gmail_label_name = "Job_Alert"
                    print(f"[{count}/{len(messages)}] 🗑️ Caught Job Alert: {subject[:30]}...")
                
                # 2. Catch Assessments
                elif any(word in text_lower for word in ["hackerrank", "coderpad", "hirevue", "assessment", "online test"]):
                    gmail_label_name = "Job_Assessment"
                    session_assessments += 1
                    print(f"[{count}/{len(messages)}] 💻 Caught Assessment: {subject[:30]}...")
                
                # 3. Catch Sneaky Rejections (Disney, Snap Inc., etc.)
                elif any(phrase in text_lower for phrase in [
                    "other candidates", "careful deliberation", "unfortunately", "not moving forward", 
                    "wish you the best", "pursuing other", "pursuing candidates", "more closely match", 
                    "keep us in mind", "success in your job search", "decided to move forward with",
                    "while your background is impressive"
                ]):
                    gmail_label_name = "Job_Rejected"
                    session_rejects += 1
                    print(f"[{count}/{len(messages)}] ❌ Caught Rejection: {subject[:30]}...")
                
                # 4. Let the AI Brain guess the rest!
                else:
                    prediction = brain(text_to_read)[0]
                    raw_label = prediction['label']
                    gmail_label_name = translation_dictionary.get(raw_label, "Job_Uncertain")
                    
                    if gmail_label_name == "Job_Application_Confirmation": session_apps += 1
                    elif gmail_label_name == "Job_Rejected": session_rejects += 1
                    else: session_uncertain += 1
                    print(f"[{count}/{len(messages)}] 🤖 AI Guessed '{gmail_label_name}': {subject[:30]}...")

                # 🏷️ APPLY LABELS & ARCHIVE!
                label_id = get_or_create_label(service, gmail_label_name)
                if label_id:
                    service.users().messages().modify(
                        userId='me', 
                        id=msg_id, 
                        body={
                            'addLabelIds': [label_id], 
                            'removeLabelIds': ['UNREAD', 'INBOX']
                        }
                    ).execute()
                
            except Exception as e:
                print(f"[{count}/{len(messages)}] ⚠️ Skipped an email: {e}")
                
            count += 1

        # 💾 Save metrics to Streamlit Dashboard
        file_exists = os.path.isfile('metrics.csv')
        with open('metrics.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Date', 'Applications', 'Rejections', 'Assessments', 'Uncertain'])
            
            # Only write a new row if we actually found real job emails
            if session_apps > 0 or session_rejects > 0 or session_assessments > 0 or session_uncertain > 0:
                writer.writerow([str(date.today()), session_apps, session_rejects, session_assessments, session_uncertain])
            
        print("\n🎉 ALL DONE! Inbox archived and dashboard updated.")

    except Exception as error:
        print(f"Oops! The robot tripped: {error}")

if __name__ == '__main__':
    main()