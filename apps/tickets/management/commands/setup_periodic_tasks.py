from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from django.utils import timezone

class Command(BaseCommand):
    help = 'Setup periodic tasks for ticket management'

    def handle(self, *args, **kwargs):
        # Create schedules
        daily_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )
        
        # Weekly schedule (Every Monday at 9:00 AM)
        weekly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='9',
            day_of_week='1',  # Monday
            defaults={
                'day_of_month':'*',
                'month_of_year':'*',
            }
        )

        # Setup tasks
        PeriodicTask.objects.get_or_create(
            name='Check Overdue Tickets',
            task='apps.tickets.tasks.check_overdue_tickets',
            interval=daily_schedule,
            defaults={
                'enabled': True,
                'start_time': timezone.now()
            }
        )

        PeriodicTask.objects.get_or_create(
            name='Send Ticket Reminders',
            task='apps.tickets.tasks.send_ticket_reminders',
            interval=daily_schedule,
            defaults={
                'enabled': True,
                'start_time': timezone.now()
            }
        )

        PeriodicTask.objects.get_or_create(
            name='Send Weekly Ticket Summary',
            task='apps.tickets.tasks.send_weekly_ticket_summary',
            crontab=weekly_schedule,
            defaults={
                'enabled': True,
            }
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully set up periodic tasks')
        )
