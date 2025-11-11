# AI Rate Limiting - Frontend Developer Guide

## Overview

All AI-powered features use **dual-layer rate limiting**:

1. **DRF Throttles** - Hourly and per-minute limits (burst protection)
2. **Custom Quota System** - Daily usage limits (resets at midnight)

---

## AI Topic Enhancement Endpoint

### Endpoint Details

```
POST /api/topics/enhance/
```

**Authentication:** JWT Bearer Token required

**Request Body:**
```json
{
  "description": "Your project description",  // Required, 10-5000 chars
  "title_en": "English title",                // Optional, max 500 chars
  "title_kz": "Kazakh title",                 // Optional, max 500 chars
  "title_ru": "Russian title"                 // Optional, max 500 chars
}
```

**Success Response (200 OK):**
```json
{
  "enhanced_title_en": "AI-enhanced English title",
  "enhanced_title_kz": "AI-enhanced Kazakh title",
  "enhanced_title_ru": "AI-enhanced Russian title",
  "enhanced_description": "AI-enhanced description text..."
}
```

---

## Rate Limits

### Layer 1: DRF Throttles (Time-Based)

| Type | Limit | Description |
|------|-------|-------------|
| **Hourly** | 10 requests/hour | Rolling 60-minute window per user |
| **Burst** | 3 requests/minute | Prevents rapid spam |

### Layer 2: Custom Quota (Daily Limit)

| Feature | Daily Limit | Reset Time |
|---------|-------------|------------|
| **Topic Enhancement** | 3 requests/day | Midnight (00:00 server time) |

### How Limits Work Together

**The most restrictive limit applies:**
- First 3 requests within 1 minute → ✅ Pass
- 4th request within same minute → ❌ **Blocked** (burst: 3/min)
- After 1 minute → 4th request → ✅ Pass (under hourly limit)
- After 3 successful requests same day → ❌ **Blocked** (daily quota: 3/day)
- After midnight → ✅ Quota resets to 0

---

## Get User's Quota Status

### Endpoint

```
GET /api/quota/
```

**Authentication:** JWT Bearer Token required

**Response:**
```json
{
  "topic_enhancements": {
    "used": 2,
    "limit": 3,
    "remaining": 1,
    "resets_at": "2025-11-08T00:00:00+06:00"
  },
  "chatbot_messages": {
    "used": 5,
    "limit": 7,
    "remaining": 2,
    "resets_at": "2025-11-08T00:00:00+06:00"
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `used` | integer | Number of requests used today |
| `limit` | integer | Maximum requests allowed per day |
| `remaining` | integer | Requests left today (`limit - used`) |
| `resets_at` | ISO 8601 timestamp | When quota resets (midnight) |

**Use this endpoint to:**
- Display "2/3 enhancements used today"
- Show progress bar of quota usage
- Disable button when `remaining = 0`
- Show countdown to `resets_at` time

---

## Error Responses

### 1. Daily Quota Exceeded (429)

**When:** User has used all 3 daily enhancements

```json
{
  "error": "Rate limit exceeded",
  "detail": "Daily limit reached (3/3 Topic Enhancements used). Resets at midnight.",
  "used": 3,
  "limit": 3,
  "remaining": 0,
  "resets_at": "2025-11-08T00:00:00+06:00"
}
```

**Frontend should show:**
- "Daily limit reached (3/3 enhancements used)"
- "Resets at midnight" with countdown timer
- Disable enhancement button

---

### 2. Burst/Hourly Throttle Exceeded (429)

**When:** User sent >3 requests per minute OR >10 requests per hour

```json
{
  "detail": "Request was throttled. Expected available in 45 seconds."
}
```

**Frontend should show:**
- "Please wait 45 seconds before trying again"
- Countdown timer
- Temporarily disable button

---

### 3. Validation Errors (400)

```json
{
  "error": "Description is required"
}
```

```json
{
  "error": "Description is too short (minimum 10 characters)"
}
```

```json
{
  "error": "Description is too long (maximum 5000 characters)"
}
```

```json
{
  "error": "English title is too long (maximum 500 characters)"
}
```

---

### 4. Authentication Error (401)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Frontend should:**
- Redirect to login
- Clear JWT token from storage

---

### 5. Server Error (500)

```json
{
  "error": "Failed to enhance thesis content. Please try again later."
}
```

**Note:** User's quota is **NOT consumed** when this error occurs.

---

## Recommended UI Flow

1. **On page load:**
   - Call `GET /api/quota/`
   - Display: "2/3 AI enhancements remaining today"
   - If `remaining = 0`: disable button, show reset countdown

2. **Before submission:**
   - Check if `remaining > 0`
   - If no quota left, prevent submission

3. **After successful enhancement:**
   - Decrement displayed count: "1/3 remaining"
   - Or refresh quota: call `GET /api/quota/` again

4. **On 429 error:**
   - Parse response
   - If `resets_at` exists → daily quota exceeded
   - If `detail` contains "seconds" → throttle exceeded
   - Show appropriate message and countdown

---

## Configuration (Backend)

**DRF Throttle Rates** (`DTest/settings.py`):
```python
'DEFAULT_THROTTLE_RATES': {
    'ai_enhancement_user': '10/hour',
    'ai_enhancement_burst': '3/minute',
}
```

**Daily Quota Limits** (`DTest/settings.py`):
```python
AI_RATE_LIMITS = {
    'topic_enhancement': 3,  # 3 per day
    'chatbot_message': 7,    # 7 per day
}
```

Can be overridden with environment variables:
- `AI_TOPIC_ENHANCEMENT_DAILY_LIMIT=3`
- `AI_CHATBOT_DAILY_LIMIT=7`

---

## Testing

```bash
# Login and get token
TOKEN=$(curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass"}' | jq -r '.access')

# Check quota
curl http://localhost:8000/api/quota/ \
  -H "Authorization: Bearer $TOKEN"

# Test enhancement
curl -X POST http://localhost:8000/api/topics/enhance/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Test project description"}'
```

**Expected:**
- First 3 requests → 200 OK
- 4th request same day → 429 with quota error
- After midnight → quota resets

---

**Last Updated:** 2025-11-07
