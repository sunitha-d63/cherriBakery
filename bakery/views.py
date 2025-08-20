from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from .models import ProductCategory, Product, Wishlist,ContactMessage
from .models import Order, OrderItem, Payment,Cart, CartItem
from .forms import RegisterForm, LoginForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage
import re
from decimal import Decimal
from django.utils import timezone  
from datetime import timedelta 
import random

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, 'You have been logged in successfully!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid email or password')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {
        'form': form,
        'active_tab': 'login'
    })

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email 
            user.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = RegisterForm()
    
    return render(request, 'registration/register.html', {
        'form': form,
        'active_tab': 'register'
    })

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            new_password = form.cleaned_data['new_password']
            
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully! You can now login with your new password.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address')
    else:
        form = PasswordResetForm()
    
    return render(request, 'registration/password_reset.html', {'form': form})


@login_required(login_url='login')
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user, 
        product=product
    )
    
    if not created:
        wishlist_item.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required(login_url='login')
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'bakery/wishlist.html', {'wishlist_items': items})

@require_POST
@login_required(login_url='login')
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect('wishlist')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

def all_products(request):
    categories = ProductCategory.objects.prefetch_related('products')
    
    if request.user.is_authenticated:
        wishlist_product_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)
    else:
        wishlist_product_ids = []

    for category in categories:
        for product in category.products.all():
            product.is_in_wishlist = product.id in wishlist_product_ids

    return render(request, 'bakery/products.html', {
        'categories': categories
    })

def category_products(request, slug):
    category = get_object_or_404(ProductCategory, slug=slug)
    products = Product.objects.filter(category=category)

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user,
            product__in=products
        ).values_list('product_id', flat=True)
    else:
        wishlist_ids = []

    for product in products:
        product.is_in_wishlist = product.id in wishlist_ids

    return render(request, 'bakery/category_products.html', {
        'category': category,
        'products': products
    })

@login_required(login_url='login')
def product_detail(request, category_slug, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        category__slug=category_slug
    )
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:3]
    weight_options = ['500 G', '1 KG', '2 KG', '3 KG', '4 KG', '5 KG']
    
    if request.method == 'POST':
        pincode = request.POST.get('pincode', '').strip()
        weight = request.POST.get('weight', '').strip()
        quantity = int(request.POST.get('quantity', '1'))
        
        errors = {}

        if not pincode or not pincode.isdigit() or len(pincode) != 6:
            errors['pincode_error'] = True
        if not weight or weight not in weight_options:
            errors['weight_error'] = True
            
        if errors:
            return render(request, 'bakery/product_detail.html', {
                'product': product,
                'related_products': related_products,
                'weight_options': weight_options,
                **errors,
                'pincode': pincode,
                'selected_weight': weight,
                'quantity': quantity,
            })

        if 'add_to_cart' in request.POST:
            cart, created = Cart.objects.get_or_create(user=request.user if request.user.is_authenticated else None)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                weight=weight,
                defaults={
                    'quantity': quantity,
                    'price': product.base_price
                }
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            messages.success(request, 'Product added to cart!')
            return redirect('cart_page') 
            
        else: 
            base_price = float(product.base_price) if isinstance(product.base_price, Decimal) else product.base_price

            request.session['order_data'] = {
                'product_id': product.id,
                'product_title': product.title,
                'category_slug': category_slug,
                'pincode': pincode,
                'weight': weight,
                'quantity': quantity,
                'base_price': base_price,
            }
            return redirect('payment_page')
    
    return render(request, 'bakery/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'weight_options': weight_options,
    })

import json
from django.shortcuts import render
from .models import Cart

