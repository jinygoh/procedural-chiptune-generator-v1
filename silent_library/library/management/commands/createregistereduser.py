from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import getpass

class Command(BaseCommand):
    help = 'Creates a new registered user via the console'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Create a new registered user"))

        while True:
            username = input("Username: ")
            if not username:
                self.stderr.write(self.style.ERROR("Username cannot be empty."))
                continue
            if User.objects.filter(username=username).exists():
                self.stderr.write(self.style.ERROR(f"Username '{username}' already exists. Please choose another."))
                continue
            break

        while True:
            email = input("Email address: ")
            if not email:
                self.stderr.write(self.style.ERROR("Email cannot be empty."))
                continue
            try:
                validate_email(email)
            except ValidationError:
                self.stderr.write(self.style.ERROR("Invalid email address. Please enter a valid email."))
                continue
            if User.objects.filter(email=email).exists():
                self.stderr.write(self.style.ERROR(f"Email '{email}' is already registered. Please use another email."))
                continue
            break

        while True:
            password = getpass.getpass("Password: ")
            if not password:
                self.stderr.write(self.style.ERROR("Password cannot be empty."))
                continue
            password_confirm = getpass.getpass("Password (again): ")
            if password != password_confirm:
                self.stderr.write(self.style.ERROR("Passwords do not match. Please try again."))
                continue
            # Add password strength validation if desired here
            break

        try:
            user = User.objects.create_user(username, email, password)
            # Optionally, send a confirmation email here if email services are configured
            # send_mail(
            #     'Welcome to Silent Library!',
            #     f'Hi {username},\n\nYour account has been successfully created.',
            #     'noreply@silentlibrary.com',
            #     [email],
            #     fail_silently=False,
            # )
            self.stdout.write(self.style.SUCCESS(f"Successfully created user '{username}' with email '{email}'."))
        except Exception as e:
            raise CommandError(f"Failed to create user: {e}")
