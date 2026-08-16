document.addEventListener('DOMContentLoaded', () => {
  // Use Event Delegation to prevent double-binding
  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('.add-to-cart-form');
    if (!form) return;

    e.preventDefault();

    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value,
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: new FormData(form),
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        // Target the span element in layout.html
        const cartBadge = document.getElementById('cart-count');
        if (cartBadge && data.cart_count !== undefined) {
          cartBadge.textContent = data.cart_count;
        }
      }
    } catch (err) {
      console.error('Error adding to cart:', err);
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  });
});