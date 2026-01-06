# Security Notes

## Important Reminders

### Production Use
- **DO NOT** deploy this to production environments
- This is a research and educational prototype only
- Not intended for real-world security operations

### Credentials & Data
- **DO NOT** store real credentials anywhere in this project
- All simulated phishing messages must contain `[TEST ENVIRONMENT]` tag
- Never ask participants to enter real credentials
- All interaction logs should be anonymized before sharing

### Logs & Data Retention
- Delete logs after experiment completion per ethics policy
- Review `ethics/consent_form.txt` for data deletion timeline
- Ensure compliance with local data protection regulations (GDPR, etc.)

### API Keys
- Never commit `.env` file to version control
- Use `.env.example` as a template
- Rotate API keys if accidentally exposed

### Generated Content
- Always perform human-in-the-loop review of generated messages
- Check `generator/blocked_outputs.log` for flagged content
- Verify all outputs contain `[TEST ENVIRONMENT]` tag

### Network Security
- When running experiments, use isolated networks
- Do not expose services to public internet without proper security measures
- Use MailHog or similar test SMTP servers, never real email services

### Model Security
- Trained models in `models/` directory are gitignored
- Do not share trained models without reviewing their training data
- Ensure training data does not contain sensitive information

## Best Practices

1. **Before each experiment:**
   - Review ethics approval
   - Verify consent forms are signed
   - Check that all safety measures are in place

2. **During experiments:**
   - Monitor logs for unexpected behavior
   - Review generated content before use
   - Ensure participants understand this is a test environment

3. **After experiments:**
   - Anonymize all data
   - Delete logs per retention policy
   - Archive only anonymized, aggregated results

## Reporting Issues

If you discover security vulnerabilities:
1. Do not create public issues
2. Contact project maintainers privately
3. Follow responsible disclosure practices

