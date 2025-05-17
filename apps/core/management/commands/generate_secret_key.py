from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key
import os
import re


class Command(BaseCommand):
    help = 'Generates a new Django SECRET_KEY and updates .env file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-env',
            action='store_true',
            help='Update the .env file with the new SECRET_KEY'
        )
        parser.add_argument(
            '--env-file',
            type=str,
            default='config/.env',
            help='Path to the .env file'
        )

    def handle(self, *args, **kwargs):
        new_key = get_random_secret_key()
        self.stdout.write(self.style.SUCCESS(f'Generated new SECRET_KEY: {new_key}'))
        
        if kwargs['update_env']:
            env_file = kwargs['env_file']
            
            if not os.path.exists(env_file):
                self.stdout.write(self.style.ERROR(f'No .env file found at {env_file}'))
                return
            
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            # Replace the current SECRET_KEY value
            if 'SECRET_KEY' in env_content:
                # Handle both quoted and unquoted values
                env_content = re.sub(
                    r"SECRET_KEY=[\'\"]?([^\'\"]+)[\'\"]?",
                    f"SECRET_KEY='{new_key}'",
                    env_content
                )
                
                with open(env_file, 'w') as f:
                    f.write(env_content)
                
                self.stdout.write(self.style.SUCCESS(f'Updated SECRET_KEY in {env_file}'))
            else:
                with open(env_file, 'a') as f:
                    f.write(f"\nSECRET_KEY='{new_key}'")
                
                self.stdout.write(self.style.SUCCESS(f'Added SECRET_KEY to {env_file}')) 