def cart_page(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.filter(id=cart_id).first()
            if not cart:
                cart = Cart.objects.create()
                request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id

    cart_items = cart.items.all()

    cart_data = [
        {
            "product": item.product.title,
            "price": float(item.price),
            "quantity": item.quantity,
            "weight": item.weight,
            "total_price": float(item.total_price),
        }
        for item in cart_items
    ]

    context = {
        "cart_items": cart_items,
        "subtotal": cart.subtotal,
        "delivery_charge": cart.delivery_charge,
        "tax_amount": cart.tax_amount,
        "cart_total": cart.total,
        "cart_data_json": json.dumps(cart_data),
    }
    return render(request, "bakery/cart.html", context)

@require_POST
def update_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        try:
            item = CartItem.objects.get(id=item_id)
            item.quantity = quantity
            item.save()
            return JsonResponse({'success': True})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    """Remove a specific item from the user's cart"""
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect('cart_page') 

 
def validate_upi_id(value):
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$'
    if not re.match(pattern, value):
        raise ValidationError('Invalid UPI ID format. Example: username@upi')

def validate_card_number(value):
    if not value.isdigit() or len(value) not in (15, 16):
        raise ValidationError('Invalid card number')
    digits = [int(x) for x in value]
    checksum = sum(digits[-1::-2])
    for d in digits[-2::-2]:
        checksum += sum(divmod(d * 2, 10))
    if checksum % 10 != 0:
        raise ValidationError('Invalid card number')

def validate_mobile(value):
    if not value.isdigit() or len(value) != 10:
        raise ValidationError('Mobile number must be 10 digits')


def validate_name(value):
    if not re.match(r'^[a-zA-Z\s\'-]{3,}$', value):
        raise ValidationError('Name can only contain letters, spaces, apostrophes and hyphens')


def validate_location(value):
    if not re.match(r'^[\w\s\.,\-/]{3,}$', value, re.UNICODE):
        raise ValidationError(
            'Location must be at least 3 characters and can only contain '
            'letters, numbers, spaces, commas ( , ), periods ( . ), hyphens ( - ), or slashes ( / ).'
        )

def validate_address(value):
    if not re.match(r'^[\w\s\.,\-/#&()]{10,}$', value, re.UNICODE):
        raise ValidationError(
            'Address must be at least 10 characters and can only contain '
            'letters, numbers, spaces, commas ( , ), periods ( . ), hyphens ( - ), '
            'slashes ( / ), hashes ( # ), ampersands ( & ), or parentheses ( ( ) ).'
        )

def validate_notes(value):
    if value and not re.match(r'^[\w\s\.,\-!?()]{0,200}$', value, re.UNICODE):
        raise ValidationError(
            'Notes can only contain letters, numbers, spaces, commas ( , ), '
            'periods ( . ), hyphens ( - ), exclamation marks ( ! ), '
            'question marks ( ? ), or parentheses ( ( ) ). Max 200 characters.'
        )

def payment_page(request):
    order_data = request.session.get('order_data')
    if not order_data:
        return redirect('home')
    
    product = get_object_or_404(Product, id=order_data['product_id'])
    quantity = int(order_data['quantity'])
    base_price = Decimal(str(order_data['base_price']))
    
    subtotal = quantity * base_price
    discount = subtotal * Decimal('0.15')
    delivery_fee = Decimal('40') if subtotal < Decimal('500') else Decimal('0')
    gst = subtotal * Decimal('0.05')
    total = subtotal - discount + delivery_fee + gst
    
    context = {
        'product': {
            'id': product.id,
            'title': product.title,
            'description': product.description,
            'weight': order_data['weight'],
            'quantity': quantity,
            'image_url': product.image.url if product.image else '/static/images/default-product.jpg',
            'base_price': base_price
        },
        'prices': {
            'subtotal': subtotal,
            'discount': discount,
            'delivery_fee': delivery_fee,
            'gst': gst,
            'total': total
        }
    }
    return render(request, 'bakery/payment.html', context)

def process_payment(request):
    if request.method == 'POST':
        errors = {}

        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        notes = request.POST.get('notes', '').strip()
        address = request.POST.get('address', '').strip()
        try:
            validate_name(name)
        except ValidationError as e:
            errors['name'] = str(e)
            
        try:
            validate_location(location)
        except ValidationError as e:
            errors['location'] = str(e)
            
        try:
            validate_mobile(mobile) 
        except ValidationError as e:
            errors['mobile'] = str(e)
            
        try:
            validate_notes(notes)
        except ValidationError as e:
            errors['notes'] = str(e)
            
        try:
            validate_address(address)
        except ValidationError as e:
            errors['address'] = str(e)

        payment_method = request.POST.get('paymentOption')
        if not payment_method:
            errors['payment'] = 'Select a payment method'
        else:
            if payment_method == 'upi':
                upi_id = request.POST.get('upi_id', '').strip()
                try:
                    validate_upi_id(upi_id)
                except ValidationError as e:
                    errors['upi'] = str(e)
            elif payment_method == 'wallet':
                wallet_id = request.POST.get('wallet_id', '').strip()
                if not wallet_id:
                    errors['wallet'] = 'Wallet ID is required'
            elif payment_method == 'credit':
                card_number = request.POST.get('card_number', '').strip()
                expiry = request.POST.get('expiry', '').strip()
                cvv = request.POST.get('cvv', '').strip()
                
                try:
                    validate_card_number(card_number)
                except ValidationError as e:
                    errors['card'] = str(e)
                
                if not expiry or not re.match(r'^\d{2}/\d{2}$', expiry):
                    errors['expiry'] = 'Enter valid expiry (MM/YY)'
                
                if not cvv or not cvv.isdigit() or len(cvv) not in (3, 4):
                    errors['cvv'] = 'Enter valid CVV'
        
        if not errors:
            order = Order.objects.create(
                customer_name=name,
                customer_mobile=mobile,
                delivery_location=location,
                delivery_address=address,
                special_notes=notes,
                payment_method=payment_method,
                subtotal=Decimal(request.POST.get('subtotal', 0)),
                discount=Decimal(request.POST.get('discount', 0)),
                delivery_fee=Decimal(request.POST.get('delivery_fee', 0)),
                tax_amount=Decimal(request.POST.get('gst', 0)),
                total_amount=Decimal(request.POST.get('total', 0)),
            )
            OrderItem.objects.create(
                order=order,
                product=get_object_or_404(Product, id=request.POST.get('product_id')),
                quantity=int(request.POST.get('quantity', 1)),
                unit_price=Decimal(request.POST.get('base_price', 0)),
                weight=request.POST.get('weight'),
            )
            tracking_id = f"TRK{order.id}{random.randint(1000, 9999)}"
            context = {
    'order': order,
    'order_date': order.order_date,
    'expected_delivery': order.order_date + timedelta(days=1),
    'tracking_id': f"TRK{order.id}{random.randint(1000, 9999)}",
    'timeline': [
        {'step': 'PLACE YOUR ORDER', 'time': order.order_date},
        {'step': 'BILLING YOUR ORDER', 'time': order.order_date + timedelta(hours=1)},
        {'step': 'LOADING YOUR ORDER', 'time': order.order_date + timedelta(hours=3, minutes=30)},
        {'step': 'DELIVERY EXPECTED', 'time': order.order_date + timedelta(days=1)},
    ]
}
            return render(request, 'bakery/order_confirmation.html', context)

        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        context = {
            'product': {
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'weight': request.POST.get('weight'),
                'quantity': int(request.POST.get('quantity', 1)),
                'image_url': product.image.url if product.image else '/static/images/default-product.jpg',
                'base_price': Decimal(request.POST.get('base_price', 0))
            },
            'prices': {
                'subtotal': Decimal(request.POST.get('subtotal', 0)),
                'discount': Decimal(request.POST.get('discount', 0)),
                'delivery_fee': Decimal(request.POST.get('delivery_fee', 0)),
                'gst': Decimal(request.POST.get('gst', 0)),
                'total': Decimal(request.POST.get('total', 0))
            },
            'form_data': request.POST,
            'errors': errors
        }
        return render(request, 'bakery/payment.html', context)
    
    return redirect('payment_page')

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'bakery/order_confirmation.html', {'order': order})

