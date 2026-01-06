# Social Engineering AI - Ethical Phishing Simulation & Detection

## Overview

This project is a comprehensive research platform for ethical phishing simulation and detection. It provides tools for generating simulated phishing messages (with built-in safety constraints), a web-based simulation server with 34+ RESTful API endpoints, and machine learning-based detection models including DistilBERT and TF-IDF classifiers.

**⚠️ IMPORTANT:** This is a research and educational prototype only. **DO NOT** use against real users without proper ethics approval and IRB clearance.

## Features

- **AI-Powered Generation**: Generate phishing scenarios using Google Gemini Pro API, OpenAI GPT-4, or local templates
- **Multi-Channel Simulation**: Email, SMS, and Social Media phishing scenarios
- **ML Detection Models**: Pre-trained DistilBERT and TF-IDF + Logistic Regression models
- **Web Dashboard**: Full-featured web interface for scenario management, analytics, and model training
- **Human-in-the-Loop Review**: Built-in review queue system for content moderation
- **Multi-Language Support**: English and Turkish language interfaces
- **Analytics & Logging**: Comprehensive interaction logging and analytics dashboard
- **Ethical Safeguards**: Automatic safety checks and `[TEST ENVIRONMENT]` tagging

## Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for containerized deployment)
- Vagrant & VirtualBox (optional, for isolated VM environment)
- Google Gemini API key (optional, for AI generation)
- OpenAI API key (optional, for GPT-4 generation)

## Quick Start

### Option 1: One-Click Launch (macOS)

Double-click `BAŞLAT.command` to automatically:
- Start the Flask server
- Open your browser
- Install dependencies if needed

### Option 2: Manual Setup

1. **Clone the repository:**
   ```bash
   git clone [YOUR_GITHUB_REPO_URL]
   cd social-engineering-ai
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r sim_server/requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY (optional)
   ```

4. **Start the server:**
   ```bash
   python3 sim_server/app.py
   ```

5. **Access the dashboard:**
   ```
   http://localhost:5000
   ```

### Option 3: Docker Deployment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys (optional)

# Build and run
docker-compose up --build
```

Access:
- Flask app: http://localhost:5000
- MailHog UI: http://localhost:8025

### Option 4: Vagrant (Isolated VM)

```bash
cd vagrant
vagrant up
vagrant ssh
cd /home/vagrant/project
source .venv/bin/activate
python sim_server/app.py
```

## Project Structure

```
social-engineering-ai/
├── sim_server/          # Flask application (34+ API endpoints)
│   ├── app.py          # Main Flask application
│   ├── generator_api.py # AI generation integration
│   ├── detection_api.py # ML model inference
│   ├── analytics.py    # Analytics and metrics
│   ├── email_service.py # SMTP email service
│   └── templates/      # HTML templates
├── generator/           # Phishing sample generators
│   ├── generate_phishing.py      # Template-based generator
│   ├── generate_with_llama.py    # Llama-2 local model
│   └── generator_api_gemini.py   # Gemini API integration
├── detection/           # ML detection models
│   ├── train_distilbert.py       # DistilBERT training
│   ├── train_tfidf_lr.py        # TF-IDF + LR training
│   └── eval_model.py            # Model evaluation
├── data/               # Datasets and samples
│   ├── sample_dataset.csv
│   ├── generated_samples.jsonl
│   └── human_written_samples.jsonl
├── models/             # Trained models (gitignored)
├── ethics/             # Ethics documentation
├── experiments/        # Experiment protocols
├── docs/              # Additional documentation
├── docker/            # Docker configuration
└── vagrant/           # Vagrant configuration
```

## API Endpoints

The Flask application provides 34+ RESTful API endpoints organized into the following categories:

### Scenario Management
- `GET /scenarios` - List all scenarios
- `POST /scenarios/create` - Create new scenario
- `DELETE /scenarios/delete/<id>` - Delete scenario
- `GET /scenario/<id>` - View scenario (Email)
- `GET /scenario/<id>/spear` - Spear phishing variant
- `GET /scenario/<id>/sms` - SMS variant
- `GET /scenario/<id>/login` - Fake login page
- `GET /scenario/<id>/social` - Social media variant

### AI Generation
- `POST /api/generate` - Generate phishing sample
- `GET /api/generate/models` - List available AI models

### Detection Models
- `GET /api/model/status` - Check model availability
- `POST /api/model/test` - Test model with sample text
- `POST /api/model/train/tfidf-lr` - Train TF-IDF + LR model
- `POST /api/model/train/distilbert` - Train DistilBERT model
- `GET /api/model/train/status` - Training status

### Review & Moderation
- `GET /review/queue` - Review queue page
- `GET /review/queue/api` - Get review queue (JSON)
- `POST /review/approve` - Approve message
- `POST /review/reject` - Reject message
- `GET /review/stats` - Review statistics

### Analytics & Logging
- `GET /logs` - View interaction logs
- `GET /logs/view` - Logs API endpoint
- `GET /stats` - Statistics dashboard
- `GET /analytics` - Analytics page
- `POST /click` - Log user interaction

### Email Service
- `POST /email/send` - Send scenario email
- `GET /email/test` - Test SMTP connection

### Surveys
- `GET /survey/pre` - Pre-experiment survey
- `GET /survey/post` - Post-experiment survey
- `POST /survey/submit` - Submit survey response

### Training & Management
- `GET /train` - Model training page
- `GET /scenarios/manage` - Scenario management page

### Localization
- `GET /set_language/<lang>` - Set interface language

## Usage

### Generating Phishing Samples

**Via Web Interface:**
1. Navigate to http://localhost:5000
2. Click "Generate New Sample"
3. Select AI model (Gemini Pro, GPT-4, or Local Templates)
4. Configure tone, target role, and count
5. Review generated content in the review queue

**Via Command Line:**
```bash
cd generator
python generate_phishing.py --tone urgent --role employee
```

**Local Mode (No AI):**
```bash
python generate_phishing.py --local
```

### Training Detection Models

**Via Web Interface:**
1. Navigate to http://localhost:5000/train
2. Select model type (TF-IDF + LR or DistilBERT)
3. Click "Train Model"
4. View training metrics upon completion

**Via Command Line:**
```bash
cd detection
# TF-IDF + Logistic Regression
python train_tfidf_lr.py --data-path ../data/sample_dataset.csv

