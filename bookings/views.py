import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import login
from django.db.models import Q
from .models import (
    JewelryItem,
    JewelryCategory,
    JewelryPurchase,
    BuyCode,
    Payment,
    UserProfile,
)
from .forms import (
    UserRegistrationForm,
    JewelryPurchaseForm,
    UserProfileForm,
    JewelrySearchForm,
)
from .forms import UserUpdateForm, ProfileUpdateForm
import qrcode
import io
import base64
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)


def index(request):
    search_form = JewelrySearchForm(request.GET or None)
    jewelry_items = JewelryItem.objects.all()  # Show all items, even sold ones
    categories = JewelryCategory.objects.all()
    user_purchases = None

    if request.user.is_authenticated:
        user_purchases = JewelryPurchase.objects.filter(buyer=request.user).order_by(
            "-created_at"
        )

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get("search")
        category_filter = search_form.cleaned_data.get("category")
        item_type_filter = search_form.cleaned_data.get("item_type")
        price_min = search_form.cleaned_data.get("price_min")
        price_max = search_form.cleaned_data.get("price_max")

        if search_query:
            jewelry_items = jewelry_items.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )

        if category_filter:
            jewelry_items = jewelry_items.filter(category=category_filter)

        if item_type_filter:
            jewelry_items = jewelry_items.filter(item_type=item_type_filter)

        if price_min:
            jewelry_items = jewelry_items.filter(price__gte=price_min)

        if price_max:
            jewelry_items = jewelry_items.filter(price__lte=price_max)

    return render(
        request,
        "bookings/index.html",
        {
            "jewelry_items": jewelry_items,
            "categories": categories,
            "search_form": search_form,
            "user_purchases": user_purchases,
        },
    )


def custom_login(request):
    # Optionally, you can use this if you want to customize login context or error handling
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("index")
    else:
        form = AuthenticationForm()
    return render(request, "bookings/login.html", {"form": form})


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to JewelryHub.")
            return redirect("profile")
    else:
        form = UserRegistrationForm()
    return render(request, "bookings/register.html", {"form": form})


