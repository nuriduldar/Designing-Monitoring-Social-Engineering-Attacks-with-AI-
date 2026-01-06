# Appendix B: Project Repository

## Repository Overview

The complete source code, environment configurations, and deployment scripts for the "Social Engineering AI" project are hosted on GitHub. The repository is structured to support both development and production environments, ensuring modularity and reproducibility of the research findings.

**Repository URL:** [YOUR_GITHUB_REPO_URL]

## Repository Structure & Contents

### Core Application (`/sim_server`)

The Flask application containing the routing logic and 34+ RESTful API endpoints:

- **`app.py`**: Main Flask application with all route handlers
- **`generator_api.py`**: Integration logic for AI model APIs (Google Gemini, OpenAI GPT-4)
- **`detection_api.py`**: ML model inference endpoints for phishing detection
- **`analytics.py`**: Analytics and metrics calculation
- **`email_service.py`**: SMTP email service for sending simulated phishing emails
- **`review_manager.py`**: Human-in-the-loop review queue management
- **`translations.py`**: Multi-language support (English/Turkish)
- **`templates/`**: Front-end assets (HTML5, CSS3, JavaScript) for simulation UIs:
  - Email phishing scenarios
  - SMS phishing scenarios
  - Social media phishing scenarios
  - Spear phishing variants
  - Fake login pages
  - Analytics dashboard
  - Review queue interface

### Machine Learning Models (`/models`)

Pre-trained DistilBERT and TF-IDF model files, along with training scripts and validation datasets:

- **`distilbert_phishing_detector/`**: Pre-trained DistilBERT model weights and configuration
- **`phishing_detector_model.joblib`**: TF-IDF + Logistic Regression model
- **`phishing_detector_vectorizer.joblib`**: TF-IDF vectorizer
- **Training scripts** in `/detection/`:
  - `train_distilbert.py`: DistilBERT fine-tuning script
  - `train_tfidf_lr.py`: TF-IDF + Logistic Regression training
  - `eval_model.py`: Model evaluation utilities

### AI Integration (`/generator` & `/sim_server/services`)

Integration logic for the Google Gemini API and OpenAI GPT-4, including prompt engineering templates used for scenario generation:

- **`generate_phishing.py`**: Template-based phishing sample generator
- **`generate_with_llama.py`**: Local Llama-2 model integration
- **`generator_api_gemini.py`**: Google Gemini Pro API integration
- **`prompts.md`**: Prompt engineering templates and guidelines

### Data Storage (`/data`)

- **`sample_dataset.csv`**: Training dataset for ML models
- **`expanded_dataset.csv`**: Expanded dataset with additional samples
- **`generated_samples.jsonl`**: AI-generated phishing scenarios
- **`human_written_samples.jsonl`**: Human-written baseline scenarios
- **`translations_cache.json`**: Translation cache for performance optimization

### Configuration Files

- **`requirements.txt`**: Python dependencies for each module
- **`Dockerfile`**: Containerization configuration for Flask application
- **`docker-compose.yml`**: Multi-container orchestration (Flask + MailHog)
- **`.env.example`**: Environment variable template for API key management
- **`.gitignore`**: Comprehensive ignore rules for sensitive files (models, logs, API keys)

### Documentation (`/docs`)

- **`api_key_setup.md`**: API key configuration guide
- **`gemini_api_setup.md`**: Google Gemini API setup instructions
- **`deployment_guide.md`**: Production deployment guide
- **`ai_integration_guide.md`**: AI model integration documentation
- **`evaluation_criteria.md`**: Model evaluation criteria
- **`quick_commands.md`**: Common commands and shortcuts

### Ethics & Experiments (`/ethics` & `/experiments`)

- **`consent_form.txt`**: Participant consent form template
- **`pilot_protocol.md`**: Experiment protocol documentation
- **`survey_questionnaire.md`**: Pre/post-experiment survey templates

### Deployment Infrastructure

- **`/docker`**: Docker configuration files
- **`/vagrant`**: Vagrant + VirtualBox setup for isolated VM environments
- **`start_public.sh`**: Script for public network access
- **`check_security.sh`**: Pre-upload security validation script

## API Endpoints Documentation

The Flask application exposes 34+ RESTful API endpoints organized into functional categories:

### Scenario Management (8 endpoints)
- `GET /scenarios` - List all available scenarios
- `POST /scenarios/create` - Create new phishing scenario
- `DELETE /scenarios/delete/<id>` - Delete scenario
- `GET /scenario/<id>` - Render email phishing scenario
- `GET /scenario/<id>/spear` - Render spear phishing variant
- `GET /scenario/<id>/sms` - Render SMS phishing scenario
- `GET /scenario/<id>/login` - Render fake login page
- `GET /scenario/<id>/social` - Render social media phishing scenario

