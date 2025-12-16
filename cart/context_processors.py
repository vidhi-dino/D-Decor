"""
Context processors for cart app
"""

def cart_context(request):
    """
    Add cart information to all template contexts
    """
    if request.user.is_authenticated:
        try:
            from .models import Cart
            cart = Cart.objects.get(user=request.user)
            return {
                'cart': cart,
                'cart_item_count': cart.get_total_items(),
                'cart_total': cart.get_total_price(),
            }
        except Cart.DoesNotExist:
            # Create empty cart for user
            cart = Cart.objects.create(user=request.user)
            return {
                'cart': cart,
                'cart_item_count': 0,
                'cart_total': 0,
            }
        except Exception:
            # Return empty cart context if any error occurs
            return {
                'cart': None,
                'cart_item_count': 0,
                'cart_total': 0,
            }
    else:
        # For anonymous users, return empty cart context
        return {
            'cart': None,
            'cart_item_count': 0,
            'cart_total': 0,
        }