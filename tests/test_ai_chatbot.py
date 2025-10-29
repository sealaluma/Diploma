"""
AI Chatbot Complete Test Suite

This script tests the entire AI chatbot system:
1. Database setup (supervisors, topics, students)
2. Tool functions (search_topics, search_supervisors, recommend)
3. Gemini integration (function calling)
4. API endpoints (health check, chat)

Run: python test_ai_chatbot.py --email student@kbtu.kz --password YourPassword

For new developers: This verifies your setup is correct.
"""

import os
import sys
import django
import argparse
import requests
from datetime import datetime


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DTest.settings')
django.setup()

from profiles.models import StudentProfile, SupervisorProfile
from topics.models import ThesisTopic
from ai_chatbot.ai_assistant.tools import (
    search_topics,
    search_supervisors,
    recommend_topics_by_skills,
    get_student_profile
)


# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"   {text}")


def test_environment():
    """Test 1: Check environment setup"""
    print_header("Test 1: Environment Setup")

    all_good = True

    # Check GEMINI_API_KEY
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print_success(f"GEMINI_API_KEY configured ({api_key[:20]}...)")
    else:
        print_error("GEMINI_API_KEY not found in environment")
        print_info("Set in .env: GEMINI_API_KEY=your-key-here")
        all_good = False

    # Check database connection
    try:
        from django.db import connection
        connection.ensure_connection()
        print_success("Database connection successful")
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        all_good = False

    return all_good


def test_database_data():
    """Test 2: Check database has required data"""
    print_header("Test 2: Database Data")

    all_good = True

    # Check topics
    total_topics = ThesisTopic.objects.count()
    available_topics = ThesisTopic.objects.filter(team__isnull=True).count()

    if total_topics > 0:
        print_success(f"Topics: {total_topics} total, {available_topics} available")
    else:
        print_error("No topics in database")
        print_info("Create topics via admin or API")
        all_good = False

    # Check supervisors
    total_supervisors = SupervisorProfile.objects.count()
    with_research = SupervisorProfile.objects.exclude(
        research_interests__isnull=True
    ).exclude(research_interests='').count()

    if total_supervisors > 0:
        print_success(f"Supervisors: {total_supervisors} total")
        if with_research > 0:
            print_success(f"Supervisors with research interests: {with_research}")
        else:
            print_warning("No supervisors have research_interests set")
            print_info("Run: python manage.py import_supervisor_research <csv_file>")
    else:
        print_error("No supervisors in database")
        all_good = False

    # Check students
    total_students = StudentProfile.objects.count()
    with_skills = StudentProfile.objects.filter(skills__isnull=False).distinct().count()

    if total_students > 0:
        print_success(f"Students: {total_students} total")
        if with_skills > 0:
            print_success(f"Students with skills: {with_skills}")
        else:
            print_warning("No students have skills set")
    else:
        print_error("No students in database")
        all_good = False

    return all_good


def test_tools():
    """Test 3: Test tool functions"""
    print_header("Test 3: Tool Functions")

    all_good = True

    # Test 3.1: search_topics
    print("3.1. Testing search_topics()...")
    try:
        results = search_topics(keywords=['AI', 'ML'], limit=5)
        print_success(f"search_topics() - Found {len(results)} topics")
        if results:
            sample = results[0]
            print_info(f"Sample: {sample['title'][:50]}")
            print_info(f"Skills: {sample['required_skills']}")
    except Exception as e:
        print_error(f"search_topics() failed: {str(e)}")
        all_good = False

    # Test 3.2: search_supervisors
    print("\n3.2. Testing search_supervisors()...")
    try:
        results = search_supervisors(keywords=['AI'], limit=5)
        print_success(f"search_supervisors() - Found {len(results)} supervisors")
        if results:
            sample = results[0]
            print_info(f"Sample: {sample['name']} ({sample['email']})")
            print_info(f"Research: {sample['research_interests'][:60]}...")
    except Exception as e:
        print_error(f"search_supervisors() failed: {str(e)}")
        all_good = False

    # Test 3.3: recommend_topics_by_skills
    print("\n3.3. Testing recommend_topics_by_skills()...")
    try:
        student = StudentProfile.objects.filter(skills__isnull=False).first()
        if student:
            results = recommend_topics_by_skills(student_id=student.user.id, limit=5)
            print_success(f"recommend_topics_by_skills() - Found {len(results)} recommendations")
            if results:
                sample = results[0]
                print_info(f"Top match: {sample['title'][:50]} ({sample['match_score']}%)")
                print_info(f"Matching: {sample['matching_skills']}")
        else:
            print_warning("No students with skills - skipping recommendation test")
    except Exception as e:
        print_error(f"recommend_topics_by_skills() failed: {str(e)}")
        all_good = False

    # Test 3.4: get_student_profile
    print("\n3.4. Testing get_student_profile()...")
    try:
        student = StudentProfile.objects.first()
        if student:
            result = get_student_profile(student_id=student.user.id)
            if 'error' not in result:
                print_success(f"get_student_profile() - Retrieved profile")
                print_info(f"Student: {result['name']} ({result['email']})")
                print_info(f"Skills: {result['skills']}")
            else:
                print_error(f"get_student_profile() returned error: {result['error']}")
                all_good = False
        else:
            print_warning("No students in database - skipping profile test")
    except Exception as e:
        print_error(f"get_student_profile() failed: {str(e)}")
        all_good = False

    return all_good


