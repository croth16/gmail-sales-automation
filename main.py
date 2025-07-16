 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/main.py b/main.py
index e69de29bb2d1d6434b8b29ae775ad8c2e48c5391..2df4eec27e145db154890fd1599027b04c6ec1c8 100644
--- a/main.py
+++ b/main.py
@@ -0,0 +1,152 @@
+import base64
+import json
+import os
+
+import openai
+from google.auth.transport.requests import Request
+from google.oauth2.credentials import Credentials
+from google_auth_oauthlib.flow import InstalledAppFlow
+from googleapiclient.discovery import build
+
+SCOPES = [
+    "https://www.googleapis.com/auth/gmail.readonly",
+    "https://www.googleapis.com/auth/spreadsheets",
+]
+SHEET_RANGE = "Sheet1!A:E"
+
+
+def authenticate_google() -> Credentials:
+    """Authenticate with Google APIs using OAuth and return credentials."""
+    creds = None
+    if os.path.exists("token.json"):
+        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
+
+    if not creds or not creds.valid:
+        if creds and creds.expired and creds.refresh_token:
+            creds.refresh(Request())
+        else:
+            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
+            creds = flow.run_local_server(port=0)
+        with open("token.json", "w") as token:
+            token.write(creds.to_json())
+
+    return creds
+
+
+def fetch_emails(service):
+    """Return Gmail message metadata for payout emails."""
+    query = 'subject:"payout incoming" from:psa'
+    results = (
+        service.users()
+        .messages()
+        .list(userId="me", q=query, includeSpamTrash=True)
+        .execute()
+    )
+    return results.get("messages", [])
+
+
+def parse_email(service, message_id: str) -> dict:
+    """Retrieve an email, parse it with OpenAI, and return structured data."""
+    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
+    payload = msg.get("payload", {})
+    parts = payload.get("parts", [])
+
+    data = ""
+    if parts:
+        for part in parts:
+            if part.get("mimeType") == "text/plain":
+                data = part["body"].get("data", "")
+                break
+    else:
+        data = payload.get("body", {}).get("data", "")
+
+    decoded = base64.urlsafe_b64decode(data).decode()
+
+    prompt = f"""
+Extract the following fields from the email and return JSON:
+- Item Name
+- Certification Number (if available)
+- Sale Price
+- Proceeds
+- Sale Date
+
+Email:
+{decoded}
+
+Output format:
+{{
+    "item_name": "",
+    "cert_number": "",
+    "sale_price": "",
+    "proceeds": "",
+    "sale_date": ""
+}}
+"""
+    response = openai.ChatCompletion.create(
+        model="gpt-3.5-turbo",
+        messages=[{"role": "user", "content": prompt}],
+        temperature=0,
+    )
+    return json.loads(response.choices[0].message.content.strip())
+
+
+def get_existing_rows(sheet_service):
+    result = (
+        sheet_service.spreadsheets()
+        .values()
+        .get(spreadsheetId=os.environ["SHEET_ID"], range=SHEET_RANGE)
+        .execute()
+    )
+    return result.get("values", [])
+
+
+def append_to_sheet(sheet_service, data):
+    body = {"values": [data]}
+    sheet_service.spreadsheets().values().append(
+        spreadsheetId=os.environ["SHEET_ID"],
+        range=SHEET_RANGE,
+        valueInputOption="RAW",
+        insertDataOption="INSERT_ROWS",
+        body=body,
+    ).execute()
+
+
+def main():
+    openai.api_key = os.environ["OPENAI_API_KEY"]
+    creds = authenticate_google()
+    gmail_service = build("gmail", "v1", credentials=creds)
+    sheet_service = build("sheets", "v4", credentials=creds)
+
+    emails = fetch_emails(gmail_service)
+    if not emails:
+        print("No matching emails found.")
+        return
+
+    existing_rows = get_existing_rows(sheet_service)
+    existing_keys = {(row[1], row[2]) for row in existing_rows if len(row) >= 3}
+
+    for email in emails:
+        try:
+            parsed = parse_email(gmail_service, email["id"])
+            key = (parsed["item_name"], parsed["sale_price"])
+            if key not in existing_keys:
+                append_to_sheet(
+                    sheet_service,
+                    [
+                        parsed["sale_date"],
+                        parsed["item_name"],
+                        parsed["sale_price"],
+                        parsed["proceeds"],
+                        parsed.get("cert_number", "N/A"),
+                    ],
+                )
+                existing_keys.add(key)
+                print(f"Added: {parsed['item_name']} at {parsed['sale_price']}")
+            else:
+                print(f"Duplicate skipped: {parsed['item_name']} at {parsed['sale_price']}")
+        except Exception as e:
+            print(f"Error processing email {email['id']}: {e}")
+
+
+if __name__ == "__main__":
+    main()
 
EOF
)
