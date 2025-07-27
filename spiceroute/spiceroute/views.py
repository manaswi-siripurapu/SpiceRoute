from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import User, VendorProfile, SupplierProfile, Category, Product, Order, OrderItem, Loan, LoanRepayment, Review, LeftoverListing, UpstreamSupplier
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Avg, Count
import json
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal # <--- NEW IMPORT: Import Decimal for precise calculations

# Home page view
def home_view(request):
    return render(request, 'home.html')

# Registration view
def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_type = request.POST.get('user_type')
        location_pincode = request.POST.get('location_pincode')
        
        # Vendor specific fields
        type_of_food = request.POST.get('type_of_food')
        
        # Supplier specific fields
        business_registration_details = request.POST.get('business_registration_details')
        
        # Basic validation
        if not (name and phone_number and password and confirm_password and user_type and location_pincode):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html')

        try:
            # Create the custom User object
            user = User.objects.create_user(username=phone_number, password=password, phone_number=phone_number, email=email)
            
            if user_type == 'vendor':
                user.is_vendor = True
                user.save()
                VendorProfile.objects.create(
                    user=user,
                    name=name,
                    location_pincode=location_pincode,
                    type_of_food=type_of_food
                )
                messages.success(request, "Vendor account created successfully! Please login.")
            elif user_type == 'supplier':
                user.is_supplier = True
                user.save()
                SupplierProfile.objects.create(
                    user=user,
                    business_name=name,
                    contact_person=name,
                    phone_number=phone_number,
                    email=email,
                    location_pincode=location_pincode,
                    location_address="Not provided during registration",
                    business_registration_details=business_registration_details
                )
                messages.success(request, "Supplier (MSH) account created successfully! Please login.")
            else:
                messages.error(request, "Invalid user type selected.")
                return render(request, 'register.html')

            return redirect('login')

        except IntegrityError:
            messages.error(request, "A user with this phone number or email already exists.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            
    return render(request, 'register.html')

# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            if user.is_vendor:
                return redirect('vendor_dashboard')
            elif user.is_supplier:
                return redirect('supplier_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

# --- AI Suggestion Logic (Simulated) ---
def get_vendor_ai_suggestions(vendor_profile):
    suggestions = []
    
    recent_orders = Order.objects.filter(
        vendor=vendor_profile,
        order_date__gte=timezone.now() - timedelta(days=30)
    )
    
    product_counts = {}
    for order in recent_orders:
        for item in order.items.all():
            product_id = item.product.id
            product_counts[product_id] = product_counts.get(product_id, 0) + item.quantity

    sorted_products = sorted(product_counts.items(), key=lambda item: item[1], reverse=True)
    
    suggested_product_ids = [prod_id for prod_id, _ in sorted_products[:3]]
    
    for prod_id in suggested_product_ids:
        product = Product.objects.filter(id=prod_id, supplier__location_pincode=vendor_profile.location_pincode, quantity_available__gt=0).first()
        if product:
            suggested_quantity = 5 if product.unit_of_measure == 'kg' else 10 if product.unit_of_measure == 'piece' else 2
            # Ensure suggested_price is Decimal for consistency
            suggested_price = product.current_price_per_unit * (Decimal(1) - Decimal(str(random.uniform(0.01, 0.05))))
            
            suggestions.append({
                'type': 'Past Purchase',
                'product_name': product.name,
                'product_id': product.id,
                'suggested_quantity': round(suggested_quantity, 2),
                'suggested_unit': product.unit_of_measure,
                'suggested_price': round(float(suggested_price), 2), # Convert back to float for template display
                'reason': f"Based on your recent purchases. Great deal from {product.supplier.business_name}!"
            })

    seasonal_products = Product.objects.filter(
        supplier__location_pincode=vendor_profile.location_pincode,
        quantity_available__gt=0
    ).exclude(id__in=suggested_product_ids).order_by('?')[:1]

    if seasonal_products:
        product = seasonal_products[0]
        suggested_quantity = 5 if product.unit_of_measure == 'kg' else 10 if product.unit_of_measure == 'piece' else 2
        # Ensure suggested_price is Decimal for consistency
        suggested_price = product.current_price_per_unit * (Decimal(1) - Decimal(str(random.uniform(0.01, 0.03))))
        suggestions.append({
            'type': 'Seasonal Pick',
            'product_name': product.name,
            'product_id': product.id,
            'suggested_quantity': round(suggested_quantity, 2),
            'suggested_unit': product.unit_of_measure,
            'suggested_price': round(float(suggested_price), 2), # Convert back to float for template display
            'reason': f"Popular this season! Check out {product.supplier.business_name}."
        })
    
    if not suggestions:
        popular_products = Product.objects.filter(
            supplier__location_pincode=vendor_profile.location_pincode,
            quantity_available__gt=0
        ).order_by('?')[:2]
        for product in popular_products:
            suggested_quantity = 5 if product.unit_of_measure == 'kg' else 10 if product.unit_of_measure == 'piece' else 2
            # Ensure suggested_price is Decimal for consistency
            suggested_price = product.current_price_per_unit * (Decimal(1) - Decimal(str(random.uniform(0.01, 0.02))))
            suggestions.append({
                'type': 'Popular Item',
                'product_name': product.name,
                'product_id': product.id,
                'suggested_quantity': round(suggested_quantity, 2),
                'suggested_unit': product.unit_of_measure,
                'suggested_price': round(float(suggested_price), 2), # Convert back to float for template display
                'reason': f"A popular choice from {product.supplier.business_name}."
            })

    return suggestions

def get_supplier_ai_insights(supplier_profile):
    insights = []

    supplier_products = Product.objects.filter(supplier=supplier_profile)

    for product in supplier_products:
        competitor_products = Product.objects.filter(
            name=product.name,
            category=product.category,
            supplier__location_pincode=supplier_profile.location_pincode
        ).exclude(supplier=supplier_profile)

        if competitor_products.exists():
            avg_competitor_price = competitor_products.aggregate(avg_price=Avg('current_price_per_unit'))['avg_price']
            if avg_competitor_price:
                # Fix: Convert float to Decimal before multiplication
                min_price = avg_competitor_price * (Decimal(1) - Decimal(str(random.uniform(0.02, 0.05))))
                max_price = avg_competitor_price * (Decimal(1) + Decimal(str(random.uniform(0.01, 0.03))))
                insights.append({
                    'type': 'Pricing Suggestion',
                    'product_name': product.name,
                    'product_id': product.id,
                    'current_price': float(product.current_price_per_unit), # Convert to float for template display
                    'suggested_min_price': round(float(min_price), 2), # Convert to float for template display
                    'suggested_max_price': round(float(max_price), 2), # Convert to float for template display
                    'reason': f"Based on competitor pricing in your area. Current price: ₹{product.current_price_per_unit}."
                })
        else:
            # Fix: Convert float to Decimal before multiplication
            min_price = product.current_price_per_unit * (Decimal(1) - Decimal(str(random.uniform(0.01, 0.03))))
            max_price = product.current_price_per_unit * (Decimal(1) + Decimal(str(random.uniform(0.01, 0.03))))
            insights.append({
                'type': 'Pricing Suggestion',
                'product_name': product.name,
                'product_id': product.id,
                'current_price': float(product.current_price_per_unit), # Convert to float for template display
                'suggested_min_price': round(float(min_price), 2), # Convert to float for template display
                'suggested_max_price': round(float(max_price), 2), # Convert to float for template display
                'reason': f"No direct competitors found for {product.name}. Consider this range."
            })

        recent_order_volume = OrderItem.objects.filter(
            product=product,
            order__order_date__gte=timezone.now() - timedelta(days=7),
            order__supplier=supplier_profile
        ).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

        demand_level = "Low"
        if recent_order_volume > 50:
            demand_level = "High"
        elif recent_order_volume > 10:
            demand_level = "Medium"
        
        insights.append({
            'type': 'Demand Forecast',
            'product_name': product.name,
            'product_id': product.id,
            'recent_volume': round(float(recent_order_volume), 2), # Convert to float for template display
            'forecast_level': demand_level,
            'reason': f"Demand for {product.name} is currently {demand_level} (Last 7 days volume: {round(float(recent_order_volume), 2)} {product.unit_of_measure})."
        })
    
    if not insights and not supplier_products.exists():
        insights.append({
            'type': 'Getting Started',
            'product_name': 'Your Inventory',
            'reason': 'List your first few products to start receiving AI pricing and demand insights!'
        })

    return insights


# Vendor Dashboard
@login_required
def vendor_dashboard_view(request):
    if not request.user.is_vendor:
        messages.warning(request, "You are not authorized to view the vendor dashboard.")
        return redirect('home')
    
    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    
    ai_suggestions = get_vendor_ai_suggestions(vendor_profile)

    context = {
        'vendor_name': vendor_profile.name,
        'ai_suggestions': ai_suggestions,
    }
    return render(request, 'vendor_dashboard.html', context)

# Supplier Dashboard
@login_required
def supplier_dashboard_view(request):
    if not request.user.is_supplier:
        messages.warning(request, "You are not authorized to view the supplier dashboard.")
        return redirect('home')
    
    supplier_profile = get_object_or_404(SupplierProfile, user=request.user)

    ai_insights = get_supplier_ai_insights(supplier_profile)

    context = {
        'supplier_name': supplier_profile.business_name,
        'ai_insights': ai_insights,
    }
    return render(request, 'supplier_dashboard.html', context)

# Placeholder for other common pages
def about_view(request):
    return render(request, 'about.html')

def faq_view(request):
    return render(request, 'faq.html')

def forgot_password_view(request):
    messages.info(request, "Forgot password functionality is not yet implemented.")
    return render(request, 'login.html')

# --- Vendor Specific Pages ---
@login_required
def browse_products_view(request):
    if not request.user.is_vendor:
        messages.warning(request, "Access denied. Please log in as a Vendor.")
        return redirect('home')

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    vendor_pincode = vendor_profile.location_pincode

    products = Product.objects.filter(
        supplier__location_pincode=vendor_pincode, 
        quantity_available__gt=0
    ).order_by('name')

    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category__id=category_id)

    categories = Category.objects.all().order_by('name')

    context = {
        'products': products,
        'categories': categories,
        'current_category_id': category_id,
        'search_query': search_query,
        'vendor_pincode': vendor_pincode,
    }
    return render(request, 'browse_products.html', context)

@login_required
def checkout_view(request):
    if not request.user.is_vendor:
        messages.warning(request, "Access denied. Please log in as a Vendor.")
        return redirect('home')

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    
    if request.method == 'POST':
        cart_data_json = request.POST.get('cart_data')
        delivery_option = request.POST.get('delivery_option')
        co_vendor_id = request.POST.get('co_vendor_id')
        payment_method = request.POST.get('payment_method')
        delivery_address = request.POST.get('delivery_address')

        if not cart_data_json:
            messages.error(request, "Your cart is empty or invalid.")
            return redirect('browse_products')

        try:
            cart_items = json.loads(cart_data_json)
        except json.JSONDecodeError:
            messages.error(request, "Invalid cart data received.")
            return redirect('browse_products')

        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('browse_products')

        total_amount = 0
        order_products_info = {}
        
        for item in cart_items:
            product_id = item.get('id')
            quantity = item.get('quantity')
            
            if not (product_id and quantity and quantity > 0):
                messages.error(request, "Invalid item in cart.")
                return redirect('browse_products')

            product = get_object_or_404(Product, id=product_id)

            if product.quantity_available < quantity:
                messages.error(request, f"Not enough {product.name} available. Only {product.quantity_available} {product.unit_of_measure} left.")
                return redirect('browse_products')
            
            item_subtotal = product.current_price_per_unit * quantity
            total_amount += item_subtotal

            if product.supplier.pk not in order_products_info:
                order_products_info[product.supplier.pk] = {
                    'supplier_profile': product.supplier,
                    'items': [],
                    'subtotal': 0
                }
            order_products_info[product.supplier.pk]['items'].append({
                'product': product,
                'quantity': quantity,
                'price_per_unit_at_purchase': product.current_price_per_unit,
                'subtotal': item_subtotal
            })
            order_products_info[product.supplier.pk]['subtotal'] += item_subtotal

        discount_applied = 0
        is_co_vendor_order = False
        if co_vendor_id:
            try:
                co_vendor_user = User.objects.get(Q(username=co_vendor_id) | Q(phone_number=co_vendor_id) | Q(email=co_vendor_id))
                if co_vendor_user.is_vendor and co_vendor_user != request.user:
                    discount_percentage = 0.05
                    discount_applied = total_amount * discount_percentage
                    total_amount -= discount_applied
                    is_co_vendor_order = True
                    messages.info(request, f"Co-vendor discount of ₹{discount_applied:.2f} applied!")
                else:
                    messages.warning(request, "Invalid or self co-vendor ID. Discount not applied.")
            except User.DoesNotExist:
                messages.warning(request, "Co-vendor not found. Discount not applied.")
            except Exception as e:
                messages.warning(request, f"Error applying co-vendor discount: {e}. Discount not applied.")

        scheduled_delivery_time = None
        if delivery_option == 'tomorrow_morning':
            scheduled_delivery_time = datetime.now() + timedelta(days=1)
            scheduled_delivery_time = scheduled_delivery_time.replace(hour=9, minute=0, second=0, microsecond=0)
        elif delivery_option == 'tomorrow_evening':
            scheduled_delivery_time = datetime.now() + timedelta(days=1)
            scheduled_delivery_time = scheduled_delivery_time.replace(hour=17, minute=0, second=0, microsecond=0)
        elif delivery_option == 'day_after_morning':
            scheduled_delivery_time = datetime.now() + timedelta(days=2)
            scheduled_delivery_time = scheduled_delivery_time.replace(hour=9, minute=0, second=0, microsecond=0)
        elif delivery_option == 'day_after_evening':
            scheduled_delivery_time = datetime.now() + timedelta(days=2)
            scheduled_delivery_time = scheduled_delivery_time.replace(hour=17, minute=0, second=0, microsecond=0)

        try:
            with transaction.atomic():
                created_orders = []
                for supplier_pk, data in order_products_info.items():
                    supplier_profile = data['supplier_profile']
                    supplier_total = data['subtotal']

                    supplier_discount_for_this_order = 0
                    if is_co_vendor_order and (total_amount + discount_applied) > 0:
                        supplier_discount_for_this_order = (supplier_total / (total_amount + discount_applied)) * discount_applied
                        supplier_total -= supplier_discount_for_this_order

                    order = Order.objects.create(
                        vendor=vendor_profile,
                        supplier=supplier_profile,
                        delivery_option=delivery_option,
                        scheduled_delivery_time=scheduled_delivery_time,
                        status='pending',
                        total_amount=supplier_total,
                        delivery_address=delivery_address if delivery_address else vendor_profile.location_address,
                        payment_method=payment_method,
                        is_co_vendor_order=is_co_vendor_order,
                        co_vendor_group_id=co_vendor_id if is_co_vendor_order else None,
                        discount_applied=supplier_discount_for_this_order
                    )
                    created_orders.append(order)

                    for item_data in data['items']:
                        OrderItem.objects.create(
                            order=order,
                            product=item_data['product'],
                            quantity=item_data['quantity'],
                            price_per_unit_at_purchase=item_data['price_per_unit_at_purchase'],
                            subtotal=item_data['subtotal']
                        )
                        product_to_update = item_data['product']
                        product_to_update.quantity_available -= item_data['quantity']
                        product_to_update.save()

            messages.success(request, f"Your order(s) have been placed successfully! Total amount: ₹{total_amount:.2f}")
            return redirect('vendor_orders')

        except Exception as e:
            messages.error(request, f"An error occurred while placing your order: {e}")
            return redirect('checkout')

    cart_data_json = request.GET.get('cart_data')
    cart_items = []
    total_amount = 0
    delivery_charge = 0

    if cart_data_json:
        try:
            cart_items_raw = json.loads(cart_data_json)
            for item in cart_items_raw:
                product_id = item.get('id')
                quantity = item.get('quantity')
                if product_id and quantity:
                    product = get_object_or_404(Product, id=product_id)
                    item_subtotal = product.current_price_per_unit * quantity
                    total_amount += item_subtotal
                    cart_items.append({
                        'product': product,
                        'quantity': quantity,
                        'subtotal': item_subtotal
                    })
        except json.JSONDecodeError:
            messages.error(request, "Error loading cart data. Please try adding items again.")
            return redirect('browse_products')
    
    if not cart_items:
        messages.warning(request, "Your cart is empty. Please add items to proceed to checkout.")
        return redirect('browse_products')

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'delivery_charge': delivery_charge,
        'grand_total': total_amount + delivery_charge,
        'vendor_profile': vendor_profile,
        'delivery_options': Order.DELIVERY_OPTIONS,
    }
    return render(request, 'checkout.html', context)

