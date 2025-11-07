# AI Chatbot Module - Project Structure

## Overview

This module provides an AI-powered chatbot to help students find thesis topics, supervisors, and get project recommendations.

**Status**: ⚠️ **Skeleton/Structure Only** - Implementation pending

---

## 📁 Project Structure

```
ai_chatbot/
├── ai_assistant/                   # Core AI logic module
│   ├── __init__.py                # Module exports
│   ├── chatbot.py                 # Main chatbot orchestration
│   ├── context_builder.py         # Database context retrieval
│   ├── prompt_builder.py          # LLM prompt construction
│   ├── llm_client.py              # Gemini API integration
│   └── recommender.py             # Algorithmic recommendations (optional)
│
├── migrations/                     # Database migrations (if needed)
│   └── __init__.py
│
├── __init__.py                     # App initialization
├── admin.py                        # Django admin configuration
├── apps.py                         # App configuration
├── models.py                       # Database models (if needed)
├── serializers.py                  # DRF serializers
├── throttles.py                    # Rate limiting
├── urls.py                         # URL routing
├── views.py                        # API endpoints
├── tests.py                        # Unit tests (TODO)
└── README.md                       # This file
```

---

## 🚀 API Endpoints

Base URL: `/api/ai/`

### 1. **POST /api/ai/chat/**
Main chatbot endpoint for AI interactions.

**Request:**
```json
{
  "message": "I'm looking for machine learning projects"
}
```

**Response:**
```json
{
  "message": "AI response text with recommendations...",
  "suggested_topics": [15, 23, 47],
  "suggested_supervisors": [5, 12]
}
```

**Authentication**: Required (JWT)
**Rate Limit**: 10 requests/hour, 3 requests/minute (burst)
**Status**: ⚠️ Not implemented (returns 501)

### 2. **GET /api/ai/health/**
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "AI Chatbot is operational"
}
```

**Authentication**: Required (JWT)
**Status**: ✅ Partial (returns placeholder)

---

## 🏗️ Module Components

### **ai_assistant/chatbot.py**
Main orchestration logic.

**Functions:**
- `chat_with_ai(user_message, user_profile)` - Main entry point
- `analyze_intent(user_message)` - Intent classification (optional)

**Flow:**
1. Receive user message
2. Get database context
3. Build LLM prompt
4. Call Gemini API
5. Parse and return response

---

### **ai_assistant/context_builder.py**
Retrieves data from database and formats for LLM.

**Functions:**
- `get_topics_context(filters)` - Format available topics
- `get_supervisors_context(filters)` - Format available supervisors
- `get_student_context(student_profile)` - Format student info
- `filter_relevant_topics(...)` - Pre-filter topics (optimization)

**Output Example:**
```
AVAILABLE THESIS TOPICS:

Topic #15: Image Classification using CNNs
Description: This project focuses on...
Required Skills: Python, TensorFlow, Computer Vision
Supervisor: Dr. Ivanov (5/10 teams available)
---
```

---

### **ai_assistant/prompt_builder.py**
Constructs prompts for the LLM.

**Functions:**
- `build_chat_prompt(...)` - Build complete prompt
- `build_multilingual_prompt(...)` - Add language support (future)

**Templates:**
- `SYSTEM_PROMPT` - System instructions for LLM
- `RESPONSE_FORMAT_INSTRUCTIONS` - How to format responses

---

### **ai_assistant/llm_client.py**
Handles Gemini API communication.

**Functions:**
- `call_gemini(prompt, temperature, max_tokens)` - API call
- `parse_llm_response(raw_response)` - Extract structured data
- `estimate_token_count(text)` - Monitor prompt size

**Configuration:**
- Model: `gemini-2.5-flash` (reuses existing integration)
- API Key: `GEMINI_API_KEY` environment variable

---

### **ai_assistant/recommender.py**
Algorithmic recommendations (optional - can rely on LLM).

**Functions:**
- `calculate_topic_match_score(student, topic)` - Scoring algorithm
- `recommend_topics(student_profile, limit)` - Top N topics
- `recommend_supervisors(skills, topic, limit)` - Top N supervisors

**Use Cases:**
- Pre-filtering before sending to LLM
- Fallback if LLM fails
- Hybrid approach (algorithm + LLM)

---

## 🔧 Implementation Approach

### **Simple Context Injection (Recommended)**

```
User Question
    ↓
Query Database (Topics, Supervisors)
    ↓
Format as Plain Text Context
    ↓
Send to Gemini with User Question
    ↓
