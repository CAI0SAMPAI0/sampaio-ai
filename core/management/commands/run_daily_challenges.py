"""
Management command to generate daily challenges.
Replaces Celery Beat scheduler — run via Render Cron Job or endpoint.

Usage:
    python manage.py run_daily_challenges
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate daily programming challenges for all difficulty levels'

    def handle(self, *args, **options):
        from studies.tasks import generate_daily_challenges_task

        self.stdout.write('Generating daily challenges...')
        try:
            result = generate_daily_challenges_task()
            self.stdout.write(
                self.style.SUCCESS('Daily challenges generated successfully.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating challenges: {e}')
            )
