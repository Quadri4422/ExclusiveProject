# mainsite/context_processors.py

def global_counts(request):
    """Calculates total cart quantity and wishlist count globally for all templates."""
    
    # 1. Calculate total items in the session cart (sum of quantities)
    session_cart = request.session.get('cart', {})
    total_cart_count = 0
    if isinstance(session_cart, dict):
        for qty in session_cart.values():
            try:
                total_cart_count += int(qty)
            except (ValueError, TypeError):
                continue

    # 2. Calculate total items in the session wishlist
    session_wishlist = request.session.get('wishlist', [])
    if isinstance(session_wishlist, list):
        total_wishlist_count = len(session_wishlist)
    else:
        total_wishlist_count = 0

    return {
        'global_cart_count': total_cart_count,
        'global_wishlist_count': total_wishlist_count,
    }