@login_required
def vendor_orders_view(request):
    if not request.user.is_vendor:
        messages.warning(request, "Access denied. Please log in as a Vendor.")
        return redirect('home')
    
    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    
    all_orders = Order.objects.filter(vendor=vendor_profile).order_by('-order_date')

    orders_by_status = {
        'pending': [],
        'confirmed': [],
        'packed': [],
        'out_for_delivery': [],
        'delivered': [],
        'cancelled': [],
    }

    for order in all_orders:
        if order.status in orders_by_status:
            orders_by_status[order.status].append(order)
        else:
            messages.warning(request, f"Order #{order.id} has an unknown status: {order.status}")
            orders_by_status['pending'].append(order)

    context = {
        'vendor_profile': vendor_profile,
        'orders_by_status': orders_by_status,
        'order_status_choices': Order.ORDER_STATUS,
    }
    return render(request, 'vendor_orders.html', context)

@login_required
def vendor_loans_view(request):
    if not request.user.is_vendor:
        messages.warning(request, "Access denied. Please log in as a Vendor.")
        return redirect('home')

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        repayment_period_days = request.POST.get('repayment_period')

        if not (amount and repayment_period_days):
            messages.error(request, "Please provide both loan amount and repayment period.")
            return redirect('vendor_loans')
        
        try:
            amount = float(amount)
            repayment_period_days = int(repayment_period_days)
            
            if amount <= 0:
                messages.error(request, "Loan amount must be positive.")
                return redirect('vendor_loans')
            
            active_loans = Loan.objects.filter(vendor=vendor_profile, status='active').exists()
            if active_loans:
                messages.warning(request, "You have an active loan. Please repay it before applying for a new one.")
                return redirect('vendor_loans')
            
            interest_rate = 0.05
            if repayment_period_days == 2:
                interest_rate = 0.02
            elif repayment_period_days == 7:
                interest_rate = 0.05
            elif repayment_period_days == 14:
                interest_rate = 0.08
            elif repayment_period_days == 30:
                interest_rate = 0.10

            Loan.objects.create(
                vendor=vendor_profile,
                amount_granted=amount,
                repayment_period_days=repayment_period_days,
                interest_rate=interest_rate,
                status='pending',
            )
            messages.success(request, "Loan application submitted successfully! It is pending admin review.")
            return redirect('vendor_loans')

        except ValueError:
            messages.error(request, "Invalid amount or repayment period. Please enter valid numbers.")
        except Exception as e:
            messages.error(request, f"An error occurred during loan application: {e}")
            
    loans = Loan.objects.filter(vendor=vendor_profile).order_by('-disbursement_date')
    
    context = {
        'vendor_profile': vendor_profile,
        'loans': loans,
        'repayment_periods': Loan.REPAYMENT_PERIODS,
    }
    return render(request, 'vendor_loans.html', context)

