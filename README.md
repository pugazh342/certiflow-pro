# 🛡️ CertiFlow Pro
### A Zero-Cost, Human-In-The-Loop (HITL) Certificate Generator & Email Dispatch Toolkit

![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/PDF_Engine-Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Jinja2](https://img.shields.io/badge/Templating-Jinja2-B41717?style=for-the-badge&logo=jinja&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

---

## 📖 Overview
**CertiFlow Pro** is a professional-grade desktop UI architecture designed to solve a common administrative bottleneck: generating and emailing batch PDFs securely, locally, and for **$0**. 

Unlike SaaS alternatives that upload sensitive recipient data to third-party clouds or charge per-document generation fees, CertiFlow Pro runs **100% locally** on your machine. It features automated data sanitization, auto-scaling typography, anti-spam network jitter, crash resilience via JSON checkpointing, and a strict Human-In-The-Loop (HITL) confirmation gate.

---

## 🏛️ System Architecture

The software operates sequentially across four distinct operational zones: **Ingest**, **Render**, **Gate**, and **Dispatch**.


```

+-------------------------------------------------------------------------------+
|                               STEP 1: INGEST                                  |
|  [ Raw CSV Upload ] ---> ( ingestor.py ) ---> [ Whitespace Strip & Case Fix ] |
|                                    |                                          |
|                      +-------------+-------------+                            |
|                      | (Regex Validation Pass)   |                            |
|                      v                           v                            |
|              ( Valid Records )          [ Quarantine Grid ]                   |
+----------------------|--------------------------------------------------------+
|
v
+-------------------------------------------------------------------------------+
|                               STEP 2: RENDER                                  |
|  ( Valid Records ) ---> ( state_manager.py ) ---> Manifest Locked (PENDING)   |
|                                                           |                   |
|                                                           v                   |
|  [ HTML Inject ] <--- ( Jinja2 Engine ) <--- ( pdf_engine.py / Playwright )   |
|        |                                                                      |
|        +---> [ Auto-Scale Fonts ] ---> [ Landscape A4 PDF Output ]            |
+-----------------------------------------------------------|-------------------+
|
v
+-------------------------------------------------------------------------------+
|                        STEP 3: THE CONFIRMATION GATE                          |
|  [ Visual Sandbox ] ---> Inspect Local Artifacts ---> Execute Dry-Run Sample  |
|                                                             |                 |
|                      +--------------------------------------+                 |
|                      |                                                        |
|                      +---> [ ABORT / KILL SWITCH ] (Halt Queue)               |
|                      |                                                        |
|                      +---> [ APPROVE & DISPATCH ]                             |
+-------------------------------------------------------------|-----------------+
|
v
+-------------------------------------------------------------------------------+
|                               STEP 4: DISPATCH                                |
|  ( mailer.py / smtplib TLS ) ---> Inject Anti-Spam Jitter (1.5s - 3.2s)       |
|              |                                                                |
|              +---> Live Terminal Telemetry ---> [ Audit Log CSV Export ]      |
+-------------------------------------------------------------------------------+

```

---

## ✨ Key Features

* **🛡️ Zero Cloud Exposure:** Your CSV mailing lists and SMTP credentials never leave your local OS network layer.
* **🧹 Smart Data Scrubbing:** Automatically strips Excel Byte-Order Marks (`utf-8-sig`), normalizes column headers, trims rogue whitespace, and enforces standard `Title Case` names.
* **📐 Auto-Scaling PDF Typography:** Dynamically evaluates string lengths. If a recipient's name exceeds 22 characters, the CSS font size scales down seamlessly to prevent horizontal container overflow.
* **💾 Idempotent Crash Recovery:** Tracks every individual recipient state (`PENDING`, `GENERATED`, `SENT`, `FAILED`) inside a local JSON checkpoint. If your computer crashes mid-dispatch, rebooting the app offers to **resume strictly from the first un-sent record**.
* **⏳ Anti-Spam Network Jitter:** Prevents automated SMTP server blocks (like Gmail Temporary Errors) by injecting randomized floating point delays (`random.uniform(1.5, 3.2)`) between mail dispatches.
* **🚨 Emergency Kill Switch:** A hardware-interrupt style software halt button instantly stops the outbound email queue mid-batch.

---

## 📂 Modular Directory Structure

```text
certiflow_pro/
│
├── .env.example                # Template for secure SMTP environment variables
├── .gitignore                  # Strict security blocks for secrets & runtime files
├── requirements.txt            # Locked production dependencies
├── config.py                   # Global constants, paths, and rate-limit settings
├── app.py                      # Main Streamlit Cockpit UI & State Controller
│
├── modules/
│   ├── __init__.py
│   ├── ingestor.py             # CSV loading, sanitization, and regex quarantine
│   ├── pdf_engine.py           # Playwright headless Chromium factory & Jinja2 inject
│   ├── mailer.py               # SMTP TLS dispatch, MIME attachments, & jitter logic
│   └── state_manager.py        # Checkpointing, resume logic, and audit CSV compiler
│
├── templates/
│   └── base_cert.html          # Clean, modern geometric A4 landscape HTML/CSS template
│
└── workspace/                  # Git-ignored local runtime storage folder
    ├── generated_pdfs/         # Temporary local PDF compilation storage
    ├── checkpoints/            # current_job.json state tracking
    └── audit_logs/             # Timestamped final settlement reports

```

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.11** or higher
* A mail account with **STARTTLS (Port 587)** access (e.g., Gmail with 2FA enabled).

### 1. Installation

Clone the repository and install the locked dependencies:

```bash
git clone [https://github.com/YOUR_GITHUB_USERNAME/certiflow-pro.git](https://github.com/YOUR_GITHUB_USERNAME/certiflow-pro.git)
cd certiflow-pro
pip install -r requirements.txt

```

### 2. Initialize Rendering Engine

CertiFlow Pro uses headless Chromium to render pixel-perfect modern CSS flexbox layouts natively across Windows, macOS, and Linux:

```bash
playwright install chromium

```

### 3. Configure Environment Secrets

Copy the configuration template and insert your mailing credentials:

```bash
# On Linux/macOS
cp .env.example .env

# On Windows (Command Prompt)
copy .env.example .env

```

Open `.env` in any text editor. **Note for Gmail users:** Do *not* use your standard login password. You must generate a 16-character **[Google App Password](https://myaccount.google.com/apppasswords)**.

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your16charapptoken

```

### 4. Launch Cockpit

Fire up the local Streamlit server:

```bash
streamlit run app.py

```

---

## 📋 CSV Schema Requirements

Your uploaded `.csv` file must contain at least two columns (case-insensitive): `Name` and `Email`. Optional columns will be dynamically mapped into the template variables.

| Name | Email | Course *(Optional)* | Date *(Optional)* |
| --- | --- | --- | --- |
| John Doe | john@company.com | Advanced Python | 15-03-2024 |
| Jane Smith | jane@company.com | Cloud Architecture | 16-03-2024 |

---

## 🛠️ Tech Stack & Engineering Specs

* **UI Controller:** `Streamlit` (Managing async event loops and HITL state flows)
* **Data Ingest:** `Pandas` (Regex array masking and Windows BOM sanitization)
* **PDF Engine:** `Playwright` + `Jinja2` (Headless Chromium printing to `@page { size: A4 landscape; }`)
* **Transport Layer:** Native Python `smtplib` + `email.mime` (STARTTLS / RFC 2822 compliance)

---

## 🔒 Security & Compliance

This tool was designed with a strict **Local-First** philosophy.

* No telemetry or analytics are collected.
* The `.gitignore` strictly blocks `.env` files and runtime workspace artifacts (`/generated_pdfs`, `/audit_logs`) from ever being committed to version control.
* Audit reports are generated strictly locally to verify settlement compliance.

---

## 📄 License

This project is licensed under the **MIT License**. Free for personal, academic, and commercial internal use.

