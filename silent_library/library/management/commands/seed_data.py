
import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth import get_user_model
from library.models import Author, Book, BookAuthor, Genre, BookGenre, Loan, Fine, Notification, Review

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')
        fake = Faker()

        # Clear existing data
        Review.objects.all().delete()
        Notification.objects.all().delete()
        Fine.objects.all().delete()
        Loan.objects.all().delete()
        BookGenre.objects.all().delete()
        BookAuthor.objects.all().delete()
        Genre.objects.all().delete()
        Book.objects.all().delete()
        Author.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        # Create users
        users = []
        for _ in range(10):
            user = User.objects.create_user(
                username=fake.user_name(),
                password='password123',
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                date_of_birth=fake.date_of_birth()
            )
            users.append(user)

        # Create authors
        authors = []
        for _ in range(20):
            author = Author.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            authors.append(author)

        # Create genres
        genres = []
        for genre_name in ['Fiction', 'Non-Fiction', 'Science Fiction', 'Fantasy', 'Mystery', 'Thriller', 'Romance', 'Horror', 'History', 'Biography']:
            genre = Genre.objects.create(genre=genre_name)
            genres.append(genre)

        # Create books
        books = []
        for _ in range(50):
            total_copies = random.randint(1, 10)
            book = Book.objects.create(
                title=fake.catch_phrase(),
                isbn=fake.isbn13(),
                total_copies=total_copies,
                available_copies=total_copies
            )
            books.append(book)

            # Add authors to the book
            for _ in range(random.randint(1, 2)):
                author = random.choice(authors)
                BookAuthor.objects.create(book=book, author=author)

            # Add genres to the book
            for _ in range(random.randint(1, 3)):
                genre = random.choice(genres)
                BookGenre.objects.create(book=book, genre=genre)

        # Create loans
        loans = []
        for _ in range(100):
            loan = Loan.objects.create(
                user=random.choice(users),
                book=random.choice(books),
                due_date=fake.future_date(),
                status=random.choice(['borrowed', 'returned', 'overdue'])
            )
            loans.append(loan)

        # Create fines
        for loan in loans:
            if loan.status == 'overdue':
                Fine.objects.create(
                    loan=loan,
                    fine_amount=random.uniform(1.0, 20.0),
                    payment_status=random.choice(['pending', 'paid', 'waived'])
                )

        # Create notifications
        for user in users:
            for _ in range(random.randint(0, 5)):
                Notification.objects.create(
                    user=user,
                    notification_text=fake.sentence()
                )

        # Create reviews
        for book in books:
            for _ in range(random.randint(0, 3)):
                Review.objects.create(
                    user=random.choice(users),
                    book=book,
                    rating=random.randint(1, 5),
                    review_text=fake.paragraph()
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded data.'))