@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_purchases = JewelryPurchase.objects.filter(buyer=request.user).order_by(
        "-created_at"
    )
    # Generate QR codes for purchases (same as before)
    for purchase in user_purchases:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(purchase.buy_code.code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        data_uri = base64.b64encode(buffer.getvalue()).decode("ascii")
        purchase.qr_code_url = f"data:image/png;base64,{data_uri}"
    return render(
        request,
        "bookings/profile.html",
        {"user_purchases": user_purchases},
    )


@login_required
def profile_update(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=user_profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect("profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=user_profile)
    return render(
        request,
        "bookings/profile_update.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


@login_required
def purchase_form(request, jewelry_id):
    jewelry_item = get_object_or_404(
        JewelryItem, id=jewelry_id
    )  # Remove is_available=True

    if request.method == "POST":
        form = JewelryPurchaseForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data["quantity"]
            shipping_address = form.cleaned_data["shipping_address"]
            special_instructions = form.cleaned_data.get("special_instructions", "")

            with transaction.atomic():
                # Create or get buy code
                unique_code = str(uuid.uuid4())[:20]
                buy_code = BuyCode.objects.create(user=request.user, code=unique_code)

                # Create the purchase
                purchase = JewelryPurchase.objects.create(
                    buy_code=buy_code,
                    jewelry_item=jewelry_item,
                    buyer=request.user,
                    quantity=quantity,
                    unit_price=jewelry_item.price,
                    shipping_address=shipping_address,
                    special_instructions=special_instructions,
                    status="pending",
                )

                # Create payment record
                Payment.objects.create(
                    purchase=purchase,
                    amount=purchase.total_cost,
                    payment_type="purchase",
                    status="pending",
                )

                messages.success(request, "Purchase order created successfully!")
                return redirect("purchase_confirmation", purchase_id=purchase.id)
    else:
        form = JewelryPurchaseForm()

    return render(
        request,
        "bookings/purchase_form.html",
        {"form": form, "jewelry_item": jewelry_item},
    )


@login_required
def purchase_confirmation(request, purchase_id):
    purchase = get_object_or_404(JewelryPurchase, id=purchase_id)
    if purchase.buyer != request.user:
        messages.error(request, "You don't have permission to view this purchase.")
        return redirect("profile")
    return render(
        request,
        "bookings/confirmation.html",
        {
            "purchase": purchase,
            "jewelry_item": purchase.jewelry_item,  # Add this line
        },
    )


@login_required
def cancel_purchase(request, purchase_id):
    purchase = get_object_or_404(JewelryPurchase, id=purchase_id)
    # Check if the purchase belongs to the current user
    if purchase.buyer != request.user:
        messages.error(request, "You don't have permission to cancel this purchase.")
        return redirect("profile")

    # Only allow cancellation if status is pending or confirmed
    if purchase.status not in ["pending", "confirmed"]:
        messages.error(request, "This purchase cannot be cancelled at this stage.")
        return redirect("profile")

    if request.method == "POST":
        with transaction.atomic():
            # Mark jewelry item as available again
            jewelry_item = purchase.jewelry_item
            jewelry_item.is_available = True
            jewelry_item.save()

            # Update purchase status
            purchase.status = "cancelled"
            purchase.save()

            # Update payment status
            payments = purchase.payments.filter(status="pending")
            for payment in payments:
                payment.status = "refunded"
                payment.save()

            messages.success(request, "Purchase has been cancelled successfully.")
            return redirect("profile")

    return render(request, "bookings/cancel_purchase.html", {"purchase": purchase})


def get_jewelry_price(request):
    """AJAX view to get the price based on jewelry item"""
    jewelry_id = request.GET.get("jewelry_id")
    try:
        jewelry_item = JewelryItem.objects.get(id=jewelry_id)
        return JsonResponse(
            {
                "price": float(jewelry_item.price),
                "name": jewelry_item.name,
                "item_type": jewelry_item.get_item_type_display(),
            }
        )
    except JewelryItem.DoesNotExist:
        return JsonResponse({"error": "Jewelry item not found"}, status=404)


@login_required
def jewelry_detail(request, jewelry_id):
    """View to display detailed information about a jewelry item"""
    jewelry_item = get_object_or_404(JewelryItem, id=jewelry_id)

    return render(
        request, "bookings/jewelry_detail.html", {"jewelry_item": jewelry_item}
    )


@login_required
def profile_view(request):
    # Display user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(
        request,
        "bookings/profile_view.html",
        {
            "profile_form": ProfileUpdateForm(instance=user_profile),
            "user": request.user,
        },
    )


@login_required
def my_jewelry(request):
    """View for users to manage their own jewelry items"""
    user_jewelry = JewelryItem.objects.filter(owner=request.user).order_by(
        "-created_at"
    )

    return render(request, "bookings/my_jewelry.html", {"user_jewelry": user_jewelry})


@login_required
def add_jewelry(request):
    """View for users to add their jewelry for sale"""
    if request.method == "POST":
        # You'll need to create a JewelryItemForm
        # form = JewelryItemForm(request.POST, request.FILES)
        # if form.is_valid():
        #     jewelry_item = form.save(commit=False)
        #     jewelry_item.owner = request.user
        #     jewelry_item.save()
        #     messages.success(request, 'Jewelry item added successfully!')
        #     return redirect('my_jewelry')
        pass
    else:
        # form = JewelryItemForm()
        pass

    return render(
        request,
        "bookings/add_jewelry.html",
        {
            # 'form': form
        },
    )


def save_user_with_profile(self, commit=True):
    """Helper function to save user with profile"""
    user = super().save(commit=False)
    user.email = self.cleaned_data["email"]
    if commit:
        user.save()
        # Create UserProfile for the user
        UserProfile.objects.get_or_create(
            user=user, defaults={"bio": "Welcome to JewelryHub!"}
        )
    return user


def booking_form(request):
    return render(request, "bookings/booking_form.html")


# Add this to your views.py to debug the password reset process
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger(__name__)


def debug_user_password(request):
    """Debug view to check user password after reset"""
    if not request.user.is_superuser:
        return JsonResponse({"error": "Access denied"})

    username = request.GET.get("username")
    if not username:
        return JsonResponse({"error": "Username required"})

    try:
        user = User.objects.get(username=username)
        return JsonResponse(
            {
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "last_login": user.last_login,
                "date_joined": user.date_joined,
                "password_starts_with": (
                    user.password[:10] + "..." if user.password else "No password"
                ),
            }
        )
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"})


def test_password_auth(request):
    """Test authentication with username and password"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            return JsonResponse({"error": "Username and password required"})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            return JsonResponse(
                {
                    "success": True,
                    "message": "Authentication successful",
                    "user_id": user.id,
                    "is_active": user.is_active,
                }
            )
        else:
            # Check if user exists
            try:
                existing_user = User.objects.get(username=username)
                return JsonResponse(
                    {
                        "success": False,
                        "message": "User exists but password is incorrect",
                        "user_exists": True,
                        "is_active": existing_user.is_active,
                    }
                )
            except User.DoesNotExist:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "User does not exist",
                        "user_exists": False,
                    }
                )

    return JsonResponse({"error": "POST method required"})


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


def login_view(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("profile")  # or your desired page
        else:
            error = "Invalid username or password."
    return render(request, "bookings/login.html", {"error": error})


def reset_user_password(user, new_password):
    """Helper function to reset a user's password"""
    user.set_password(new_password)
    user.save()