@login_required
def vendor_leftovers_view(request):
    if not request.user.is_vendor:
        messages.warning(request, "Access denied. Please log in as a Vendor.")
        return redirect('home')

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        quantity = request.POST.get('quantity')
        unit_of_measure = request.POST.get('unit_of_measure')
        price_per_unit = request.POST.get('price_per_unit')
        condition = request.POST.get('condition')
        expiry_date_str = request.POST.get('expiry_date')
        pickup_delivery_preference = request.POST.get('pickup_delivery_preference')
        photo = request.FILES.get('photo')

        if not (item_name and quantity and unit_of_measure and price_per_unit and condition and pickup_delivery_preference):
            messages.error(request, "Please fill all required fields for the leftover listing.")
            return redirect('vendor_leftovers')

        try:
            quantity = float(quantity)
            price_per_unit = float(price_per_unit)
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None

            if quantity <= 0 or price_per_unit < 0:
                messages.error(request, "Quantity must be positive and price cannot be negative.")
                return redirect('vendor_leftovers')
            
            LeftoverListing.objects.create(
                seller_vendor=vendor_profile,
                item_name=item_name,
                quantity=quantity,
                unit_of_measure=unit_of_measure,
                price_per_unit=price_per_unit,
                condition=condition,
                expiry_date=expiry_date,
                pickup_delivery_preference=pickup_delivery_preference,
                photo=photo,
                is_active=True
            )
            messages.success(request, f"'{item_name}' listed successfully in the Leftover Market!")
            return redirect('vendor_leftovers')

        except ValueError:
            messages.error(request, "Invalid quantity or price. Please enter valid numbers.")
        except Exception as e:
            messages.error(request, f"An error occurred while listing your item: {e}")
    
    my_listings = LeftoverListing.objects.filter(seller_vendor=vendor_profile).order_by('-listing_date')
    
    other_listings = LeftoverListing.objects.filter(
        ~Q(seller_vendor=vendor_profile),  # Exclude current vendor's own listings
        is_active=True,
        expiry_date__gte=timezone.now().date(),  # Only show items not expired
    ).order_by('-listing_date')

    context = {
        'my_listings': my_listings,
        'other_listings': other_listings,
        'unit_of_measure_choices': Product.UNIT_OF_MEASURE_CHOICES,
        'condition_choices': LeftoverListing.CONDITION_CHOICES,
        'pickup_delivery_choices': LeftoverListing.pickup_delivery_preference.field.choices,
    }
    return render(request, 'vendor_leftovers.html', context)

