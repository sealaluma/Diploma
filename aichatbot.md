# AI Chatbot Setup & Usage Guide

## Overview

The AI Chatbot is an intelligent assistant that helps students find thesis topics, supervisors, and get personalized recommendations using Google Gemini AI with function calling.

**Features:**
- 🔍 Search thesis topics by keywords (ML, AI, web dev, etc.)
- 👨‍🏫 Find supervisors by research interests
- 🎯 Get personalized topic recommendations based on skills
- 💬 Natural language conversation with real database queries

---

## Quick Setup (5 Steps)

### Step 1: Get Gemini API Key

1. Visit: **https://aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click: **"Get API Key"** or **"Create API Key"**
4. Copy the generated API key

**Free Tier:**
- 50 requests per day
- Perfect for development

### Step 2: Configure Environment

Add to your `.env` file:

```bash
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### Step 3: Setup Supervisors

You need supervisors with research interests for the AI to search.

**Important:** Supervisor email in database **MUST MATCH** email in your CSV file.

#### 3.1. Create Supervisor Accounts

Either via Django admin or shell:

```bash
python manage.py shell
```

```python
from users.models import CustomUser
from profiles.models import SupervisorProfile

# Create supervisor (email MUST match CSV!)
user = CustomUser.objects.create_user(
    email='a.akshabaev@kbtu.kz',  # Must match CSV email
    password='SupervisorPass123!',
    role='Supervisor'
)

# Profile auto-created, just set names
profile = SupervisorProfile.objects.get(user=user)
profile.first_name = 'Askar'
profile.last_name = 'Akshabaev'
profile.save()

print(f"✅ Created: {user.email}")
```

#### 3.2. Import Research Interests

**Prepare CSV file:**
```csv
Email,Research Interests
a.akshabaev@kbtu.kz,"Development (backend, frontend, mobile). Can be related to AI"
t.umarov@kbtu.kz,"Model-Driven Architecture, Formal methods, AI applications, ML"
```

**Run import command:**
```bash
python manage.py import_supervisor_research "/path/to/supervisor_research.csv"
```

This matches supervisors by email and adds their research interests.

### Step 4: Create Test Student

```bash
python manage.py shell
```

```python
from users.models import CustomUser
from profiles.models import StudentProfile, Skill

# Create student
user = CustomUser.objects.create_user(
    email='test.student@kbtu.kz',
    password='TestPass123!',
    role='Student'
)

# Complete profile
profile = StudentProfile.objects.get(user=user)
profile.first_name = 'Test'
profile.last_name = 'Student'
profile.specialization = 'Computer Science'
profile.gpa = 3.5
profile.save()

# Add skills (important for recommendations!)
python_skill, _ = Skill.objects.get_or_create(name='Python')
js_skill, _ = Skill.objects.get_or_create(name='JavaScript')
profile.skills.add(python_skill, js_skill)

# Mark complete
user.is_profile_completed = True
user.save()

print(f"✅ Created student: {user.email}")
```

### Step 5: Run Tests

```bash
# Run comprehensive test
python test_ai_chatbot.py --email test.student@kbtu.kz --password TestPass123!

# Or skip API tests if server isn't running
python test_ai_chatbot.py --skip-api

# Or skip Gemini tests if quota exceeded
python test_ai_chatbot.py --skip-gemini
```

**Expected output:**
```
✅ Environment: PASSED
✅ Database: PASSED
✅ Tools: PASSED
✅ Gemini: PASSED
✅ API: PASSED

🎉 All tests passed! AI Chatbot is ready to use.
```

---

## Usage Examples

### Example 1: Using API

```bash
# 1. Start server
python manage.py runserver

# 2. Get JWT token
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test.student@kbtu.kz", "password": "TestPass123!"}'

# 3. Chat with AI
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me AI topics"}'
```

**Response:**
```json
{
  "message": "Here are AI topics:\n\n1. Computer Vision Project\n   Skills: Python, TensorFlow\n   Status: Available ✅\n\n2. NLP Chatbot\n   Skills: Python, NLP\n   Status: Taken"
}
```

### Example 2: Direct Function Usage

```python
from ai_chatbot.ai_assistant.tools import search_topics, search_supervisors

# Search topics
topics = search_topics(keywords=['AI', 'machine learning'], limit=5)
print(f"Found {len(topics)} topics")

# Search supervisors
supervisors = search_supervisors(keywords=['AI'], limit=3)
for sup in supervisors:
    print(f"{sup['name']}: {sup['research_interests'][:60]}...")
```

---

## API Endpoints

### POST `/api/ai/chat/`

Send a message to the AI chatbot.

**Headers:**
- `Authorization: Bearer <jwt_token>`
- `Content-Type: application/json`

**Request:**
```json
{
  "message": "What projects do you recommend for me?"
}
```

**Response:**
```json
{
  "message": "Based on your skills (Python, JavaScript), I recommend:\n\n1. Web App (85% match)\n   You have: Python, JavaScript\n   You need: React"
}
```

**Debug mode:** Add `?debug=true` to see function calls

### GET `/api/ai/health/`

Check if chatbot is operational.

**Response:**
```json
{
  "status": "ok",
  "message": "AI Chatbot is fully operational",
  "checks": {
    "gemini_api_key": true,
    "database": true,
    "student_profile": true,
    "profile_completed": true
  }
}
```

---

## Troubleshooting

### Issue: "GEMINI_API_KEY not found"

```bash
# Check .env file
cat .env | grep GEMINI_API_KEY