def delivery_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'bakery/delivery_details.html', {'order': order})


@login_required(login_url='login')
def clear_wishlist(request):
    user = request.user
    user.wishlist_items.all().delete()
    return redirect('wishlist') 

@login_required(login_url='login')
def about(request):
    cards = [
        "images/card1.png",
        "images/card2.png",
        "images/card3.png",
        "images/card4.png",
        "images/card5.png",
    ]
    return render(request, "bakery/about.html", {"cards": cards})

@login_required(login_url='login')
def blog(request):
    return render(request, 'bakery/blog.html')

@login_required(login_url='login')
def home(request):
    banners = [
        {
            'title': "Baked with Love, Served with Joy",
            'subtitle': "Freshly baked breads, cakes, and pastries made daily with the finest ingredients",
            'bannerImg': "images/slide1.png",
            'arrowImg': "images/polygon.png",
            'textClass': "text-dark",
        },
        {
            'title': "Crafting Artisan Bakes Since 2012",
            'subtitle': "Freshly baked breads, cakes, and pastries made daily with the fineExperience the rich tradition of baking with every bite.st ingredients",
            'bannerImg': "images/slide2.png",
            'arrowImg': "images/polygon2.png",
            'textClass': "text-white",
        },
        {
            'title': "Your Neighborhood Bakery",
            'subtitle': "From oven to your table - fresh, warm, and delicious.",
            'bannerImg': "images/slide3.png",
            'arrowImg': "images/polygon3.png",
            'textClass': "text-dark",
        },
        {
            'title': "Fresh. Local. Handmade.",
            'subtitle': "We bake daily so you can enjoy real flavor, every time.",
            'bannerImg': "images/slide4.png",
            'arrowImg': "images/polygon4.png",
            'textClass': "text-dark",
        },
    ]
    testimonials = [
        {
            "image": "images/user1.png",
            "text": '"A hidden gem with real passion behind every bake."',
            "subtext":'"You can taste the quality in every bite. It’s clear they care deeply about their craft."',
            "author": "— Daniel K., Chef & Culinary Enthusiast",
        },
        {
            "image": "images/user2.png",
            "text": '"The kids love the cookies—and so do I!"',
            "subtext":'"We stop by after school for their chocolate chip cookies. Soft, gooey, and always fresh."',
            "author": "— Lena W., Mom of Two",
        },
        {
            "image": "images/user3.png",
            "text": '"Absolutely the nest bakery in town!"',
            "subtext":'"From the moment you walk in,the smell is heavenly.Their sourdough is unmatched,and the staff is always so warm and welcoming."',
            "author": "— Jessica M.,Local Foodie",
        },
        {
            "image": "images/user4.png",
            "text": '"Their croissants are the better than and I had in  Paris."',
            "subtext":'"Crispy, buttery,and perfectly flasky—these croissants are pure perfection. I come here every weekend just for them!"',
            "author": "— Mark R., Travel Blogger",
        },
        {
            "image": "images/user5.png",
            "text": '"Our wedding cake was everything we dreamed of."',
            "subtext":'"Beautiful,delicious, and made with love. Thank you for making our special day unforgettable!"',
            "author": "— Priya & Aaran, Newlyweds",
        },
    ]
    return render(request, 'bakery/home.html', {
        'banners': banners,
        'testimonials': testimonials,
    })