@login_required
def mark_leftover_as_sold_view(request, listing_id):
    if request.method == 'POST':
        leftover_listing = get_object_or_404(LeftoverListing, id=listing_id)
        
        if leftover_listing.seller_vendor.user != request.user and not request.user.is_staff:
            messages.error(request, "You are not authorized to mark this item as sold.")
            return redirect('vendor_leftovers')

        if not leftover_listing.is_active:
            messages.warning(request, "This item is already marked as sold or inactive.")
            return redirect('vendor_leftovers')

        try:
            buyer_vendor_id = request.POST.get('buyer_vendor_id')
            buyer_vendor_profile = None
            if buyer_vendor_id:
                try:
                    buyer_user = User.objects.get(Q(username=buyer_vendor_id) | Q(phone_number=buyer_vendor_id) | Q(email=buyer_vendor_id))
                    if buyer_user.is_vendor:
                        buyer_vendor_profile = buyer_user.vendor_profile
                except User.DoesNotExist:
                    messages.warning(request, "Buyer vendor not found, but item marked as sold.")

            leftover_listing.is_active = False
            leftover_listing.buyer_vendor = buyer_vendor_profile
            leftover_listing.transaction_date = timezone.now()
            leftover_listing.save()
            
            seller_profile = leftover_listing.seller_vendor
            seller_profile.total_reviews_as_seller += 1
            seller_profile.average_rating_as_seller = (seller_profile.average_rating_as_seller * (seller_profile.total_reviews_as_seller - 1) + 5) / seller_profile.total_reviews_as_seller
            seller_profile.save()

            messages.success(request, f"'{leftover_listing.item_name}' has been marked as sold!")
            return redirect('vendor_leftovers')

        except Exception as e:
            messages.error(request, f"An error occurred while marking the item as sold: {e}")
            return redirect('vendor_leftovers')
    
    messages.error(request, "Invalid request for marking item as sold.")
    return redirect('vendor_leftovers')


