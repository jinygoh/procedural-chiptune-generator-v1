from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from .models import Book, Author, Genre, Loan, Review
from .forms import UserRegistrationForm, UserLoginForm, UserEditForm, BookForm, ReviewForm
from django.db.models import Q
from django.conf import settings


def is_admin(user):
    return user.is_staff

def home(request):
    return render(request, 'library/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Send confirmation email
            email_subject = 'Successful Registration on Silent Library'
            email_message = f"Dear {user.first_name},\n\n"                       f"Thank you for registering on our platform. We are excited to have you as a member.\n\n"                       f"Thank you.\nSilent Library Team"
            email_recipient = [user.email]
            
            try:
                send_mail(
                    subject=email_subject,
                    message=email_message,
                    from_email=f"Silent Library <{settings.DEFAULT_FROM_EMAIL}>",
                    recipient_list=email_recipient
                )
            except Exception as e:
                messages.error(request, f'Error sending email to {email_recipient}: {str(e)}')

            messages.success(request, 'Registration successful. Please check your email for confirmation.')
            # You might not want to log the user in automatically in this case,
            # as they should confirm their email first.  Uncomment the line below if
            # you still want automatic login.
            # login(request, user)

            return redirect('registration_complete')
    else:
        form = UserRegistrationForm()
    return render(request, 'library/register.html', {'form': form})

def registration_complete(request):
    return render(request, 'library/registration_complete.html')

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('dashboard')
    else:
        form = UserLoginForm()
    return render(request, 'library/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    loans = Loan.objects.filter(user=request.user)
    return render(request, 'library/dashboard.html', {'loans': loans})

from .forms import UserRegistrationForm, UserLoginForm, UserEditForm, UserEditUsernameEmailForm, UserEditPasswordForm, BookForm, ReviewForm

@login_required
def profile(request):
    if 'edit_profile' in request.POST:
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserEditForm(instance=request.user)

    if 'edit_username_email' in request.POST:
        username_email_form = UserEditUsernameEmailForm(request.POST, instance=request.user, user=request.user)
        if username_email_form.is_valid():
            username_email_form.save()
            messages.success(request, 'Username and email updated successfully.')
            return redirect('profile')
    else:
        username_email_form = UserEditUsernameEmailForm(instance=request.user, user=request.user)

    if 'change_password' in request.POST:
        password_form = UserEditPasswordForm(request.POST, user=request.user)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully.')
            return redirect('profile')
        # Removed the else block that was duplicating form errors into messages
    else:
        password_form = UserEditPasswordForm(user=request.user)

    return render(request, 'library/profile.html', {
        'form': form,
        'username_email_form': username_email_form,
        'password_form': password_form
    })

def search_books(request):
    query = request.GET.get('q')
    books = Book.objects.all()
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(authors__first_name__icontains=query) |
            Q(authors__last_name__icontains=query) |
            Q(genres__genre__icontains=query)
        ).distinct()
    return render(request, 'library/search.html', {'books': books, 'query': query})

def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    reviews = Review.objects.filter(book=book)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.book = book
            review.user = request.user
            review.save()
            return redirect('book_detail', book_id=book.pk)
    else:
        form = ReviewForm()
    return render(request, 'library/book_detail.html', {'book': book, 'reviews': reviews, 'form': form})

@user_passes_test(is_admin, login_url=reverse_lazy('admin_login'))
def admin_dashboard(request):
    return render(request, 'library/admin_dashboard.html')

@user_passes_test(is_admin, login_url=reverse_lazy('admin_login'))
def admin_books(request):
    books = Book.objects.all()
    return render(request, 'library/admin_books.html', {'books': books})

@user_passes_test(is_admin, login_url=reverse_lazy('admin_login'))
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_books')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form})

@user_passes_test(is_admin, login_url=reverse_lazy('admin_login'))
def edit_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('admin_books')
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {'form': form})

@user_passes_test(is_admin, login_url=reverse_lazy('admin_login'))
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        book.delete()
        return redirect('admin_books')
    return render(request, 'library/book_confirm_delete.html', {'book': book})