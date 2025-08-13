# bookings/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from . import views
from .views import custom_login, profile_update

urlpatterns = [
    # Home and main pages
    path("", views.index, name="index"),
    # Authentication
    path("register/", views.register, name="register"),
    path(
        "login/",
        custom_login,
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="index"), name="logout"),
    # User profile
    path("profile/", views.profile, name="profile"),
    path("profile/update/", profile_update, name="profile_update"),
    path("profile/view/", views.profile_view, name="profile_view"),
    # Jewelry management (for sellers)
    path("my-jewelry/", views.my_jewelry, name="my_jewelry"),
    path("add-jewelry/", views.add_jewelry, name="add_jewelry"),
    # Jewelry viewing and purchasing
    path("jewelry/<int:jewelry_id>/", views.jewelry_detail, name="jewelry_detail"),
    path("purchase/<int:jewelry_id>/", views.purchase_form, name="purchase_form"),
    path(
        "purchase/confirmation/<int:purchase_id>/",
        views.purchase_confirmation,
        name="purchase_confirmation",
    ),
    path(
        "purchase/cancel/<int:purchase_id>/",
        views.cancel_purchase,
        name="cancel_purchase",
    ),
    # AJAX endpoints
    path("api/jewelry-price/", views.get_jewelry_price, name="get_jewelry_price"),
    # Password reset URLs (optional but recommended)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="bookings/password_reset.html"
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="bookings/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="bookings/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="bookings/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