@login_required
def vendor_my_reviews_view(request):
    if not request.user.is_vendor:
        messages.warning(request, "Access denied. Please log in as a Vendor.")
        return redirect('home')

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if not (supplier_id and rating):
            messages.error(request, "Please select a supplier and provide a rating.")
            return redirect('vendor_my_reviews')
        
        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                messages.error(request, "Rating must be between 1 and 5.")
                return redirect('vendor_my_reviews')

            supplier_to_review = get_object_or_404(SupplierProfile, id=supplier_id)

            has_ordered = Order.objects.filter(
                vendor=vendor_profile,
                supplier=supplier_to_review,
                status='delivered'
            ).exists()

            if not has_ordered:
                messages.error(request, "You can only review suppliers you have ordered from and received delivery.")
                return redirect('vendor_my_reviews')
            
            existing_review = Review.objects.filter(
                reviewer_vendor=vendor_profile,
                reviewed_supplier=supplier_to_review
            ).first()

            if existing_review:
                messages.warning(request, "You have already reviewed this supplier. You can update your existing review in the future.")
                return redirect('vendor_my_reviews')


            review = Review.objects.create(
                reviewer_vendor=vendor_profile,
                reviewed_supplier=supplier_to_review,
                rating=rating,
                comment=comment,
                is_moderated=False
            )

            with transaction.atomic():
                supplier_to_review.total_reviews += 1
                if supplier_to_review.total_reviews == 1:
                    supplier_to_review.average_rating = rating
                else:
                    supplier_to_review.average_rating = (
                        (supplier_to_review.average_rating * (supplier_to_review.total_reviews - 1)) + rating
                    ) / supplier_to_review.total_reviews
                supplier_to_review.save()

            messages.success(request, f"Your review for {supplier_to_review.business_name} has been submitted!")
            return redirect('vendor_my_reviews')

        except ValueError:
            messages.error(request, "Invalid rating. Please select a number.")
        except Exception as e:
            messages.error(request, f"An error occurred during review submission: {e}")

    my_reviews = Review.objects.filter(reviewer_vendor=vendor_profile).order_by('-review_date')
    
    suppliers_to_review = SupplierProfile.objects.filter(
        orders_received__vendor=vendor_profile,
        orders_received__status='delivered'
    ).exclude(reviews_received__reviewer_vendor=vendor_profile).distinct()

    context = {
        'my_reviews': my_reviews,
        'suppliers_to_review': suppliers_to_review,
        'rating_choices': Review.rating.field.choices,
    }
    return render(request, 'vendor_my_reviews.html', context)

