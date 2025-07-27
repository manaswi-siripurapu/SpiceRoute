from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Extend Django's built-in User model to add custom fields for user types
class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_vendor = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='spiceroute_users',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='spiceroute_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

# Profile for Vendors
class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='vendor_profile')
    name = models.CharField(max_length=255)
    location_pincode = models.CharField(max_length=10)
    location_address = models.TextField(null=True, blank=True)
    type_of_food = models.CharField(max_length=100, null=True, blank=True)
    average_rating_as_seller = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews_as_seller = models.IntegerField(default=0)

    def __str__(self):
        return f"Vendor: {self.name}"

# Profile for Suppliers (Micro-Supply Hubs - MSH)
class SupplierProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='supplier_profile')
    business_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15) # MSH's contact number for bargaining
    email = models.EmailField(null=True, blank=True)
    location_pincode = models.CharField(max_length=10)
    location_address = models.TextField()
    business_registration_details = models.TextField(null=True, blank=True)
    storage_capacity_sqft = models.IntegerField(null=True, blank=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False) # Admin verification status

    def __str__(self):
        return f"MSH: {self.business_name}"

# Category for raw materials
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories" # Fix plural name in admin

    def __str__(self):
        return self.name

# Product (raw material) offered by MSHs
class Product(models.Model):
    UNIT_OF_MEASURE_CHOICES = [
        ('kg', 'Kilogram'), ('gram', 'Gram'), ('piece', 'Piece'), ('bunch', 'Bunch'),
        ('liter', 'Liter'), ('ml', 'Milliliter'), ('dozen', 'Dozen'), ('unit', 'Unit') # Added 'unit' as a generic option
    ]
    QUALITY_GRADE_CHOICES = [
        ('grade_a', 'Grade A'),
        ('grade_b', 'Grade B'),
        ('standard', 'Standard Quality'),
        ('premium', 'Premium'),
        ('organic', 'Organic Certified'), # If different from is_organic
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='products_offered')
    unit_of_measure = models.CharField(max_length=50, choices=UNIT_OF_MEASURE_CHOICES)
    current_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    quality_grade = models.CharField(max_length=50, choices=QUALITY_GRADE_CHOICES, default='standard') # Added choices
    is_organic = models.BooleanField(default=False)
    ai_suggested_min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ai_suggested_max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} by {self.supplier.business_name}"

# Order placed by a Vendor
class Order(models.Model):
    DELIVERY_OPTIONS = [
        ('instant', 'Instant Delivery'),
        ('tomorrow_morning', 'Tomorrow Morning (9 AM-12 PM)'),
        ('tomorrow_evening', 'Tomorrow Evening (5 PM-8 PM)'),
        ('day_after_morning', 'Day After Morning'),
        ('day_after_evening', 'Day After Evening'),
    ]
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('packed', 'Packed'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='orders_placed')
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='orders_received')
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_option = models.CharField(max_length=50, choices=DELIVERY_OPTIONS)
    scheduled_delivery_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=ORDER_STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    payment_method = models.CharField(max_length=50, choices=[('cod', 'Cash on Delivery'), ('online', 'Online Payment')])
    is_co_vendor_order = models.BooleanField(default=False)
    co_vendor_group_id = models.CharField(max_length=100, null=True, blank=True) # Simple ID to link co-orders
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order #{self.id} by {self.vendor.name} from {self.supplier.business_name}"

# Individual items within an Order
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_unit_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} {self.product.unit_of_measure} of {self.product.name} in Order #{self.order.id}"

# Micro-loans for Vendors
class Loan(models.Model):
    REPAYMENT_PERIODS = [
        (2, '2 Days'),
        (5, '5 Days'),
        (7, '1 Week'),
        (14, '2 Weeks'),
        (30, '1 Month'),
    ]
    LOAN_STATUS = [
        ('pending', 'Pending Admin Approval'),
        ('active', 'Active'),
        ('repaid', 'Repaid'),
        ('overdue', 'Overdue'),
        ('defaulted', 'Defaulted'),
    ]

    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='loans')
    amount_granted = models.DecimalField(max_digits=10, decimal_places=2)
    repayment_period_days = models.IntegerField(choices=REPAYMENT_PERIODS)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2) # e.g., 0.05 for 5%
    amount_to_repay = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    disbursement_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=LOAN_STATUS, default='pending')
    last_repayment_date = models.DateTimeField(null=True, blank=True)
    admin_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')

    def save(self, *args, **kwargs):
        if not self.pk or (self.status == 'active' and (self.due_date is None or self.amount_to_repay is None)):
            if self.disbursement_date is None:
                self.disbursement_date = timezone.now()
            
            self.due_date = self.disbursement_date + timezone.timedelta(days=self.repayment_period_days)
            self.amount_to_repay = self.amount_granted * (1 + self.interest_rate)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Loan #{self.id} for {self.vendor.name} - {self.amount_granted} ({self.status})"

# Records individual repayments for a loan
class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50) # e.g., 'online', 'cash'

    def __str__(self):
        return f"Repayment of {self.amount_paid} for Loan #{self.loan.id}"

# Reviews and Ratings
class Review(models.Model):
    reviewer_vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews_given')
    reviewer_supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews_given_by_msh')
    
    # Reviewed entity can be an MSH or an UpstreamSupplier
    reviewed_supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews_received')
    reviewed_upstream_supplier = models.ForeignKey('UpstreamSupplier', on_delete=models.CASCADE, null=True, blank=True, related_name='reviews_received_from_msh')

    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)]) # 1 to 5 stars
    comment = models.TextField(null=True, blank=True)
    review_date = models.DateTimeField(auto_now_add=True)
    is_moderated = models.BooleanField(default=False)

    class Meta:
        pass

    def __str__(self):
        if self.reviewer_vendor and self.reviewed_supplier:
            return f"Vendor {self.reviewer_vendor.name} rated MSH {self.reviewed_supplier.business_name}: {self.rating} stars"
        elif self.reviewer_supplier and self.reviewed_upstream_supplier:
            return f"MSH {self.reviewer_supplier.business_name} rated Upstream {self.reviewed_upstream_supplier.name}: {self.rating} stars"
        return f"Review ID {self.id} - {self.rating} stars"

# Leftover Groceries Market listings
class LeftoverListing(models.Model):
    CONDITION_CHOICES = [
        ('fresh', 'Fresh'),
        ('good_for_1_day', 'Good for 1 Day'),
        ('slightly_imperfect', 'Slightly Imperfect but Usable'),
    ]

    seller_vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='listings_as_seller')
    item_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=50, choices=Product.UNIT_OF_MEASURE_CHOICES) # Re-using choices from Product
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    photo = models.ImageField(upload_to='leftover_images/', null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    listing_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    pickup_delivery_preference = models.CharField(max_length=50, choices=[('pickup', 'Pickup'), ('delivery', 'Delivery')])
    
    buyer_vendor = models.ForeignKey(VendorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='listings_as_buyer')
    transaction_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Leftover: {self.item_name} by {self.seller_vendor.name} ({self.quantity} {self.unit_of_measure})"

# Upstream Suppliers (for MSHs to source from)
class UpstreamSupplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    average_rating_by_msh = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews_by_msh = models.IntegerField(default=0)
    
    msh_suppliers = models.ManyToManyField(SupplierProfile, related_name='upstream_suppliers')

    def __str__(self):
        return self.name

