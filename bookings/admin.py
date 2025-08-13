from django.contrib import admin
from .models import (
    UserProfile,
    JewelryCategory,
    JewelryItem,
    BuyCode,
    JewelryPurchase,
    PurchaseReview,
    Payment,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "created_profile")
    search_fields = ("user__username", "user__email", "phone")
    list_filter = ("user__date_joined",)
    
    def created_profile(self, obj):
        return obj.user.date_joined.strftime("%Y-%m-%d")
    created_profile.short_description = "Profile Created"


@admin.register(JewelryCategory)
class JewelryCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    prepopulated_fields = {"name": ("name",)}


@admin.register(JewelryItem)
class JewelryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "item_type", "owner", "price", "weight", "is_available", "created_at")
    list_filter = ("item_type", "category", "is_available", "created_at")
    search_fields = ("name", "owner__username", "description")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "category", "item_type", "owner")
        }),
        ("Details", {
            "fields": ("description", "weight", "price", "image")
        }),
        ("Availability", {
            "fields": ("is_available",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(BuyCode)
class BuyCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "is_active", "created_at")
    search_fields = ("code", "user__username")
    list_filter = ("is_active", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(JewelryPurchase)
class JewelryPurchaseAdmin(admin.ModelAdmin):
    list_display = ("purchase_id", "jewelry_item", "buyer", "quantity", "total_cost", "status", "created_at")
    list_filter = ("status", "created_at", "jewelry_item__item_type")
    search_fields = ("buy_code__code", "buyer__username", "jewelry_item__name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "total_cost")
    
    def purchase_id(self, obj):
        return f"#{obj.id}"
    purchase_id.short_description = "Purchase ID"
    
    fieldsets = (
        ("Purchase Information", {
            "fields": ("buy_code", "jewelry_item", "buyer")
        }),
        ("Order Details", {
            "fields": ("quantity", "unit_price", "total_cost", "status")
        }),
        ("Shipping", {
            "fields": ("shipping_address", "special_instructions")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["mark_as_confirmed", "mark_as_shipped", "mark_as_delivered"]
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status="confirmed")
        self.message_user(request, f"{queryset.count()} purchases marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected purchases as confirmed"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status="shipped")
        self.message_user(request, f"{queryset.count()} purchases marked as shipped.")
    mark_as_shipped.short_description = "Mark selected purchases as shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status="delivered")
        self.message_user(request, f"{queryset.count()} purchases marked as delivered.")
    mark_as_delivered.short_description = "Mark selected purchases as delivered"


@admin.register(PurchaseReview)
class PurchaseReviewAdmin(admin.ModelAdmin):
    list_display = ("purchase", "reviewer", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("purchase__jewelry_item__name", "reviewer__username", "review_text")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "purchase", "amount", "payment_type", "status", "created_at")
    list_filter = ("payment_type", "status", "created_at")
    search_fields = ("transaction_id", "purchase__buy_code__code", "purchase__buyer__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ("Payment Information", {
            "fields": ("purchase", "amount", "payment_type")
        }),
        ("Transaction Details", {
            "fields": ("transaction_id", "status")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["mark_as_completed", "mark_as_failed", "mark_as_refunded"]
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status="completed")
        self.message_user(request, f"{queryset.count()} payments marked as completed.")
    mark_as_completed.short_description = "Mark selected payments as completed"
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status="failed")
        self.message_user(request, f"{queryset.count()} payments marked as failed.")
    mark_as_failed.short_description = "Mark selected payments as failed"
    
    def mark_as_refunded(self, request, queryset):
        queryset.update(status="refunded")
        self.message_user(request, f"{queryset.count()} payments marked as refunded.")
    mark_as_refunded.short_description = "Mark selected payments as refunded"


# Customize the admin site header and title
admin.site.site_header = "JewelryHub Administration"
admin.site.site_title = "JewelryHub Admin"
admin.site.index_title = "Welcome to JewelryHub Administration"