# --- API View to fetch Order Details for Modal ---
@csrf_exempt
@login_required
def order_details_api_view(request, order_id):
    if not (request.user.is_vendor or request.user.is_supplier):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    order = get_object_or_404(Order, id=order_id)

    if request.user.is_vendor and order.vendor.user != request.user:
        return JsonResponse({'error': 'Not authorized to view this order.'}, status=403)
    if request.user.is_supplier and order.supplier.user != request.user:
        return JsonResponse({'error': 'Not authorized to view this order.'}, status=403)

    order_items_data = []
    for item in order.items.all():
        order_items_data.append({
            'product_name': item.product.name,
            'quantity': float(item.quantity),
            'unit_of_measure': item.product.unit_of_measure,
            'price_per_unit_at_purchase': float(item.price_per_unit_at_purchase),
            'subtotal': float(item.subtotal),
        })

    order_data = {
        'id': order.id,
        'vendor_name': order.vendor.name,
        'supplier_name': order.supplier.business_name,
        'order_date': order.order_date.isoformat(),
        'delivery_option_display': order.get_delivery_option_display(),
        'scheduled_delivery_time': order.scheduled_delivery_time.isoformat() if order.scheduled_delivery_time else None,
        'status_display': order.get_status_display(),
        'total_amount': float(order.total_amount),
        'delivery_address': order.delivery_address,
        'payment_method_display': order.get_payment_method_display(),
        'is_co_vendor_order': order.is_co_vendor_order,
        'co_vendor_group_id': order.co_vendor_group_id,
        'discount_applied': float(order.discount_applied),
        'items': order_items_data,
    }
    return JsonResponse(order_data)

# --- API View to fetch Product Details for Edit Modal ---
@csrf_exempt
@login_required
def product_details_api_view(request, product_id):
    if not request.user.is_supplier:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    product = get_object_or_404(Product, id=product_id)

    if product.supplier.user != request.user:
        return JsonResponse({'error': 'Not authorized to view this product.'}, status=403)

    product_data = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'category_id': product.category.id if product.category else None,
        'unit_of_measure': product.unit_of_measure,
        'current_price_per_unit': float(product.current_price_per_unit),
        'quantity_available': float(product.quantity_available),
        'image_url': product.image.url if product.image else None,
        'quality_grade': product.quality_grade,
        'is_organic': product.is_organic,
        'ai_suggested_min_price': float(product.ai_suggested_min_price) if product.ai_suggested_min_price else None,
        'ai_suggested_max_price': float(product.ai_suggested_max_price) if product.ai_suggested_max_price else None,
    }
    return JsonResponse(product_data)

# --- API View to update Product Price directly from AI suggestion ---
@csrf_exempt
@login_required
def update_product_price_api_view(request, product_id):
    if not request.user.is_supplier:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)

        if product.supplier.user != request.user:
            return JsonResponse({'error': 'Not authorized to update this product.'}, status=403)
        
        try:
            data = json.loads(request.body)
            new_price = Decimal(str(data.get('new_price'))) # <--- FIX: Convert to Decimal

            if new_price <= 0:
                return JsonResponse({'error': 'New price must be positive.'}, status=400)
            
            product.current_price_per_unit = new_price
            product.save()
            messages.success(request, f"Price for '{product.name}' updated to ₹{new_price:.2f} successfully!")
            return JsonResponse({'success': True, 'new_price': float(new_price)}) # Convert back to float for JSON

        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid price provided.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {e}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)


# --- API View to add AI suggested product to cart (client-side) ---
@csrf_exempt
@login_required
def add_ai_suggestion_to_cart_api_view(request):
    if not request.user.is_vendor:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            suggested_quantity = data.get('suggested_quantity')

            product = get_object_or_404(Product, id=product_id)

            if product.quantity_available < suggested_quantity:
                return JsonResponse({'error': f"Not enough {product.name} available. Only {product.quantity_available} {product.unit_of_measure} left."}, status=400)
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': float(product.current_price_per_unit),
                'unit': product.unit_of_measure,
                'quantity': suggested_quantity
            }
            return JsonResponse({'success': True, 'product': product_data})

        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid product data provided.'}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {e}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)


