# Deployment Guide: Hugging Face Spaces

This guide explains how to deploy the AI Customer Support Resolution System to Hugging Face Spaces.

## Prerequisites

- Hugging Face account (create at https://huggingface.co)
- Git installed locally
- Docker account (optional, for image versioning)

## Step-by-Step Deployment

### 1. Create a New Space on Hugging Face

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Fill in the form:
   - **Space name**: `customer-support-resolution`
   - **Space type**: `Docker`
   - **Visibility**: `Public` or `Private`
   - **Persisted storage**: Not required (optional)
4. Click "Create Space"

### 2. Clone Your New Space Locally

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/customer-support-resolution
cd customer-support-resolution
```

### 3. Copy Project Files

Copy all files from this project to the Space directory:

```bash
cp customer_support_env.py <space-dir>/
cp Inference.py <space-dir>/
cp requirements.txt <space-dir>/
cp openenv.yaml <space-dir>/
cp Dockerfile <space-dir>/
cp README.md <space-dir>/
```

Directory structure should look like:
```
customer-support-resolution/
├── customer_support_env.py
├── Inference.py
├── requirements.txt
├── openenv.yaml
├── Dockerfile
└── README.md
```

### 4. Push to Hugging Face

```bash
cd customer-support-resolution
git add .
git commit -m "Add AI Customer Support Resolution System"
git push
```

Hugging Face will automatically detect the Dockerfile and build your Space.

### 5. Set Environment Variables

Once the Space is deployed:

1. Go to your Space settings (gear icon)
2. Click "Repository" or "Variables"
3. Add the following environment variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `HF_TOKEN` | `hf_xxxxx...` | Your Hugging Face API token |
| `API_BASE_URL` | `https://router.huggingface.co/v1` | API endpoint |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | Model to use |
| `CUSTOMER_SUPPORT_TASK` | `email_triage` | Default task |

**To get your HF_TOKEN:**
- Go to https://huggingface.co/settings/tokens
- Click "New token"  
- Select "Read" or "Write" access
- Copy the token

### 6. Verify Deployment

Once the Space builds successfully:

1. Your Space URL will be: `https://YOUR_USERNAME-customer-support-resolution.hf.space`

2. Test the endpoint:
```bash
curl https://YOUR_USERNAME-customer-support-resolution.hf.space/
```

3. Run the inference with different tasks:
```bash
# Via web interface or API - the space will automatically run Inference.py
```

### 7. Monitor Logs

Access Space logs to debug:
1. Go to your Space settings
2. Click "Logs"
3. View real-time output and errors

## Continuous Deployment

Any changes pushed to the Space repository will trigger automatic redeployment:

```bash
# Make changes locally
git add .
git commit -m "Update model or configuration"
git push  # Automatically redeploys!
```

## Environment Variable Options

### Task Selection
```bash
CUSTOMER_SUPPORT_TASK=email_triage        # Easy
CUSTOMER_SUPPORT_TASK=ticket_priority     # Medium
CUSTOMER_SUPPORT_TASK=multi_turn_resolution  # Hard
```

### Model Selection
```bash
# Using Hugging Face Inference API
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"

# Or other models
MODEL_NAME="meta-llama/Llama-2-70b-chat-hf"
MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.1"
```

### API Endpoints
```bash
# Hugging Face (recommended)
API_BASE_URL="https://router.huggingface.co/v1"

# OpenAI-compatible endpoints
API_BASE_URL="https://api.openai.com/v1"
API_BASE_URL="https://vllm-server-endpoint"
```

### Reproducibility
```bash
CUSTOMER_SUPPORT_SEED=42              # Set for reproducible results
```

## Scaling Configuration

For high-traffic deployments, configure in Dockerfile:

```dockerfile
# Increase resource allocation
ENV TIMEOUT=600
ENV MAX_STEPS=8
ENV MAX_WORKERS=4
```

## Troubleshooting

### Build Failures
**Error**: `Docker build failed`
- Check Dockerfile syntax
- Ensure all required files are present
- View full logs in Space settings

### Runtime Errors  
**Error**: `HF_TOKEN not found`
- Verify environment variables are set in Space settings
- Restart the Space after setting variables

**Error**: `Model not found`
- Verify MODEL_NAME is valid
- Check API_BASE_URL is accessible
- Ensure HF_TOKEN has sufficient permissions

### API Connection Issues
**Error**: `Failed to connect to API endpoint`
- Test API endpoint with curl:
  ```bash
  curl -H "Authorization: Bearer $HF_TOKEN" \
    https://router.huggingface.co/v1/models
  ```
- Verify internet connectivity
- Check firewall/proxy settings

## Performance Optimization

### Reduce Memory Usage
```dockerfile
# Use smaller base image
FROM python:3.10-slim
RUN pip install --no-cache-dir -r requirements.txt
```

### Faster Cold Starts
1. Pre-warm model cache
2. Use model caching strategies
3. Optimize Dockerfile layer caching

### Cost Optimization
- Use free tier API quotas for development
- Upgrade to paid API for production
- Monitor usage in HF dashboard

## Production Best Practices

1. **Use API keys securely**
   - Never commit secrets to git
   - Use Space secrets/environment variables
   - Rotate API keys regularly

2. **Implement logging**
   - Log all inferences for auditing
   - Track performance metrics
   - Monitor error rates

3. **Set up health checks**
   - Included in Dockerfile with HEALTHCHECK
   - Test endpoint `/health` regularly
   - Alert on failures

4. **Version control**
   - Tag releases: `git tag v1.0.0`
   - Document changes in git history
   - Maintain CHANGELOG.md

5. **Documentation**
   - Keep README.md updated
   - Document environment variables
   - Provide usage examples

## Integration Examples

### cURL Request
```bash
# Access your Space (runs Inference.py)
curl https://YOUR_USERNAME-customer-support-resolution.hf.space/
```

### Python Client
```python
import requests

space_url = "https://YOUR_USERNAME-customer-support-resolution.hf.space"
response = requests.get(space_url)
print(response.text)
```

### GitHub Actions CI/CD
```yaml
name: Deploy to HF Spaces

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Push to HF Spaces
        run: |
          git push https://huggingface.co/YOUR_USERNAME/customer-support-resolution
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
```

## Support

For issues with:
- **Hugging Face Spaces**: https://huggingface.co/docs/hub/spaces
- **Docker on HF**: https://huggingface.co/docs/hub/spaces-dockerfile
- **This environment**: See README.md troubleshooting section

## Additional Resources

- HF Spaces Documentation: https://huggingface.co/docs/hub/spaces
- OpenEnv Specification: https://github.com/openenv/spec
- Docker Reference: https://docs.docker.com/reference/
- OpenAI API: https://platform.openai.com/docs/api-reference

---

**Happy Deploying!** 🚀
