from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.apps import apps
from decimal import Decimal
from .models import Cart, CartItem

@login_required
def cart_detail(request):
    """Display cart contents page"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    
    # Calculate totals
    subtotal = cart.get_total_price()
    total_items = cart.get_total_items()
    
    # Check for applied coupon in session
    applied_coupon = request.session.get('applied_coupon', None)
    discount_amount = Decimal('0.00')
    final_total = subtotal
    
    if applied_coupon:
        # Calculate discount if coupon is applied
        discount_percentage = Decimal(str(applied_coupon.get('discount', 0)))
        discount_amount = (subtotal * discount_percentage / 100).quantize(Decimal('0.01'))
        final_total = subtotal - discount_amount
    
    # Check stock status for each item
    stock_warnings = []
    can_checkout = True
    
    # Enhance items with stock information if decor app is available
    enhanced_items = []
    for item in items:
        item_data = {
            'item': item,
            'stock_info': None
        }
        
        # Try to get stock info from decor app
        if apps.is_installed('decor'):
            try:
                from decor.models import DecorItemsModel
                decor_item = DecorItemsModel.objects.filter(
                    item_name=item.product_name
                ).first()
                
                if decor_item:
                    available_stock = decor_item.stock_quantity
                    item_data['stock_info'] = {
                        'available': available_stock,
                        'status': 'in_stock' if available_stock >= item.quantity else 'out_of_stock'
                    }
                    
                    if available_stock < item.quantity:
                        stock_warnings.append(f"{item.product_name}: Only {available_stock} available, you have {item.quantity} in cart")
                        can_checkout = False
                    elif available_stock < 10:
                        item_data['stock_info']['status'] = 'low_stock'
            except:
                pass
        
        enhanced_items.append(item_data)
    
    context = {
        'cart': cart,
        'items': items,
        'enhanced_items': enhanced_items,
        'subtotal': subtotal,
        'total_items': total_items,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'applied_coupon': applied_coupon,
        'stock_warnings': stock_warnings,
        'can_checkout': can_checkout,
    }
    
    return render(request, 'cart/cart_detail.html', context)

@login_required
@require_POST
def add_to_cart(request):
    """Add products to cart via POST request"""
    # Extract product data from POST
    product_name = request.POST.get('product_name')
    product_price = request.POST.get('product_price')
    product_image = request.POST.get('product_image', '')
    quantity = request.POST.get('quantity', '1')
    
    # Validate data
    if not product_name or not product_price:
        messages.error(request, 'Invalid product data.')
        return redirect(request.META.get('HTTP_REFERER', 'decor:home'))
    
    try:
        price = Decimal(product_price)
        qty = int(quantity)
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        messages.error(request, 'Invalid price or quantity.')
        return redirect(request.META.get('HTTP_REFERER', 'decor:home'))
    
    # Check stock availability if decor app is installed
    if apps.is_installed('decor'):
        try:
            from decor.models import DecorItemsModel
            decor_item = DecorItemsModel.objects.filter(item_name=product_name).first()
            if decor_item and decor_item.stock_quantity < qty:
                messages.error(request, f'Only {decor_item.stock_quantity} units of {product_name} are available.')
                return redirect(request.META.get('HTTP_REFERER', 'decor:home'))
        except:
            pass
    
    # Get or create user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Add or update cart item
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product_name=product_name,
        defaults={
            'product_price': price,
            'product_image': product_image,
            'quantity': qty
        }
    )
    
    if not item_created:
        # Item already exists, update quantity
        new_quantity = cart_item.quantity + qty
        
        # Check total quantity against stock
        if apps.is_installed('decor'):
            try:
                from decor.models import DecorItemsModel
                decor_item = DecorItemsModel.objects.filter(item_name=product_name).first()
                if decor_item and decor_item.stock_quantity < new_quantity:
                    messages.error(request, f'Cannot add more. Only {decor_item.stock_quantity} units available.')
                    return redirect(request.META.get('HTTP_REFERER', 'decor:home'))
            except:
                pass
        
        cart_item.quantity = new_quantity
        cart_item.product_price = price  # Update price in case it changed
        cart_item.product_image = product_image
        cart_item.save()
        messages.success(request, f'Updated {product_name} quantity in your cart.')
    else:
        messages.success(request, f'Added {product_name} to your cart.')
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Added {product_name} to cart',
            'cart_count': cart.get_total_items()
        })
    
    return redirect('cart:detail')

@login_required
@require_POST
def update_cart(request, item_id):
    """Modify quantity of existing cart items"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    quantity = request.POST.get('quantity', '1')
    
    try:
        qty = int(quantity)
        if qty <= 0:
            cart_item.delete()
            messages.success(request, f'Removed {cart_item.product_name} from your cart.')
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                cart = Cart.objects.get(user=request.user)
                return JsonResponse({
                    'success': True,
                    'removed': True,
                    'message': f'Removed {cart_item.product_name}',
                    'cart_subtotal': str(cart.get_total_price()),
                    'cart_count': cart.get_total_items()
                })
        else:
            # Check stock availability if decor app is installed
            if apps.is_installed('decor'):
                try:
                    from decor.models import DecorItemsModel
                    decor_item = DecorItemsModel.objects.filter(
                        item_name=cart_item.product_name
                    ).first()
                    if decor_item and decor_item.stock_quantity < qty:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'error': f'Only {decor_item.stock_quantity} units available'
                            })
                        else:
                            messages.error(request, f'Only {decor_item.stock_quantity} units available.')
                            return redirect('cart:detail')
                except:
                    pass
            
            cart_item.quantity = qty
            cart_item.save()
            messages.success(request, f'Updated {cart_item.product_name} quantity.')
    except ValueError:
        messages.error(request, 'Invalid quantity.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Invalid quantity'
            })
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'item_total': str(cart_item.get_total_price()),
            'cart_subtotal': str(cart.get_total_price()),
            'cart_count': cart.get_total_items()
        })
    
    return redirect('cart:detail')

@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Delete specific item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product_name
    cart_item.delete()
    
    messages.success(request, f'Removed {product_name} from your cart.')
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = Cart.objects.get(user=request.user)
        return JsonResponse({
            'success': True,
            'message': f'Removed {product_name}',
            'cart_subtotal': str(cart.get_total_price()),
            'cart_count': cart.get_total_items()
        })
    
    return redirect('cart:detail')

@login_required
@require_POST
def clear_cart(request):
    """Empty entire cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart.clear()
        messages.success(request, 'Your cart has been cleared.')
    except Cart.DoesNotExist:
        messages.info(request, 'Your cart is already empty.')
    
    return redirect('cart:detail')