# DistilBERT
python train_distilbert.py --data-path ../data/sample_dataset.csv
```

### Evaluating Models

```bash
cd detection
python eval_model.py --text "Your email text here"
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```env
# AI API Keys (optional)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
SECRET_KEY=generate-secure-random-key-for-production
LOG_PATH=interaction_logs.csv

# SMTP Configuration (optional, defaults to MailHog)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
```

**Security Note:** Never commit `.env` to version control. The `.env` file is already in `.gitignore`.

## Ethical Warnings & Checklist

⚠️ **CRITICAL:** Before using this with real participants:

- [ ] Obtain IRB/Ethics Committee approval
- [ ] Review and customize `ethics/consent_form.txt`
- [ ] Ensure all participants sign informed consent
- [ ] Verify all generated messages contain `[TEST ENVIRONMENT]` tag
- [ ] Review all generated messages manually (human-in-the-loop)
- [ ] Never ask participants to enter real credentials
- [ ] Anonymize all collected data
- [ ] Delete logs after experiment completion per ethics policy
- [ ] Store data securely and limit access

**DO NOT:**
- Deploy to production environments
- Use against real users without approval
- Store real credentials
- Skip human review of generated content

## Security

### API Key Management

- All API keys are stored in `.env` file (gitignored)
- Never hardcode API keys in source code
- Use `.env.example` as a template for configuration
- Rotate API keys if accidentally exposed

### Before Uploading to GitHub

1. **Run security check:**
   ```bash
   ./check_security.sh
   ```

2. **Verify `.env` is not tracked:**
   ```bash
   git status
   git ls-files | grep -E "\.env$|\.csv$|\.log$"
   ```

3. **Ensure no hardcoded secrets:**
   - No API keys in code
   - No credentials in logs
   - No personal information

See `SECURITY_NOTES.md` for detailed security guidelines.

## Data & Logs

- **Interaction logs**: `interaction_logs.csv` (configurable via `LOG_PATH`)
- **Log format**: `timestamp,participant_id,scenario_id,action,metadata`
- **Generated samples**: `data/generated_samples.jsonl`
- **Blocked outputs**: `generator/blocked_outputs.log`

**Anonymization:** Before sharing or publishing, ensure all participant IDs are anonymized and personal information is removed.

## Deployment

### Public Access (Same Network)

```bash
./start_public.sh
# Share: http://YOUR_IP:5000
```

### Public Access (Internet - Ngrok)

```bash
# Install ngrok
brew install ngrok

# Configure auth token
ngrok config add-authtoken YOUR_TOKEN

# Start Flask (Terminal 1)
python3 sim_server/app.py

# Start ngrok (Terminal 2)
ngrok http 5000

# Share the ngrok URL
```

See `docs/deployment_guide.md` for detailed deployment instructions.

## License

MIT License - See `LICENSE` file

## Support & Documentation

- `docs/quick_commands.md` - Common commands and shortcuts
- `docs/api_key_setup.md` - API key configuration guide
- `docs/gemini_api_setup.md` - Gemini API setup
- `docs/deployment_guide.md` - Deployment instructions
- `docs/ai_integration_guide.md` - AI model integration
- `experiments/pilot_protocol.md` - Experiment protocol
- `SECURITY_NOTES.md` - Security best practices

## Repository Information

See `REPOSITORY_INFO.md` for detailed repository structure, API endpoint documentation, and deployment information suitable for academic papers and documentation.

---

**Remember:** This is a research tool. Always prioritize ethics and participant safety.
