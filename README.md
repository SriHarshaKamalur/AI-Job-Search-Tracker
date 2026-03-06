# 📊 AI Job Search Tracker & Gmail Triage Robot

An autonomous, AI-powered Python pipeline that monitors a Gmail inbox for job application updates, categorizes them using a Hugging Face machine learning model, and visualizes the data on a live Streamlit dashboard. 

## 🏗️ System Architecture
This project integrates cloud APIs, local machine learning, and data visualization to create a seamless "Inbox Zero" automation tool for job seekers.

* **Email Ingestion:** Authenticates with the **Gmail API** (OAuth 2.0) to securely fetch recent, unprocessed emails.
* **Triage & Classification:** * **Keyword Scanner:** A multi-layered regex/keyword scanner instantly identifies standard Job Alerts, Online Assessments (HackerRank, HireVue), and subtle corporate rejection language (e.g., "pursuing other candidates").
  * **AI Brain:** Emails that bypass the keyword scanner are passed to a local **Hugging Face NLP model** (`text-classification`) to accurately predict outcomes (Confirmation, Rejection, or Uncertain).
* **Automated Inbox Management:** The script dynamically generates and applies custom Gmail labels (e.g., `Job_Assessment`, `Job_Rejected`) and archives the emails (removes from Inbox) to keep the primary workspace clean.
* **Data Pipeline:** Daily metrics (Applications, Rejections, Assessments) are appended to a local `metrics.csv` database.
* **Interactive Dashboard:** A **Streamlit** web application reads the database and uses **Plotly** to render interactive daily trend graphs and conversion rate metrics.

## 💻 Tech Stack
* **Language:** Python 3.x
* **Machine Learning:** Hugging Face `transformers`, PyTorch
* **Cloud & APIs:** Google Cloud Platform (GCP), Gmail API v1, `google-auth`
* **Data & Frontend:** Streamlit, Pandas, Plotly Express
* **Automation:** Windows Task Scheduler / `.bat` scripting

## 🚀 How It Works
1. The user applies for jobs normally.
2. The Python script runs locally (manually or via a scheduled task).
3. The robot scans the inbox, parses the email bodies via base64 decoding, and feeds the text to the classification engine.
4. Emails are labeled and archived in Gmail.
5. The Streamlit dashboard updates instantly to reflect the new application, rejection, and assessment counts.

> **Note on Security:** To protect personal inbox data and Google Cloud credentials, the `auth/` directory (containing `credentials.json` and `token.json`) and the user's specific `metrics.csv` data are explicitly excluded from this repository via `.gitignore`.