# --- Supplier Specific Pages ---
@login_required
def supplier_orders_view(request):
    if not request.user.is_supplier:
        messages.warning(request, "Access denied. Please log in as a Supplier.")
        return redirect('home')

    supplier_profile = get_object_or_404(SupplierProfile, user=request.user)

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('new_status')

        if not (order_id and new_status):
            messages.error(request, "Invalid order ID or status provided.")
            return redirect('supplier_orders')
        
        try:
            order = get_object_or_404(Order, id=order_id, supplier=supplier_profile)
            
            valid_statuses = [choice[0] for choice in Order.ORDER_STATUS]
            if new_status not in valid_statuses:
                messages.error(request, f"Invalid status '{new_status}' selected.")
                return redirect('supplier_orders')

            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.id} status updated to '{order.get_status_display()}' successfully!")
            return redirect('supplier_orders')

        except Order.DoesNotExist:
            messages.error(request, "Order not found or you are not authorized to manage this order.")
        except Exception as e:
            messages.error(request, f"An error occurred while updating order status: {e}")
        
    all_orders = Order.objects.filter(supplier=supplier_profile).order_by('-order_date')

    orders_by_status = {
        'pending': [],
        'confirmed': [],
        'packed': [],
        'out_for_delivery': [],
        'delivered': [],
        'cancelled': [],
    }

    for order in all_orders:
        if order.status in orders_by_status:
            orders_by_status[order.status].append(order)
        else:
            messages.warning(request, f"Order #{order.id} has an unknown status: {order.status}")
            orders_by_status['pending'].append(order)

    context = {
        'supplier_profile': supplier_profile,
        'orders_by_status': orders_by_status,
        'order_status_choices': Order.ORDER_STATUS,
    }
    return render(request, 'supplier_orders.html', context)

@login_required
def supplier_inventory_view(request):
    if not request.user.is_supplier:
        messages.warning(request, "Access denied.")
        return redirect('home')

    supplier_profile = get_object_or_404(SupplierProfile, user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_product':
            item_name = request.POST.get('name')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            unit_of_measure = request.POST.get('unit_of_measure')
            current_price_per_unit = request.POST.get('current_price_per_unit')
            quantity_available = request.POST.get('quantity_available')
            quality_grade = request.POST.get('quality_grade')
            is_organic = request.POST.get('is_organic') == 'on'
            image = request.FILES.get('image')

            if not (item_name and category_id and unit_of_measure and current_price_per_unit and quantity_available and quality_grade):
                messages.error(request, "Please fill all required fields for adding a product.")
                return redirect('supplier_inventory')
            
            try:
                category = get_object_or_404(Category, id=category_id)
                current_price_per_unit = float(current_price_per_unit)
                quantity_available = float(quantity_available)

                if current_price_per_unit <= 0 or quantity_available < 0:
                    messages.error(request, "Price must be positive and quantity cannot be negative.")
                    return redirect('supplier_inventory')
                
                Product.objects.create(
                    name=item_name,
                    description=description,
                    category=category,
                    supplier=supplier_profile,
                    unit_of_measure=unit_of_measure,
                    current_price_per_unit=current_price_per_unit,
                    quantity_available=quantity_available,
                    quality_grade=quality_grade,
                    is_organic=is_organic,
                    image=image
                )
                messages.success(request, f"Product '{item_name}' added successfully!")
                return redirect('supplier_inventory')

            except ValueError:
                messages.error(request, "Invalid price or quantity. Please enter valid numbers.")
            except Exception as e:
                messages.error(request, f"An error occurred while adding the product: {e}")

        elif action == 'edit_product':
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, id=product_id, supplier=supplier_profile)

            item_name = request.POST.get('name')
            description = request.POST.get('description')
            category_id = request.POST.get('category')
            unit_of_measure = request.POST.get('unit_of_measure')
            current_price_per_unit = request.POST.get('current_price_per_unit')
            quantity_available = request.POST.get('quantity_available')
            quality_grade = request.POST.get('quality_grade')
            is_organic = request.POST.get('is_organic') == 'on'
            image = request.FILES.get('image')

            if not (item_name and category_id and unit_of_measure and current_price_per_unit and quantity_available and quality_grade):
                messages.error(request, "Please fill all required fields for editing the product.")
                return redirect('supplier_inventory')
            
            try:
                category = get_object_or_404(Category, id=category_id)
                current_price_per_unit = float(current_price_per_unit)
                quantity_available = float(quantity_available)

                if current_price_per_unit <= 0 or quantity_available < 0:
                    messages.error(request, "Price must be positive and quantity cannot be negative.")
                    return redirect('supplier_inventory')
                
                product.name = item_name
                product.description = description
                product.category = category
                product.unit_of_measure = unit_of_measure
                product.current_price_per_unit = current_price_per_unit
                product.quantity_available = quantity_available
                product.quality_grade = quality_grade
                product.is_organic = is_organic
                if image:
                    product.image = image
                product.save()

                messages.success(request, f"Product '{item_name}' updated successfully!")
                return redirect('supplier_inventory')

            except ValueError:
                messages.error(request, "Invalid price or quantity. Please enter valid numbers.")
            except Exception as e:
                messages.error(request, f"An error occurred while updating the product: {e}")
        
        else:
            messages.error(request, "Invalid action for inventory management.")
            return redirect('supplier_inventory')

    products = Product.objects.filter(supplier=supplier_profile).order_by('name')
    categories = Category.objects.all().order_by('name')

    context = {
        'supplier_profile': supplier_profile,
        'products': products,
        'categories': categories,
        'unit_of_measure_choices': Product.UNIT_OF_MEASURE_CHOICES,
        'quality_grade_choices': Product.QUALITY_GRADE_CHOICES,
    }
    return render(request, 'supplier_inventory.html', context)