### AI Generation (2 endpoints)
- `POST /api/generate` - Generate phishing sample using AI models
- `GET /api/generate/models` - List available AI models (Gemini, GPT-4, Local)

### Detection Models (5 endpoints)
- `GET /api/model/status` - Check model availability and status
- `POST /api/model/test` - Test detection model with sample text
- `POST /api/model/train/tfidf-lr` - Train TF-IDF + Logistic Regression model
- `POST /api/model/train/distilbert` - Train DistilBERT model
- `GET /api/model/train/status` - Get training job status

### Review & Moderation (4 endpoints)
- `GET /review/queue` - Review queue interface
- `GET /review/queue/api` - Get review queue items (JSON)
- `POST /review/approve` - Approve message for use
- `POST /review/reject` - Reject message with reason
- `GET /review/stats` - Review statistics

### Analytics & Logging (5 endpoints)
- `GET /logs` - View interaction logs interface
- `GET /logs/view` - Get logs data (JSON API)
- `GET /stats` - Statistics dashboard
- `GET /analytics` - Analytics page
- `POST /click` - Log user interaction event

### Email Service (2 endpoints)
- `POST /email/send` - Send scenario email to participant
- `GET /email/test` - Test SMTP connection

### Surveys (3 endpoints)
- `GET /survey/pre` - Pre-experiment survey page
- `GET /survey/post` - Post-experiment survey page
- `POST /survey/submit` - Submit survey response

### Training & Management (2 endpoints)
- `GET /train` - Model training interface
- `GET /scenarios/manage` - Scenario management interface

### Localization (1 endpoint)
- `GET /set_language/<lang>` - Set interface language (en/tr)

## Quick Start Guide

To run the project locally, follow these steps:

### 1. Clone the Repository

```bash
git clone [YOUR_GITHUB_REPO_URL]
cd social-engineering-ai
```

### 2. Environment Setup

Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r sim_server/requirements.txt
```

### 3. API Configuration

Create a `.env` file from the template and add your API keys:

```bash
cp .env.example .env
# Edit .env and add:
# GEMINI_API_KEY=your_gemini_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here (optional)
```

**API Key Sources:**
- Google Gemini: https://aistudio.google.com/app/apikey
- OpenAI GPT-4: https://platform.openai.com/api-keys

### 4. Launch the Application

Execute the Flask development server:

```bash
python sim_server/app.py
```

### 5. Access the Dashboard

Open http://localhost:5000 in your web browser to access the dashboard.

## Alternative Deployment Methods

### Docker Compose

```bash
docker-compose up --build
```

Access:
- Flask app: http://localhost:5000
- MailHog UI: http://localhost:8025

### Vagrant (Isolated VM)

```bash
cd vagrant
vagrant up
vagrant ssh
cd /home/vagrant/project
source .venv/bin/activate
python sim_server/app.py
```

## Security & Privacy

### API Key Management

- All API keys are stored in `.env` file (excluded from version control)
- `.env` file is listed in `.gitignore`
- Never commit real API keys or secrets
- Use `.env.example` as a template

### Data Protection

- All interaction logs are stored locally
- Participant data should be anonymized before sharing
- Logs should be deleted after experiment completion per ethics policy
- Models directory is gitignored to prevent accidental sharing of training data

### Pre-Upload Security Checklist

Before uploading to GitHub:

1. Run security check: `./check_security.sh`
2. Verify `.env` is not tracked: `git status`
3. Ensure no hardcoded secrets in code
4. Review `SECURITY_NOTES.md`

## Dependencies

### Core Dependencies
- Flask 2.3+
- Python 3.11+
- scikit-learn (for TF-IDF + LR model)
- transformers (for DistilBERT)
- torch (for DistilBERT inference)

### Optional Dependencies
- google-generativeai (for Gemini API)
- openai (for GPT-4 API)
- transformers + torch (for local Llama-2)

See `sim_server/requirements.txt` for complete dependency list.

## License

MIT License - See `LICENSE` file for details.

## Citation

If you use this repository in your research, please cite:

```
[Your Citation Format Here]
```

## Contact & Support

For questions, issues, or contributions:
- Review documentation in `/docs` directory
- Check `SECURITY_NOTES.md` for security guidelines
- Refer to `experiments/pilot_protocol.md` for experiment setup

---

**Note:** This repository is maintained for research purposes. Always follow ethical guidelines and obtain proper IRB approval before conducting experiments with human participants.

