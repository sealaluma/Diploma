"""
Management command to test AI chatbot tools.

Usage:
    python manage.py test_tools
    python manage.py test_tools --verbose
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
import time

from ai_chatbot.ai_assistant.tools import (
    search_topics,
    search_supervisors,
    recommend_topics_by_skills,
    get_student_profile,
    call_tool
)
from profiles.models import StudentProfile, SupervisorProfile
from topics.models import ThesisTopic


class Command(BaseCommand):
    help = 'Test AI chatbot tools (Stage 1 testing)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each test'
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('🧪 AI CHATBOT TOOLS - STAGE 1 TESTING'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Track results
        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        # Test 1: search_topics
        self.stdout.write(self.style.WARNING('\n📋 TEST 1: search_topics()'))
        self.stdout.write('-'*80)

        try:
            # Test 1.1: Basic keyword search
            self.stdout.write('\nTest 1.1: Search ML topics...')
            start = time.time()
            results = search_topics(keywords=["machine learning", "ML", "AI"], limit=10)
            elapsed = time.time() - start

            total_tests += 1
            if results is not None:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: Found {len(results)} topics in {elapsed:.3f}s'))

                if verbose and len(results) > 0:
                    for i, topic in enumerate(results[:3], 1):
                        self.stdout.write(f'    {i}. Topic #{topic["id"]}: {topic["title"]}')
                        self.stdout.write(f'       Skills: {topic["required_skills"]}')
                        self.stdout.write(f'       Available: {topic["available"]}')
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR('  ❌ FAIL: Returned None'))

            # Test 1.2: Search by skills
            self.stdout.write('\nTest 1.2: Search topics with Python skill...')
            results = search_topics(required_skills=["Python"], limit=5)
            total_tests += 1

            if results is not None:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: Found {len(results)} Python topics'))

                if verbose and len(results) > 0:
                    for topic in results[:2]:
                        self.stdout.write(f'    - {topic["title"]}: {topic["required_skills"]}')
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR('  ❌ FAIL'))

            # Test 1.3: Empty results
            self.stdout.write('\nTest 1.3: Search non-existent topic...')
            results = search_topics(keywords=["xyz_nonexistent_quantum_computing_2099"])
            total_tests += 1

            if results is not None and len(results) == 0:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS('  ✅ PASS: Correctly returned empty list'))
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR(f'  ❌ FAIL: Expected [], got {len(results)} results'))

            # Test 1.4: Available topics only
            self.stdout.write('\nTest 1.4: Check availability filtering...')
            results = search_topics(available_only=True, limit=20)
            total_tests += 1

            unavailable_count = sum(1 for t in results if not t['available'])
            if unavailable_count == 0:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: All {len(results)} topics are available'))
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR(f'  ❌ FAIL: {unavailable_count} topics marked unavailable'))

        except Exception as e:
            failed_tests += 1
            self.stdout.write(self.style.ERROR(f'  ❌ ERROR: {str(e)}'))

        # Test 2: search_supervisors
        self.stdout.write(self.style.WARNING('\n\n📋 TEST 2: search_supervisors()'))
        self.stdout.write('-'*80)

        try:
            # Test 2.1: Search by research interests
            self.stdout.write('\nTest 2.1: Search ML supervisors...')
            start = time.time()
            results = search_supervisors(keywords=["machine learning", "AI"])
            elapsed = time.time() - start

            total_tests += 1
            if results is not None:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: Found {len(results)} ML supervisors in {elapsed:.3f}s'))

                if verbose and len(results) > 0:
                    for i, sup in enumerate(results[:3], 1):
                        self.stdout.write(f'    {i}. {sup["name"]} ({sup["email"]})')
                        self.stdout.write(f'       Teams: {sup["current_teams"]}/{sup["max_teams"]}')
                        research = sup['research_interests'][:80] + '...' if len(sup['research_interests']) > 80 else sup['research_interests']
                        self.stdout.write(f'       Research: {research}')
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR('  ❌ FAIL: Returned None'))

            # Test 2.2: Search by skills
            self.stdout.write('\nTest 2.2: Search supervisors with Python skills...')
            results = search_supervisors(skills=["Python"], limit=5)
            total_tests += 1

            if results is not None:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: Found {len(results)} Python supervisors'))

                if verbose and len(results) > 0:
                    for sup in results[:2]:
                        self.stdout.write(f'    - {sup["name"]}: {sup["skills"]}')
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR('  ❌ FAIL'))

            # Test 2.3: Availability check
            self.stdout.write('\nTest 2.3: Check availability filtering...')
            results = search_supervisors(available_only=True, limit=20)
            total_tests += 1

            unavailable_count = sum(1 for s in results if not s['available'])
            if unavailable_count == 0:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: All {len(results)} supervisors are available'))
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR(f'  ❌ FAIL: {unavailable_count} supervisors not available'))

            # Test 2.4: Multilingual search
            self.stdout.write('\nTest 2.4: Multilingual search (Russian)...')
            results = search_supervisors(keywords=["кибербезопасность", "безопасность"])
            total_tests += 1

            if results is not None:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: Found {len(results)} cybersecurity supervisors'))
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR('  ❌ FAIL'))

        except Exception as e:
            failed_tests += 1
            self.stdout.write(self.style.ERROR(f'  ❌ ERROR: {str(e)}'))

        # Test 3: recommend_topics_by_skills
        self.stdout.write(self.style.WARNING('\n\n📋 TEST 3: recommend_topics_by_skills()'))
        self.stdout.write('-'*80)

        try:
            # Get a test student
            student = StudentProfile.objects.filter(skills__isnull=False).first()

            if not student:
                self.stdout.write(self.style.WARNING('  ⚠️  SKIP: No students with skills found'))
                total_tests += 1
            else:
                student_skills = list(student.skills.values_list('name', flat=True))

                self.stdout.write(f'\nTest 3.1: Recommendations for student {student.user.email}')
                self.stdout.write(f'  Student skills: {student_skills}')

                start = time.time()
                results = recommend_topics_by_skills(student_id=student.user.id, limit=5)
                elapsed = time.time() - start

                total_tests += 1
                if results is not None:
                    passed_tests += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: Found {len(results)} recommendations in {elapsed:.3f}s'))

                    if verbose and len(results) > 0:
                        for i, rec in enumerate(results[:3], 1):
                            self.stdout.write(f'    {i}. Topic #{rec["id"]}: {rec["title"]}')
                            self.stdout.write(f'       Match: {rec["match_score"]}%')
                            self.stdout.write(f'       You have: {rec["matching_skills"]}')
                            self.stdout.write(f'       You need: {rec["missing_skills"]}')
                else:
                    failed_tests += 1
                    self.stdout.write(self.style.ERROR('  ❌ FAIL: Returned None'))

            # Test 3.2: Invalid student ID
            self.stdout.write('\nTest 3.2: Invalid student ID...')
            results = recommend_topics_by_skills(student_id=999999, limit=5)
            total_tests += 1

            if results == []:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS('  ✅ PASS: Correctly returned empty list'))
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR(f'  ❌ FAIL: Expected [], got {results}'))

        except Exception as e:
            failed_tests += 1
            self.stdout.write(self.style.ERROR(f'  ❌ ERROR: {str(e)}'))

        # Test 4: get_student_profile
        self.stdout.write(self.style.WARNING('\n\n📋 TEST 4: get_student_profile()'))
        self.stdout.write('-'*80)

        try:
            student = StudentProfile.objects.first()

            if not student:
                self.stdout.write(self.style.WARNING('  ⚠️  SKIP: No students found'))
                total_tests += 1
            else:
                self.stdout.write(f'\nTest 4.1: Get profile for {student.user.email}...')
                profile = get_student_profile(student_id=student.user.id)

                total_tests += 1
                if 'error' not in profile:
                    passed_tests += 1
                    self.stdout.write(self.style.SUCCESS('  ✅ PASS: Retrieved profile'))

                    if verbose:
                        self.stdout.write(f'    Name: {profile["name"]}')
                        self.stdout.write(f'    Email: {profile["email"]}')
                        self.stdout.write(f'    Skills: {profile["skills"]}')
                        self.stdout.write(f'    Specialization: {profile["specialization"]}')
                        self.stdout.write(f'    GPA: {profile["gpa"]}')
                else:
                    failed_tests += 1
                    self.stdout.write(self.style.ERROR(f'  ❌ FAIL: {profile["error"]}'))

            # Test 4.2: Invalid ID
            self.stdout.write('\nTest 4.2: Invalid student ID...')
            profile = get_student_profile(student_id=999999)
            total_tests += 1

            if 'error' in profile:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS('  ✅ PASS: Correctly returned error'))
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR('  ❌ FAIL: Should return error'))

        except Exception as e:
            failed_tests += 1
            self.stdout.write(self.style.ERROR(f'  ❌ ERROR: {str(e)}'))

        # Test 5: call_tool helper
        self.stdout.write(self.style.WARNING('\n\n📋 TEST 5: call_tool() helper'))
        self.stdout.write('-'*80)

        try:
            self.stdout.write('\nTest 5.1: Call tool by name...')
            results = call_tool('search_topics', keywords=['AI'], limit=3)
            total_tests += 1

            if results is not None:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ PASS: call_tool works ({len(results)} results)'))
            else:
                failed_tests += 1
                self.stdout.write(self.style.ERROR('  ❌ FAIL'))

            self.stdout.write('\nTest 5.2: Invalid tool name...')
            total_tests += 1
            try:
                call_tool('non_existent_tool')
                failed_tests += 1
                self.stdout.write(self.style.ERROR('  ❌ FAIL: Should raise ValueError'))
            except ValueError:
                passed_tests += 1
                self.stdout.write(self.style.SUCCESS('  ✅ PASS: Correctly raised ValueError'))

        except Exception as e:
            failed_tests += 1
            self.stdout.write(self.style.ERROR(f'  ❌ ERROR: {str(e)}'))

        # Database stats
        self.stdout.write(self.style.WARNING('\n\n📊 DATABASE STATISTICS'))
        self.stdout.write('-'*80)

        try:
            total_topics = ThesisTopic.objects.count()
            available_topics = ThesisTopic.objects.filter(team__isnull=True).count()
            total_supervisors = SupervisorProfile.objects.count()
            with_research = SupervisorProfile.objects.exclude(
                research_interests__isnull=True
            ).exclude(research_interests='').count()
            total_students = StudentProfile.objects.count()
            students_with_skills = StudentProfile.objects.filter(skills__isnull=False).distinct().count()

            self.stdout.write(f'\nTopics:')
            self.stdout.write(f'  Total: {total_topics}')
            self.stdout.write(f'  Available: {available_topics}')

            self.stdout.write(f'\nSupervisors:')
            self.stdout.write(f'  Total: {total_supervisors}')
            self.stdout.write(f'  With research interests: {with_research}')

            self.stdout.write(f'\nStudents:')
            self.stdout.write(f'  Total: {total_students}')
            self.stdout.write(f'  With skills: {students_with_skills}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error getting stats: {str(e)}'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('📈 TEST SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        self.stdout.write(f'Total tests: {total_tests}')
        self.stdout.write(self.style.SUCCESS(f'✅ Passed: {passed_tests}'))
        if failed_tests > 0:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {failed_tests}'))

        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        self.stdout.write(f'\nPass rate: {pass_rate:.1f}%')

        if failed_tests == 0:
            self.stdout.write(self.style.SUCCESS('\n🎉 ALL TESTS PASSED! Ready for Stage 2!\n'))
        else:
            self.stdout.write(self.style.ERROR('\n⚠️  Some tests failed. Check errors above.\n'))

        self.stdout.write('='*80 + '\n')