def test_gemini_integration():
    """Test 4: Test Gemini function calling"""
    print_header("Test 4: Gemini Integration (Optional)")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print_warning("GEMINI_API_KEY not configured - skipping Gemini tests")
        return True

    print_info("Testing Gemini function calling...")
    print_info("(This uses your API quota - 50 requests/day on free tier)")

    try:
        from ai_chatbot.ai_assistant.chatbot import chat_with_ai

        student = StudentProfile.objects.filter(skills__isnull=False).first()
        if not student:
            print_warning("No student with skills - skipping Gemini test")
            return True

        print_info(f"Testing with student: {student.user.email}")

        response = chat_with_ai(
            user_message="Show me AI topics",
            user_profile=student
        )

        if 'error' in response:
            if '429' in str(response['error']):
                print_warning("Gemini API quota exceeded (50/day on free tier)")
                print_info("Wait until quota resets or use a different API key")
            else:
                print_error(f"Gemini error: {response['error']}")
            return False

        print_success("Gemini response received")
        print_info(f"Response length: {len(response.get('message', ''))} chars")

        if response.get('function_calls_made'):
            print_success(f"Function calls made: {len(response['function_calls_made'])}")
            for fc in response['function_calls_made']:
                print_info(f"  - {fc['name']}() called")

        return True

    except Exception as e:
        print_error(f"Gemini test failed: {str(e)}")
        return False


def test_api_endpoints(email, password, base_url):
    """Test 5: Test API endpoints"""
    print_header("Test 5: API Endpoints")

    if not email or not password:
        print_warning("No credentials provided - skipping API tests")
        print_info("Run with: python test_ai_chatbot.py --email user@kbtu.kz --password pass")
        return True

    all_good = True

    # Test 5.1: Login
    print("5.1. Testing login...")
    try:
        login_url = f"{base_url}/api/users/login/"
        response = requests.post(login_url, json={
            "email": email,
            "password": password
        })

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get('access')
            print_success("Login successful")
            print_info(f"Token: {access_token[:30]}...")
        else:
            print_error(f"Login failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False

    except Exception as e:
        print_error(f"Login test failed: {str(e)}")
        print_warning("Make sure server is running: python manage.py runserver")
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Test 5.2: Health check
    print("\n5.2. Testing /api/ai/health/...")
    try:
        health_url = f"{base_url}/api/ai/health/"
        response = requests.get(health_url, headers=headers)

        if response.status_code == 200:
            health = response.json()
            status = health.get('status', 'unknown')

            if status == 'ok':
                print_success("Health check: OK")
            elif status == 'warning':
                print_warning(f"Health check: Warning - {health.get('message')}")
            else:
                print_error(f"Health check: Error - {health.get('message')}")
                all_good = False

            checks = health.get('checks', {})
            for check_name, check_status in checks.items():
                icon = "✅" if check_status else "❌"
                print_info(f"{icon} {check_name}: {check_status}")
        else:
            print_error(f"Health check failed: {response.status_code}")
            all_good = False
    except Exception as e:
        print_error(f"Health check test failed: {str(e)}")
        all_good = False

    # Test 5.3: Chat endpoint
    print("\n5.3. Testing /api/ai/chat/...")
    try:
        chat_url = f"{base_url}/api/ai/chat/"

        # First check if we have API quota
        if not os.getenv('GEMINI_API_KEY'):
            print_warning("GEMINI_API_KEY not configured - skipping chat test")
            return all_good

        response = requests.post(chat_url,
            headers=headers,
            json={"message": "What topics do we have?"}
        )

        if response.status_code == 200:
            result = response.json()
            print_success("Chat endpoint working")
            print_info(f"Response: {result.get('message', '')[:100]}...")
        elif response.status_code == 403:
            print_warning("Profile incomplete or not a student")
        elif response.status_code == 429:
            print_warning("Rate limit or Gemini quota exceeded")
        else:
            print_error(f"Chat failed: {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            all_good = False

    except Exception as e:
        print_error(f"Chat test failed: {str(e)}")
        all_good = False

    return all_good


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Test AI Chatbot System')
    parser.add_argument('--email', help='Student email for API tests')
    parser.add_argument('--password', help='Student password for API tests')
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--skip-gemini', action='store_true', help='Skip Gemini tests')
    parser.add_argument('--skip-api', action='store_true', help='Skip API tests')

    args = parser.parse_args()

    print(f"\n{Colors.BOLD}AI Chatbot Test Suite{Colors.END}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # Run tests
    results['Environment'] = test_environment()
    results['Database'] = test_database_data()
    results['Tools'] = test_tools()

    if not args.skip_gemini:
        results['Gemini'] = test_gemini_integration()

    if not args.skip_api:
        results['API'] = test_api_endpoints(args.email, args.password, args.url)

    # Summary
    print_header("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, test_result in results.items():
        icon = "✅" if test_result else "❌"
        status = "PASSED" if test_result else "FAILED"
        color = Colors.GREEN if test_result else Colors.RED
        print(f"{icon} {test_name}: {color}{status}{Colors.END}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! AI Chatbot is ready to use.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Check the output above for details.{Colors.END}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
