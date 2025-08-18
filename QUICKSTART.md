# 🚀 Quick Start Guide

Get the Sample OpenRouter Backend running in minutes!

## ⚡ Super Quick Start (Windows)

1. **Run the setup script:**
   ```cmd
   scripts\setup.bat
   ```

2. **Or use PowerShell:**
   ```powershell
   scripts\setup.ps1
   ```

3. **Start the service:**
   ```cmd
   python app\main.py
   ```

4. **Test the API:**
   ```cmd
   python scripts\test_api.py
   ```

## 🔧 Manual Setup

### 1. Install Dependencies
```bash
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy the example file
copy env.example .env

# Edit .env and add your keys:
# OPENROUTER_API_KEY=your_key_here
# SECRET_KEY=your_secret_here
```

### 3. Run the Service
```bash
python app\main.py
```

## 🧪 Test Your Setup

### Generate a Token
```bash
python scripts\generate_token.py --user-id test_user
```

### Test the API
```bash
python scripts\test_api.py
```

### Manual Test
```bash
# Health check
curl http://localhost:8000/health

# Generate token
curl -X POST "http://localhost:8000/auth/token?user_id=test_user"

# Use token (replace YOUR_TOKEN)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"prompt_text": "Hello!"}' \
     http://localhost:8000/ask-llm
```

## 🌐 Access Points

- **Service**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🐳 Docker Alternative

```bash
docker-compose up --build
```

## 📚 What's Next?

1. **Read the full README.md** for detailed information
2. **Explore the API documentation** at `/docs`
3. **Customize prompts** in `app/prompts.py`
4. **Deploy to GCP** using `deploy_gcp.sh`

## 🆘 Need Help?

- Check the logs for error details
- Verify your `.env` file is configured
- Ensure the virtual environment is activated
- Check that port 8000 is available

---

**Happy coding! 🎉**
