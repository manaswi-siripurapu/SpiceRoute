from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, VendorProfile, SupplierProfile, Category, Product, Order, OrderItem, Loan, LoanRepayment, Review, LeftoverListing, UpstreamSupplier

# Custom User Admin to display custom fields
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'is_vendor', 'is_supplier')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'is_vendor', 'is_supplier')}),
    )
    list_display = ('username', 'email', 'phone_number', 'is_vendor', 'is_supplier', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    list_filter = ('is_vendor', 'is_supplier', 'is_staff', 'is_active')

admin.site.register(User, CustomUserAdmin)

# Register other models
@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'location_pincode', 'type_of_food', 'average_rating_as_seller')
    search_fields = ('name', 'user__username', 'location_pincode')
    list_filter = ('type_of_food',)

@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'contact_person', 'phone_number', 'location_pincode', 'is_verified', 'average_rating')
    search_fields = ('business_name', 'user__username', 'phone_number')
    list_filter = ('is_verified',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'category', 'current_price_per_unit', 'quantity_available', 'quality_grade', 'is_organic')
    list_filter = ('supplier', 'category', 'is_organic', 'quality_grade')
    search_fields = ('name', 'supplier__business_name')
    raw_id_fields = ('supplier', 'category') # For better UX with many suppliers/categories

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'supplier', 'order_date', 'status', 'total_amount', 'delivery_option', 'is_co_vendor_order')
    list_filter = ('status', 'delivery_option', 'is_co_vendor_order', 'order_date')
    search_fields = ('vendor__name', 'supplier__business_name', 'id')
    raw_id_fields = ('vendor', 'supplier')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_per_unit_at_purchase', 'subtotal')
    list_filter = ('order__status', 'product__category')
    search_fields = ('order__id', 'product__name')
    raw_id_fields = ('order', 'product')

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'amount_granted', 'repayment_period_days', 'due_date', 'status', 'admin_approved_by')
    list_filter = ('status', 'repayment_period_days', 'disbursement_date')
    search_fields = ('vendor__name', 'id')
    raw_id_fields = ('vendor', 'admin_approved_by')

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount_paid', 'payment_date')
    list_filter = ('payment_date',)
    search_fields = ('loan__id',)
    raw_id_fields = ('loan',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('rating', 'comment', 'reviewer_vendor', 'reviewed_supplier', 'reviewed_upstream_supplier', 'review_date', 'is_moderated')
    list_filter = ('rating', 'is_moderated', 'review_date')
    search_fields = ('comment', 'reviewer_vendor__name', 'reviewed_supplier__business_name', 'reviewed_upstream_supplier__name')
    raw_id_fields = ('reviewer_vendor', 'reviewer_supplier', 'reviewed_supplier', 'reviewed_upstream_supplier')

@admin.register(LeftoverListing)
class LeftoverListingAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'seller_vendor', 'quantity', 'price_per_unit', 'condition', 'is_active', 'listing_date', 'buyer_vendor')
    list_filter = ('condition', 'is_active', 'listing_date')
    search_fields = ('item_name', 'seller_vendor__name', 'buyer_vendor__name')
    raw_id_fields = ('seller_vendor', 'buyer_vendor')

@admin.register(UpstreamSupplier)
class UpstreamSupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'average_rating_by_msh')
    search_fields = ('name', 'phone_number')
    filter_horizontal = ('msh_suppliers',) # For ManyToMany field