Return AI Response
```

**Why this approach?**
- ✅ Simple: No RAG, no vector databases
- ✅ Small dataset: ~56 supervisors, ~100 topics
- ✅ Real-time: Always fresh data
- ✅ Cost-effective: Direct DB queries
- ✅ Fast: PostgreSQL is efficient

**NOT using RAG because:**
- Dataset is small (all data fits in prompt)
- Structured data (PostgreSQL handles it well)
- No need for semantic search
- No unstructured documents

---

## 🛡️ Security & Rate Limiting

### **Rate Limits**
Reuses existing AI rate limiting from `topics/throttles.py`:

| User Type | Limit | Scope |
|-----------|-------|-------|
| Authenticated | 10/hour | `ai_enhancement_user` |
| Authenticated | 3/minute | `ai_enhancement_burst` |

### **Authentication**
- JWT required for all endpoints
- User must have StudentProfile

### **Input Validation**
- Message: 1-2000 characters
- Sanitization: Strip whitespace, check for empty

---

## 📋 Implementation Checklist

### **Phase 1: MVP (Core Functionality)**
- [ ] Implement `get_topics_context()` - Query and format topics
- [ ] Implement `get_supervisors_context()` - Query and format supervisors
- [ ] Implement `get_student_context()` - Format student profile
- [ ] Implement `build_chat_prompt()` - Construct LLM prompt
- [ ] Implement `call_gemini()` - Reuse from `topics/ai_enhancement`
- [ ] Implement `chat_with_ai()` - Orchestrate the flow
- [ ] Implement `ai_chat()` view - Handle API request/response
- [ ] Write tests for chatbot logic
- [ ] Test end-to-end with real queries

### **Phase 2: Enhancements**
- [ ] Add response parsing (`parse_llm_response()`)
- [ ] Extract topic/supervisor IDs from response
- [ ] Implement smart filtering (`filter_relevant_topics()`)
- [ ] Add intent classification (optional)
- [ ] Implement recommendation scoring (optional)
- [ ] Add multilingual support (EN/KZ/RU)

### **Phase 3: Advanced Features**
- [ ] Store chat history in database
- [ ] Add conversation memory (multi-turn)
- [ ] WebSocket support for streaming responses
- [ ] Admin analytics dashboard
- [ ] A/B testing different prompts

---

## 🧪 Testing

### **Manual Testing**
```bash
# Get JWT token
TOKEN=$(curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"password"}' \
  | jq -r '.access')

# Test health check
curl http://localhost:8000/api/ai/health/ \
  -H "Authorization: Bearer $TOKEN"

# Test chatbot (once implemented)
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need a machine learning project"}'
```

### **Unit Tests**
```bash
python manage.py test ai_chatbot
```

---

## 💡 Example Conversations

### **Example 1: Find ML Projects**
**User:** "I'm interested in machine learning projects"

**AI Response:**
```
I found 3 machine learning projects that match your interests:

1. Topic #15: Image Classification using CNNs
   - Skills: Python, TensorFlow, Computer Vision
   - Supervisor: Dr. Ivanov (5/10 teams available)
   - This matches your Python and ML skills well!

2. Topic #23: NLP Sentiment Analysis
   - Skills: Python, NLP, Deep Learning
   - Supervisor: Dr. Petrov (3/10 teams available)
   - Great for text processing experience

Would you like more details on any of these topics?
```

### **Example 2: Find Available Supervisors**
**User:** "Who are the available supervisors for computer vision?"

**AI Response:**
```
Here are 2 supervisors specializing in computer vision with availability:

1. Dr. Ivanov (5/10 teams)
   - Expertise: Computer Vision, Deep Learning, Image Processing
   - Research: Neural networks, object detection

2. Dr. Kozlov (2/10 teams)
   - Expertise: Computer Vision, Robotics, OpenCV
   - Research: Autonomous systems, visual SLAM

Both supervisors are currently accepting new teams!
```

---

## 🔗 Related Files

- **Rate Limiting**: `/topics/throttles.py` - Reused throttle classes
- **AI Integration**: `/topics/ai_enhancement/enhancer.py` - Gemini client reference
- **Settings**: `/DTest/settings.py` - Rate limits configuration
- **Main URLs**: `/DTest/urls.py` - URL routing

---

## 📚 Next Steps

1. **Start with context builders** - Implement database queries first
2. **Test context output** - Verify formatted text looks good
3. **Integrate Gemini** - Reuse existing code from `topics/ai_enhancement`
4. **Build prompt** - Craft effective system prompt
5. **Wire up view** - Connect everything in `ai_chat()` view
6. **Test extensively** - Try different questions and edge cases
7. **Iterate on prompt** - Refine based on response quality

---

## 🤔 Design Decisions

### **Why not RAG?**
- Small dataset (~56 supervisors, ~100 topics)
- All data fits in LLM context window
- Simple PostgreSQL queries are sufficient
- No need for vector embeddings

### **Why reuse rate limits?**
- Same cost profile (Gemini API calls)
- Consistent user experience
- Simpler configuration

### **Why separate app?**
- Clear separation of concerns
- Independent development/testing
- Can be disabled without affecting other features

---

## 📞 Support

For questions or issues:
1. Check function TODOs for implementation guidance
2. Review existing AI enhancement code in `topics/ai_enhancement/`
3. Consult Django REST Framework docs for API patterns
4. Test with small examples first

---

**Status**: ⚠️ Structure complete, implementation pending
**Last Updated**: 2025-10-28
