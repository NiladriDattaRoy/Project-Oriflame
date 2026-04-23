/**
 * Oriflame E-Commerce — Cart JavaScript
 * Handles add-to-cart, sidebar cart, quantity updates, and cart removal.
 */

document.addEventListener('DOMContentLoaded', () => {
  initCartSidebar();
  initAddToCartButtons();
});

/* ==================== CART SIDEBAR ==================== */
function initCartSidebar() {
  const cartBtn = document.querySelector('#cart-toggle');
  const sidebar = document.querySelector('.cart-sidebar');
  const overlay = document.querySelector('.cart-sidebar-overlay');
  const closeBtn = document.querySelector('#cart-close');
  
  if (!cartBtn || !sidebar) return;
  
  cartBtn.addEventListener('click', (e) => {
    e.preventDefault();
    openCart();
  });
  
  if (closeBtn) closeBtn.addEventListener('click', closeCart);
  if (overlay) overlay.addEventListener('click', closeCart);
}

function openCart() {
  const sidebar = document.querySelector('.cart-sidebar');
  const overlay = document.querySelector('.cart-sidebar-overlay');
  if (sidebar) sidebar.classList.add('open');
  if (overlay) overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
  loadCartItems();
}

function closeCart() {
  const sidebar = document.querySelector('.cart-sidebar');
  const overlay = document.querySelector('.cart-sidebar-overlay');
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) overlay.classList.remove('active');
  document.body.style.overflow = '';
}

/* ==================== ADD TO CART ==================== */
function initAddToCartButtons() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-add-cart, .add-to-cart-btn');
    if (!btn) return;
    
    e.preventDefault();
    const productId = btn.dataset.productId;
    const qty = btn.dataset.qty || 1;
    
    if (productId) {
      addToCart(productId, qty);
    }
  });
}

async function addToCart(productId, quantity = 1) {
  try {
    const response = await fetch('/cart/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ product_id: productId, quantity: parseInt(quantity) })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showToast(data.message || 'Added to cart!', 'success');
      updateCartBadge(data.cart_count);
      loadCartItems();
    } else {
      if (data.redirect) {
        window.location.href = data.redirect;
        return;
      }
      showToast(data.message || 'Failed to add to cart', 'error');
    }
  } catch (err) {
    showToast('Something went wrong', 'error');
    console.error('Add to cart error:', err);
  }
}

/* ==================== LOAD CART ITEMS ==================== */
async function loadCartItems() {
  const container = document.querySelector('.cart-sidebar-items');
  const subtotalEl = document.querySelector('#cart-subtotal');
  const totalEl = document.querySelector('#cart-total');
  const countEl = document.querySelector('#cart-sidebar-count');
  
  if (!container) return;
  
  try {
    const response = await fetch('/cart/items');
    const data = await response.json();
    
    if (data.items && data.items.length > 0) {
      container.innerHTML = data.items.map(item => `
        <div class="cart-item" data-item-id="${item.id}">
          <div class="cart-item-image">
            <img src="${item.image || '/static/images/placeholder.png'}" alt="${item.name}">
          </div>
          <div class="cart-item-info">
            <div class="cart-item-name">${item.name}</div>
            <div class="cart-item-price">${formatCurrency(item.price)}</div>
            <div class="cart-item-qty">
              <button class="qty-btn" onclick="updateCartQty(${item.id}, ${item.quantity - 1})">−</button>
              <span>${item.quantity}</span>
              <button class="qty-btn" onclick="updateCartQty(${item.id}, ${item.quantity + 1})">+</button>
            </div>
          </div>
          <button class="cart-item-remove" onclick="removeCartItem(${item.id})" style="font-size: 9px; letter-spacing: 1px; font-weight: 700; background: transparent; border: none; text-transform: uppercase;">Remove</button>
        </div>
      `).join('');
      
      if (subtotalEl) subtotalEl.textContent = formatCurrency(data.total);
      if (totalEl) totalEl.textContent = formatCurrency(data.total);
      if (countEl) countEl.textContent = `${data.count} item${data.count !== 1 ? 's' : ''}`;
    } else {
      container.innerHTML = `
        <div class="empty-state" style="padding: 48px 16px;">
          <div class="empty-state-icon" style="font-size: 14px; margin-bottom: 8px; font-weight: 700;">EMPTY</div>
          <h3 style="font-size: 16px;">Your cart is empty</h3>
          <p style="font-size: 13px;">Add some products to get started!</p>
        </div>
      `;
      if (subtotalEl) subtotalEl.textContent = '₹0';
      if (totalEl) totalEl.textContent = '₹0';
      if (countEl) countEl.textContent = '0 items';
    }
    
    updateCartBadge(data.count || 0);
  } catch (err) {
    console.error('Load cart error:', err);
  }
}

/* ==================== UPDATE CART QUANTITY ==================== */
async function updateCartQty(itemId, newQty) {
  if (newQty < 1) {
    removeCartItem(itemId);
    return;
  }
  
  try {
    const response = await fetch('/cart/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId, quantity: newQty })
    });
    
    const data = await response.json();
    
    if (data.success) {
      loadCartItems();
    } else {
      showToast(data.message || 'Failed to update', 'error');
    }
  } catch (err) {
    showToast('Something went wrong', 'error');
  }
}

/* ==================== REMOVE CART ITEM ==================== */
async function removeCartItem(itemId) {
  try {
    const response = await fetch('/cart/remove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showToast('Item removed from cart', 'success');
      loadCartItems();
    } else {
      showToast(data.message || 'Failed to remove', 'error');
    }
  } catch (err) {
    showToast('Something went wrong', 'error');
  }
}

/* ==================== UPDATE CART BADGE ==================== */
function updateCartBadge(count) {
  const badges = document.querySelectorAll('.cart-badge');
  badges.forEach(badge => {
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  });
}
