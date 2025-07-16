 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/README.md
index 0000000000000000000000000000000000000000..cbe23bc26770897c2e0752311150bd6aa813f2f4 100644
--- a//dev/null
+++ b/README.md
@@ -0,0 +1,22 @@
+# Gmail Sales Automation
+
+This project automates the process of extracting payout emails from Gmail and logging them into a Google Sheet.  Messages are parsed with OpenAI to retrieve sale details.
+
+## Setup
+
+1. **Create Google credentials**
+   - Generate OAuth client credentials for a desktop application and save the file as `credentials.json` in the project directory.  This file should not be committed to version control.
+   - The first run will store authorization tokens in `token.json`.
+2. **Install dependencies**
+   ```bash
+   pip install -r requirements.txt  # or use the `pyproject.toml`
+   ```
+3. **Environment variables**
+   - `OPENAI_API_KEY` – your OpenAI API key.
+   - `SHEET_ID` – the ID of the Google Spreadsheet to update.
+4. **Run the script**
+   ```bash
+   python main.py
+   ```
+
+The script uses `InstalledAppFlow.run_local_server()` for OAuth authentication.  Ensure that your environment allows opening a browser window for the OAuth flow.
 
EOF
)
