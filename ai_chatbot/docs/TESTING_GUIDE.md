# Stage 1 Testing Guide: Tools (Database Functions)

## 🎯 Goal
Test that search functions work correctly **without AI integration**.

---

## ✅ Prerequisites

1. Migration completed: `research_interests` field exists
2. CSV data imported: Supervisors have research interests
3. Database has some topics and students

---

## 🧪 Test 1: search_topics()

### **Test 1.1: Basic keyword search**

```bash
python manage.py shell
```

```python
from ai_chatbot.ai_assistant.tools import search_topics

# Test 1: Search for ML topics
results = search_topics(keywords=["machine learning", "ML", "AI"])
print(f"Found {len(results)} ML topics")

for topic in results:
    print(f"\nTopic #{topic['id']}: {topic['title']}")
    print(f"  Skills: {topic['required_skills']}")
    print(f"  Available: {topic['available']}")
    print(f"  Description: {topic['description'][:100]}...")
```

**Expected output:**
```
Found 5 ML topics

Topic #15: Image Classification using CNNs
  Skills: ['Python', 'TensorFlow', 'Computer Vision']
  Available: True
  Description: Build a deep learning model for image recognition...

Topic #23: NLP Sentiment Analysis
  Skills: ['Python', 'NLP', 'NLTK']
  Available: True
  Description: Analyze social media sentiment...
```

---

### **Test 1.2: Search by skills**

```python
# Test 2: Search topics requiring Python
results = search_topics(
    required_skills=["Python"],
    available_only=True,
    limit=5
)

print(f"\nFound {len(results)} topics requiring Python")
for topic in results:
    print(f"- {topic['title']}: {topic['required_skills']}")
```

**Expected output:**
```
Found 5 topics requiring Python
- Image Classification: ['Python', 'TensorFlow', 'Computer Vision']
- Web Scraper: ['Python', 'BeautifulSoup', 'Selenium']
- Data Pipeline: ['Python', 'Pandas', 'SQL']
```

---

### **Test 1.3: Search with keywords AND skills**

```python
# Test 3: ML topics that need Python
results = search_topics(
    keywords=["machine learning"],
    required_skills=["Python"],
    limit=5
)

print(f"\nFound {len(results)} ML topics with Python")
for topic in results:
    print(f"- {topic['title']}")
    print(f"  Required: {topic['required_skills']}")
```

---

### **Test 1.4: Empty results**

```python
# Test 4: Search for non-existent topic
results = search_topics(keywords=["quantum_computing_xyz_nonexistent"])
print(f"\nFound {len(results)} results (should be 0)")
```

**Expected:** `Found 0 results`

---

### **Test 1.5: All available topics**

```python
# Test 5: Get all available topics
results = search_topics(available_only=True, limit=20)
print(f"\nTotal available topics: {len(results)}")

# Check availability
for topic in results:
    if not topic['available']:
        print(f"ERROR: Topic #{topic['id']} marked available but has team!")
```

---

## 🧪 Test 2: search_supervisors()

### **Test 2.1: Search by research interests**

```python
from ai_chatbot.ai_assistant.tools import search_supervisors

# Test 1: Find ML supervisors
results = search_supervisors(keywords=["machine learning", "AI"])
print(f"\nFound {len(results)} ML supervisors")

for sup in results:
    print(f"\n{sup['name']} ({sup['email']})")
    print(f"  Research: {sup['research_interests'][:100]}...")
    print(f"  Skills: {sup['skills']}")
    print(f"  Teams: {sup['current_teams']}/{sup['max_teams']}")
    print(f"  Available: {sup['available']}")
```

**Expected output:**
```
Found 5 ML supervisors

Jaylet Olivier (o.jaylet@kbtu.kz)
  Research: Machine learning, Data Analysis, Predictive modelling, Computer vision...
  Skills: ['Python', 'ML', 'Data Science']
  Teams: 3/10
  Available: True

Bigadevanahalli Mruthyunjaya (a.bigadevanahalli@kbtu.kz)
  Research: Application on AI In Business, Generative and Agentic AI...
  Skills: ['AI', 'Data Analytics', 'Cloud']
  Teams: 5/10
  Available: True
```

---

### **Test 2.2: Search by skills**

```python
# Test 2: Find supervisors with Python skills
results = search_supervisors(skills=["Python"])
print(f"\nFound {len(results)} Python supervisors")

for sup in results:
    print(f"- {sup['name']}: {sup['skills']}")
```