# If missing, add it
echo 'GEMINI_API_KEY=your-key-here' >> .env
```

### Issue: "No supervisors found"

**Reason:** Supervisors don't have `research_interests` set.

**Solution:** Run the import command:
```bash
python manage.py import_supervisor_research "/path/to/csv"
```

**Verify:**
```python
from profiles.models import SupervisorProfile

sups = SupervisorProfile.objects.exclude(research_interests__isnull=True).exclude(research_interests='')
print(f"Supervisors with research: {sups.count()}")
```

### Issue: "Gemini quota exceeded"

**Error:** `429 RESOURCE_EXHAUSTED`

**Reason:** Free tier is 50 requests/day.

**Solutions:**
- Wait until quota resets (midnight Pacific Time)
- Get a new API key
- Upgrade to paid tier

### Issue: "Profile incomplete"

**Error:** `403 Forbidden`

**Reason:** Student profile not completed.

**Solution:**
```python
from users.models import CustomUser

user = CustomUser.objects.get(email='student@kbtu.kz')
user.is_profile_completed = True
user.save()
```

---

## How It Works

### Architecture

```
User Question
    ↓
API Endpoint (/api/ai/chat/)
    ↓
chatbot.py orchestrates:
    ↓
llm_client.py → Gemini API
    ↓
Gemini decides which functions to call
    ↓
tools.py → Database queries
    ↓
Results back to Gemini
    ↓
Gemini formats response
    ↓
Return to user
```

### Function Calling

Gemini has access to 4 functions:

1. **search_topics** - Search by keywords/skills
2. **search_supervisors** - Find supervisors by research area
3. **recommend_topics_by_skills** - Personalized recommendations
4. **get_student_profile** - Get student info

When you ask: *"Show me ML topics"*

Gemini:
1. Analyzes your message
2. Calls: `search_topics(keywords=['ML', 'machine learning'])`
3. Gets results from database
4. Formats nice response

---

## Important Notes

### Database Requirements

- **Topics:** Need topics with required skills
- **Supervisors:** Must have `research_interests` field populated (via CSV import)
- **Students:** Need skills for recommendations to work
- **Skills:** Common skills should exist (Python, JavaScript, etc.)

### Email Matching

**Critical:** When importing research interests from CSV:

```csv
Email,Research Interests
a.akshabaev@kbtu.kz,"AI, ML, Backend"
```

The email **MUST EXACTLY MATCH** the supervisor's email in the database.

If mismatch:
- Database: `akshabaev@kbtu.kz`
- CSV: `a.akshabaev@kbtu.kz`
- ❌ Won't match! Research interests won't be imported.

### Rate Limiting

Currently **disabled** for testing. For production:

Uncomment in `ai_chatbot/views.py`:
```python
# @throttle_classes([AIChatbotThrottle])  # Remove comment
```

---

## Cost Estimation

### Free Tier (Google AI Studio)
- **Limit:** 50 requests/day
- **Cost:** $0
- **Perfect for:** Development, testing, demos

### Paid Tier (Google Cloud)
- **Gemini 2.0 Flash:** ~$0.075 per 1K input tokens, ~$0.30 per 1K output tokens
- **Average request:** ~500 tokens = $0.02-0.05
- **1000 requests/day:** ~$30-50/month

---

## Files Reference

### Core Files
- `ai_chatbot/ai_assistant/tools.py` - 4 database search functions
- `ai_chatbot/ai_assistant/llm_client.py` - Gemini client with function declarations
- `ai_chatbot/ai_assistant/chatbot.py` - Orchestration logic
- `ai_chatbot/views.py` - REST API endpoints
- `ai_chatbot/serializers.py` - Request/response validation

### Test File
- `test_ai_chatbot.py` - Comprehensive test suite (tests everything!)

---

## Quick Test Commands

```bash
# Test everything (recommended)
python tests/test_ai_chatbot.py --email student@kbtu.kz --password pass

# Test without API (if server not running)
python tests/test_ai_chatbot.py --skip-api

# Test without Gemini (if quota exceeded)
python tests/test_ai_chatbot.py --skip-gemini

# Test specific parts in Django shell
python manage.py shell
>>> from ai_chatbot.ai_assistant.tools import search_topics
>>> results = search_topics(keywords=['AI'])
>>> print(len(results))
```

---

## Checklist for New Developers

- [ ] Get Gemini API key from https://aistudio.google.com/apikey
- [ ] Add `GEMINI_API_KEY` to `.env` file
- [ ] Create supervisor accounts (**emails must match CSV!**)
- [ ] Import research interests: `python manage.py import_supervisor_research <csv>`
- [ ] Create test student with skills
- [ ] Run test script: `python test_ai_chatbot.py`
- [ ] Verify all tests pass
- [ ] Start server and test API

---

## Support

**Test Script:** `python test_ai_chatbot.py` will tell you what's wrong!

**Common Fix:** Most issues are:
1. Missing `GEMINI_API_KEY`
2. Supervisors missing `research_interests`
3. Student profile incomplete

Run the test script to diagnose! 🚀

---

**Last Updated:** January 2025
**Version:** 1.0
