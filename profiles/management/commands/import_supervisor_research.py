"""
Management command to import supervisor research interests from CSV

Usage:
    python manage.py import_supervisor_research /path/to/supervisors.csv
"""

import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import CustomUser
from profiles.models import SupervisorProfile


class Command(BaseCommand):
    help = 'Import supervisor research interests from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file with supervisor data'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Skip first 2 header rows
                next(f)
                next(f)

                reader = csv.reader(f)

                # Skip the column headers row
                headers = next(reader)
                # Expected: ['№', 'Ф.И.О', 'Почта', 'Область исследования...']

                updated_count = 0
                not_found_count = 0
                skipped_count = 0

                self.stdout.write(self.style.SUCCESS(f'\n📊 Starting import from: {csv_file}\n'))
                self.stdout.write('=' * 80)

                for row in reader:
                    if len(row) < 4:
                        continue

                    number = row[0].strip()
                    name = row[1].strip()
                    email = row[2].strip()
                    research = row[3].strip()

                    # Skip empty rows
                    if not email or not research:
                        continue

                    try:
                        # Find user by email
                        user = CustomUser.objects.get(email=email, role='Supervisor')

                        # Get supervisor profile
                        profile = user.supervisor_profile

                        # Check if already has research_interests
                        if profile.research_interests:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⚠️  {email} already has research_interests, updating...'
                                )
                            )

                        # Update research_interests
                        if not dry_run:
                            profile.research_interests = research
                            profile.save()

                        # Show success
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ {number}. {name} ({email})\n'
                                f'   Research: {research[:100]}...' if len(research) > 100 else f'   Research: {research}'
                            )
                        )
                        updated_count += 1

                    except CustomUser.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'❌ User not found: {email}')
                        )
                        not_found_count += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Error updating {email}: {str(e)}')
                        )
                        not_found_count += 1

                # Summary
                self.stdout.write('\n' + '=' * 80)
                self.stdout.write(self.style.SUCCESS(f'\n📈 IMPORT SUMMARY:\n'))
                self.stdout.write(f'  ✅ Updated: {updated_count}')
                self.stdout.write(f'  ❌ Not found: {not_found_count}')
                self.stdout.write(f'  ⏭️  Skipped: {skipped_count}')
                self.stdout.write(f'  📊 Total: {updated_count + not_found_count + skipped_count}\n')

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING('\n⚠️  This was a DRY RUN - no changes were saved!')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('Run without --dry-run to apply changes')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Import completed successfully!')
                    )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'❌ File not found: {csv_file}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