@login_required
def supplier_upstream_suppliers_view(request):
    if not request.user.is_supplier:
        messages.warning(request, "Access denied.")
        return redirect('home')

    supplier_profile = get_object_or_404(SupplierProfile, user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        contact_person = request.POST.get('contact_person')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        address = request.POST.get('address')

        if not (name and phone_number):
            messages.error(request, "Supplier Name and Phone Number are required.")
            return redirect('supplier_upstream_suppliers')
        
        try:
            existing_supplier = UpstreamSupplier.objects.filter(phone_number=phone_number).first()
            if existing_supplier:
                if supplier_profile not in existing_supplier.msh_suppliers.all():
                    existing_supplier.msh_suppliers.add(supplier_profile)
                    messages.success(request, f"Existing supplier '{name}' linked to your MSH.")
                else:
                    messages.info(request, f"Supplier '{name}' is already linked to your MSH.")
                return redirect('supplier_upstream_suppliers')

            new_upstream_supplier = UpstreamSupplier.objects.create(
                name=name,
                contact_person=contact_person,
                phone_number=phone_number,
                email=email,
                address=address
            )
            new_upstream_supplier.msh_suppliers.add(supplier_profile)
            messages.success(request, f"Upstream supplier '{name}' added and linked successfully!")
            return redirect('supplier_upstream_suppliers')

        except IntegrityError:
            messages.error(request, "A supplier with this phone number already exists.")
        except Exception as e:
            messages.error(request, f"An error occurred while adding supplier: {e}")

    upstream_suppliers = supplier_profile.upstream_suppliers.all().order_by('name')

    context = {
        'supplier_profile': supplier_profile,
        'upstream_suppliers': upstream_suppliers,
    }
    return render(request, 'supplier_upstream_suppliers.html', context)


@login_required
def financials_view(request):
    if not request.user.is_supplier:
        messages.warning(request, "Access denied.")
        return redirect('home')

    supplier_profile = get_object_or_404(SupplierProfile, user=request.user)

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    daily_earnings_data = Order.objects.filter(
        supplier=supplier_profile,
        status='delivered',
        order_date__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0.00

    weekly_earnings_data = Order.objects.filter(
        supplier=supplier_profile,
        status='delivered',
        order_date__date__gte=today - timedelta(days=6)
    ).aggregate(total=Sum('total_amount'))['total'] or 0.00

    monthly_earnings_data = Order.objects.filter(
        supplier=supplier_profile,
        status='delivered',
        order_date__date__gte=start_of_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0.00

    transaction_log = Order.objects.filter(
        supplier=supplier_profile,
        status='delivered'
    ).order_by('-order_date')

    context = {
        'supplier_profile': supplier_profile,
        'daily_earnings': daily_earnings_data,
        'weekly_earnings': weekly_earnings_data,
        'monthly_earnings': monthly_earnings_data,
        'transaction_log': transaction_log,
    }
    return render(request, 'supplier_financials.html', context)


@login_required
def supplier_profile_view(request):
    if not request.user.is_supplier:
        messages.warning(request, "Access denied.")
        return redirect('home')

    supplier_profile = get_object_or_404(SupplierProfile, user=request.user)

    if request.method == 'POST':
        business_name = request.POST.get('business_name')
        contact_person = request.POST.get('contact_person')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        location_pincode = request.POST.get('location_pincode')
        location_address = request.POST.get('location_address')
        business_registration_details = request.POST.get('business_registration_details')
        storage_capacity_sqft = request.POST.get('storage_capacity_sqft')

        if not (business_name and contact_person and phone_number and location_pincode and location_address):
            messages.error(request, "Business Name, Contact Person, Phone, Pincode, and Address are required.")
            return redirect('supplier_profile')
        
        try:
            supplier_profile.business_name = business_name
            supplier_profile.contact_person = contact_person
            supplier_profile.phone_number = phone_number
            supplier_profile.user.email = email
            supplier_profile.email = email
            supplier_profile.location_pincode = location_pincode
            supplier_profile.location_address = location_address
            supplier_profile.business_registration_details = business_registration_details
            supplier_profile.storage_capacity_sqft = int(storage_capacity_sqft) if storage_capacity_sqft else None
            
            supplier_profile.user.save()
            supplier_profile.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('supplier_profile')

        except ValueError:
            messages.error(request, "Invalid input for storage capacity. Please enter a number.")
        except Exception as e:
            messages.error(request, f"An error occurred while updating your profile: {e}")

    vendor_reviews = Review.objects.filter(reviewed_supplier=supplier_profile, reviewer_vendor__isnull=False).order_by('-review_date')

    context = {
        'supplier_profile': supplier_profile,
        'vendor_reviews': vendor_reviews,
    }
    return render(request, 'supplier_profile.html', context)