---

### **Test 2.3: Multilingual search**

```python
# Test 3: Search in Russian
results = search_supervisors(keywords=["кибербезопасность"])
print(f"\nFound {len(results)} cybersecurity supervisors")

for sup in results:
    print(f"- {sup['name']}")
    print(f"  Research: {sup['research_interests'][:80]}...")
```

**Expected:** Should find supervisors like "Жаксалыков Темирлан" with cybersecurity research

---

### **Test 2.4: Check availability filtering**

```python
# Test 4: Only available supervisors
available_sups = search_supervisors(available_only=True, limit=10)
print(f"\nAvailable supervisors: {len(available_sups)}")

for sup in available_sups:
    if sup['current_teams'] >= 10:
        print(f"ERROR: {sup['name']} has {sup['current_teams']} teams but marked available!")
```

---

### **Test 2.5: All supervisors**

```python
# Test 5: Get all supervisors with research interests
results = search_supervisors(available_only=False, limit=50)
print(f"\nTotal supervisors with research: {len(results)}")

# Check which have no research_interests
no_research = [s for s in results if s['research_interests'] == 'Not specified']
print(f"Without research interests: {len(no_research)}")
```

---

## 🧪 Test 3: recommend_topics_by_skills()

### **Test 3.1: Get recommendations for student**

```python
from ai_chatbot.ai_assistant.tools import recommend_topics_by_skills

# First, find a student ID
from profiles.models import StudentProfile
student = StudentProfile.objects.first()
print(f"Testing with student: {student.user.email}")
print(f"Student skills: {list(student.skills.values_list('name', flat=True))}")

# Get recommendations
recommendations = recommend_topics_by_skills(student_id=student.user.id, limit=5)
print(f"\nFound {len(recommendations)} recommendations")

for rec in recommendations:
    print(f"\nTopic #{rec['id']}: {rec['title']}")
    print(f"  Match: {rec['match_score']}%")
    print(f"  You have: {rec['matching_skills']}")
    print(f"  You need: {rec['missing_skills']}")
    print(f"  Required: {rec['required_skills']}")
```

**Expected output:**
```
Testing with student: john.doe@kbtu.kz
Student skills: ['Python', 'JavaScript', 'React']

Found 5 recommendations

Topic #15: Image Classification
  Match: 67%
  You have: ['Python']
  You need: ['TensorFlow', 'Computer Vision']
  Required: ['Python', 'TensorFlow', 'Computer Vision']

Topic #23: Web Development
  Match: 100%
  You have: ['Python', 'JavaScript', 'React']
  You need: []
  Required: ['Python', 'JavaScript', 'React']
```

---

### **Test 3.2: Student with no skills**

```python
# Test 2: Student without skills
student_no_skills = StudentProfile.objects.create(
    user=...,  # Create test user first
    first_name="Test",
    last_name="Student"
)

recommendations = recommend_topics_by_skills(student_id=student_no_skills.user.id)
print(f"Recommendations for student with no skills: {len(recommendations)}")
# Expected: 0 or []
```

---

### **Test 3.3: Non-existent student**

```python
# Test 3: Invalid student ID
recommendations = recommend_topics_by_skills(student_id=999999)
print(f"Recommendations for invalid ID: {recommendations}")
# Expected: []
```

---

## 🧪 Test 4: get_student_profile()

### **Test 4.1: Get existing student**

```python
from ai_chatbot.ai_assistant.tools import get_student_profile

# Get first student
student = StudentProfile.objects.first()
profile = get_student_profile(student_id=student.user.id)

print(f"\nStudent Profile:")
print(f"  Name: {profile['name']}")
print(f"  Email: {profile['email']}")
print(f"  Skills: {profile['skills']}")
print(f"  Specialization: {profile['specialization']}")
print(f"  GPA: {profile['gpa']}")
```

**Expected output:**
```
Student Profile:
  Name: John Doe
  Email: john.doe@kbtu.kz
  Skills: ['Python', 'JavaScript', 'React']
  Specialization: Computer Systems and Software
  GPA: 3.8
```

---

### **Test 4.2: Non-existent student**

```python
# Test: Invalid ID
profile = get_student_profile(student_id=999999)
print(profile)
# Expected: {'error': 'Student with ID 999999 not found'}
```

---

## 🧪 Test 5: call_tool() Helper

### **Test 5.1: Call tool by name**

