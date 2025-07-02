from django.contrib import admin
from .models import (
    Author, Book, BookAuthor, Genre, BookGenre,
    User, Loan, Fine, Notification, Review
)

# Define custom admin classes to enhance the interface

class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1  # Number of extra forms to display

class BookGenreInline(admin.TabularInline):
    model = BookGenre
    extra = 1

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'isbn', 'total_copies', 'available_copies')
    search_fields = ('title', 'isbn')
    inlines = [BookAuthorInline, BookGenreInline]

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name')
    search_fields = ('first_name', 'last_name')

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('genre',)
    search_fields = ('genre',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff',)

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'borrow_date', 'due_date', 'status')
    search_fields = ('book__title', 'user__email')
    list_filter = ('status', 'due_date')

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('loan', 'fine_amount', 'payment_status', 'fine_date')
    search_fields = ('loan__book__title', 'loan__user__email')
    list_filter = ('payment_status',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'review_date')
    search_fields = ('book__title', 'user__email')
    list_filter = ('rating',)

@admin.register(BookAuthor)
class BookAuthorAdmin(admin.ModelAdmin):
    list_display = ('book', 'author')

@admin.register(BookGenre)
class BookGenreAdmin(admin.ModelAdmin):
    list_display = ('book', 'genre')


# Register other models if they need to be managed
admin.site.register(Notification)