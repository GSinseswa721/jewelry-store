# bookings/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile,
    JewelryItem,
    JewelryCategory,
    JewelryPurchase,
)
import re
from django.core.exceptions import ValidationError


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Create UserProfile with phone number
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data["phone"],
                bio="Welcome to JewelryHub!",
            )
        return user

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email


class UserProfileForm(forms.ModelForm):
    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if not re.match(r"^(\+\d{1,4})?0?\d{9}$", phone):
            raise ValidationError(
                "Enter a valid phone number (10 digits, with optional country code)."
            )
        return phone

    class Meta:
        model = UserProfile
        fields = ("profile_image", "bio", "phone", "address")
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "placeholder": "Tell us about yourself...",
                }
            ),
            "profile_image": forms.FileInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "placeholder": "Your phone number",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "placeholder": "Your address",
                }
            ),
        }


class JewelryPurchaseForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input rounded-lg border-gray-300 w-full",
                "min": "1",
                "max": "10",
            }
        ),
        help_text="Number of items to purchase",
    )

    shipping_address = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "form-input rounded-lg border-gray-300 w-full",
                "placeholder": "Enter your shipping address...",
            }
        ),
        help_text="Where should we ship your jewelry?",
    )

    special_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-input rounded-lg border-gray-300 w-full",
                "placeholder": "Any special instructions or requests...",
            }
        ),
        help_text="Optional: Any special handling or delivery instructions",
    )


class JewelrySearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input rounded-lg border-gray-300 w-full",
                "placeholder": "Search jewelry...",
            }
        ),
    )

    category = forms.ModelChoiceField(
        queryset=JewelryCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(
            attrs={"class": "form-select rounded-lg border-gray-300 w-full"}
        ),
    )

    item_type = forms.ChoiceField(
        choices=[("", "All Types")] + JewelryItem.ITEM_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select rounded-lg border-gray-300 w-full"}
        ),
    )

    price_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input rounded-lg border-gray-300 w-full",
                "placeholder": "Min Price",
                "step": "0.01",
            }
        ),
    )

    price_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input rounded-lg border-gray-300 w-full",
                "placeholder": "Max Price",
                "step": "0.01",
            }
        ),
    )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
        }


class ProfileUpdateForm(forms.ModelForm):
    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if not re.match(r"^(\+\d{1,4})?0?\d{9}$", phone):
            raise ValidationError(
                "Enter a valid phone number (10 digits, with optional country code)."
            )
        return phone

    class Meta:
        model = UserProfile
        fields = ["profile_image", "bio", "phone", "address"]
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-input rounded-lg border-gray-300 w-full",
                }
            ),
            "profile_image": forms.FileInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
            "address": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-input rounded-lg border-gray-300 w-full",
                }
            ),
        }


class JewelryItemForm(forms.ModelForm):
    """Form for adding/editing jewelry items"""

    class Meta:
        model = JewelryItem
        fields = [
            "name",
            "category",
            "item_type",
            "description",
            "weight",
            "price",
            "image",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "placeholder": "Jewelry item name",
                }
            ),
            "category": forms.Select(
                attrs={"class": "form-select rounded-lg border-gray-300 w-full"}
            ),
            "item_type": forms.Select(
                attrs={"class": "form-select rounded-lg border-gray-300 w-full"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "placeholder": "Describe your jewelry item...",
                }
            ),
            "weight": forms.NumberInput(
                attrs={
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "step": "0.01",
                    "placeholder": "Weight in grams",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "step": "0.01",
                    "placeholder": "Price in USD",
                }
            ),
            "image": forms.FileInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
        }

    def save(self, commit=True):
        jewelry_item = super().save(commit=False)
        if commit:
            jewelry_item.save()
        return jewelry_item


class JewelryCategoryForm(forms.ModelForm):
    """Form for adding jewelry categories (admin use)"""

    class Meta:
        model = JewelryCategory
        fields = ["name", "description", "image"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "placeholder": "Category name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-input rounded-lg border-gray-300 w-full",
                    "placeholder": "Category description",
                }
            ),
            "image": forms.FileInput(
                attrs={"class": "form-input rounded-lg border-gray-300 w-full"}
            ),
        }