@login_required(login_url='login')
def contact(request):
    locations = [
        {"city": "Chennai", "addr": "No. 45, Anna Salai, T. Nagar, Chennai - 600017"},
        {"city": "Coimbatore", "addr": "12, DB Road, RS Puram, Coimbatore - 641002"},
        {"city": "Madurai", "addr": "28, KK Nagar Main Road, Madurai - 625020"},
        {"city": "Tiruchirappalli (Trichy)", "addr": "7, Salai Road, Thillai Nagar, Trichy - 620018"},
        {"city": "Salem", "addr": "15, Five Roads, Fairlands, Salem - 636016"},
        {"city": "Tirunelveli", "addr": "11, South Bypass Road, Palayamkottai, Tirunelveli - 627002"},
        {"city": "Erode", "addr": "9, Brough Road, Erode - 638001"},
        {"city": "Vellore", "addr": "14, Katpadi Road, Gandhi Nagar, Vellore - 632006"},
        {"city": "Thoothukudi (Tuticorin)", "addr": "6, Beach Road, Tuticorin - 628001"},
        {"city": "Thanjavur", "addr": "10, Medical College Road, Thanjavur - 613004"},
        {"city": "Dindigul", "addr": "4, GTN Road, Dindigul - 624005"},
        {"city": "Kanchipuram", "addr": "3, Ekambaranathar Sannathi Street, Kanchipuram - 631502"},
        {"city": "Karur", "addr": "22, Kovai Road, Karur - 639002"},
        {"city": "Nagercoil", "addr": "16, Cape Road, Vadasery, Nagercoil - 629001"},
        {"city": "Cuddalore", "addr": "8, Beach Road, Cuddalore - 607001"},
        {"city": "Villupuram", "addr": "19, Tindivanam Road, Villupuram - 605602"},
        {"city": "Namakkal", "addr": "5, Salem Road, Namakkal - 637001"},
        {"city": "Tiruppur", "addr": "20, Avinashi Road, Tiruppur - 641603"},
    ]
    
    if request.method == 'POST':
        errors = {}
        form_data = request.POST.copy() 
        name = form_data.get('name', '').strip()
        if not name:
            errors['name'] = "Name is required"
        elif not re.match(r'^[A-Za-z ]+$', name):
            errors['name'] = "Only letters and spaces allowed"
        elif len(name) < 2 or len(name) > 100:
            errors['name'] = "Name must be 2-100 characters"
        
        email = form_data.get('email', '').strip()
        if not email:
            errors['email'] = "Email is required"
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors['email'] = "Please enter a valid email address"

        phone = form_data.get('phone', '').strip()
        if not phone:
            errors['phone'] = "Phone number is required"
        elif not re.match(r'^\d{10}$', phone):
            errors['phone'] = "Phone must be exactly 10 digits"

        subject = form_data.get('subject', '').strip()
        if not subject:
            errors['subject'] = "Subject is required"
        elif not re.match(r'^[A-Za-z0-9 ,.!?-]+$', subject):
            errors['subject'] = "Subject cannot contain special characters except ,.!?-"
        elif len(subject) < 5 or len(subject) > 100:
            errors['subject'] = "Subject must be 5-100 characters"
        
        message = form_data.get('message', '').strip()
        if not message:
            errors['message'] = "Message is required"
        elif not re.match(r'^[A-Za-z0-9 \n,.!?-]+$', message):
            errors['message'] = "Message cannot contain special characters except ,.!?-"
        elif len(message) < 10 or len(message) > 1000:
            errors['message'] = "Message must be 10-1000 characters"
        
        if not errors:
            try:
                contact = ContactMessage.objects.create(
                    user=request.user,
                    name=name,
                    email=email,
                    phone=phone,
                    subject=subject,
                    message=message
                )

                send_mail(
                    f'New Contact Message: {subject}',
                    f'''From: {name} <{email}>
Phone: {phone}
User: {request.user.username}

Message:
{message}''',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                form_data = {}
            
            except Exception as e:
                errors['database'] = "Failed to save your message. Please try again."
        
        context = {
            'locations': locations,
            'page_title': 'Our Branches Across Tamil Nadu',
            'errors': errors,
            'form_data': form_data
        }
        return render(request, 'bakery/contact.html', context)

    context = {
        'locations': locations,
        'page_title': 'Our Branches Across Tamil Nadu'
    }
    return render(request, 'bakery/contact.html', context)

from django.db.models import Q

@login_required(login_url='login')
def search_products(request):
    query = request.GET.get('q', '').strip() 
    products = []
    categories = []

    if query:
        products = Product.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category')

        categories = ProductCategory.objects.filter(products__in=products).distinct()
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user,
            product__in=products
        ).values_list('product_id', flat=True)
    else:
        wishlist_ids = []

    for product in products:
        product.is_in_wishlist = product.id in wishlist_ids

    return render(request, 'bakery/search_results.html', {
        'query': query,
        'products': products,
        'categories': categories,
    })