```python
from ai_chatbot.ai_assistant.tools import call_tool

# Test 1: Call search_topics
results = call_tool('search_topics', keywords=['AI'], limit=3)
print(f"Found {len(results)} topics via call_tool")

# Test 2: Call search_supervisors
results = call_tool('search_supervisors', keywords=['web development'])
print(f"Found {len(results)} supervisors via call_tool")
```

---

### **Test 5.2: Invalid tool name**

```python
# Test: Non-existent tool
try:
    call_tool('non_existent_tool')
except ValueError as e:
    print(f"Error caught: {e}")
    # Expected: "Tool 'non_existent_tool' not found..."
```

---

## ✅ Success Criteria

After running all tests, you should verify:

### **search_topics:**
- ✅ Returns results for valid keywords
- ✅ Filters by skills correctly
- ✅ Returns only available topics when `available_only=True`
- ✅ Returns empty list for non-existent topics
- ✅ Handles multilingual search (English/Russian/Kazakh)

### **search_supervisors:**
- ✅ Finds supervisors by research_interests keywords
- ✅ Filters by skills correctly
- ✅ Returns only available supervisors when `available_only=True`
- ✅ Shows correct team counts (0-10)
- ✅ Handles multilingual research interests

### **recommend_topics_by_skills:**
- ✅ Returns topics sorted by match score (highest first)
- ✅ Calculates match percentage correctly
- ✅ Shows matching and missing skills
- ✅ Returns empty list for students with no skills
- ✅ Handles non-existent student IDs

### **get_student_profile:**
- ✅ Returns complete student information
- ✅ Includes skills list
- ✅ Returns error for non-existent students

---

## 🐛 Common Issues

### **Issue 1: No results found**

**Problem:** `search_topics` returns empty list

**Debug:**
```python
# Check if topics exist
from topics.models import ThesisTopic
print(f"Total topics: {ThesisTopic.objects.count()}")

# Check specific topic
topic = ThesisTopic.objects.first()
print(f"Sample topic: {topic.title}")
print(f"Description: {topic.description}")
print(f"Skills: {list(topic.required_skills.values_list('name', flat=True))}")
```

---

### **Issue 2: Supervisors not found**

**Problem:** `search_supervisors` returns empty

**Debug:**
```python
# Check if supervisors have research_interests
from profiles.models import SupervisorProfile

sups = SupervisorProfile.objects.all()
print(f"Total supervisors: {sups.count()}")

with_research = sups.exclude(research_interests__isnull=True).exclude(research_interests='')
print(f"With research interests: {with_research.count()}")

# Check sample
sup = with_research.first()
if sup:
    print(f"\nSample: {sup.first_name} {sup.last_name}")
    print(f"Research: {sup.research_interests[:200]}")
```

---

### **Issue 3: Skills not matching**

**Problem:** Filtering by skills doesn't work

**Debug:**
```python
# Check skill names
from profiles.models import Skill
skills = Skill.objects.all()
print(f"Total skills: {skills.count()}")
print(f"Sample skills: {list(skills.values_list('name', flat=True)[:10])}")

# Check case sensitivity
python_skill = Skill.objects.filter(name__icontains='python')
print(f"Python skill variations: {list(python_skill.values_list('name', flat=True))}")
```

---

## 📊 Performance Check

### **Test query speed:**

```python
import time

# Test search_topics performance
start = time.time()
results = search_topics(keywords=['machine learning'], limit=10)
elapsed = time.time() - start
print(f"search_topics took {elapsed:.3f} seconds")
# Expected: < 0.1 seconds for 50-100 topics

# Test search_supervisors performance
start = time.time()
results = search_supervisors(keywords=['AI'], limit=10)
elapsed = time.time() - start
print(f"search_supervisors took {elapsed:.3f} seconds")
# Expected: < 0.1 seconds for 50 supervisors

# Test recommend_topics_by_skills performance
student = StudentProfile.objects.first()
start = time.time()
results = recommend_topics_by_skills(student_id=student.user.id, limit=10)
elapsed = time.time() - start
print(f"recommend_topics_by_skills took {elapsed:.3f} seconds")
# Expected: < 0.2 seconds for 50-100 topics
```

---

## ✅ Stage 1 Complete!

Once all tests pass, you're ready for **Stage 2: AI Integration**!

**Checklist:**
- [ ] All search functions work correctly
- [ ] No errors in Django shell
- [ ] Results are accurate and formatted properly
- [ ] Performance is acceptable (< 0.2s per query)
- [ ] Ready to integrate with Gemini AI
