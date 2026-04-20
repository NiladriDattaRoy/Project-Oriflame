/**
 * Oriflame E-Commerce — Checkout JavaScript
 * Handles payment method selection, form validation, and order processing.
 */

document.addEventListener('DOMContentLoaded', () => {
  initPaymentMethods();
  initCheckoutForm();
  initAddressForm();
});

/* ==================== PAYMENT METHOD SELECTION ==================== */
function initPaymentMethods() {
  const methods = document.querySelectorAll('.payment-method');
  
  methods.forEach(method => {
    method.addEventListener('click', () => {
      methods.forEach(m => m.classList.remove('selected'));
      method.classList.add('selected');
      
      const radio = method.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      
      // Show/hide payment details
      const allDetails = document.querySelectorAll('.payment-details');
      allDetails.forEach(d => d.style.display = 'none');
      
      const detailId = method.dataset.details;
      if (detailId) {
        const detail = document.getElementById(detailId);
        if (detail) detail.style.display = 'block';
      }
    });
  });
}

/* ==================== CHECKOUT FORM ==================== */
function initCheckoutForm() {
  const form = document.getElementById('checkout-form');
  if (!form) return;
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!validateCheckoutForm(form)) return;
    
    const submitBtn = form.querySelector('.btn-place-order');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner" style="width:20px;height:20px;border-width:2px;"></span> Processing...';
    }
    
    try {
      const formData = new FormData(form);
      const response = await fetch('/checkout', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Show payment processing modal
        showPaymentProcessing(data);
      } else {
        showToast(data.message || 'Checkout failed', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = 'Place Order';
        }
      }
    } catch (err) {
      showToast('Something went wrong. Please try again.', 'error');
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Place Order';
      }
    }
  });
}

/* ==================== FORM VALIDATION ==================== */
function validateCheckoutForm(form) {
  const required = form.querySelectorAll('[required]');
  let valid = true;
  
  required.forEach(field => {
    const group = field.closest('.form-group');
    const error = group ? group.querySelector('.form-error') : null;
    
    if (!field.value.trim()) {
      field.style.borderColor = '#e74c3c';
      if (error) error.textContent = 'This field is required';
      valid = false;
    } else {
      field.style.borderColor = '';
      if (error) error.textContent = '';
    }
  });
  
  // Check payment method selected
  const paymentSelected = form.querySelector('input[name="payment_method"]:checked');
  if (!paymentSelected) {
    showToast('Please select a payment method', 'warning');
    valid = false;
  }
  
  if (!valid) {
    showToast('Please fill in all required fields', 'warning');
  }
  
  return valid;
}

/* ==================== PAYMENT PROCESSING ==================== */
function showPaymentProcessing(data) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  overlay.innerHTML = `
    <div class="modal" style="text-align:center; padding: 48px;">
      <div class="spinner" style="margin: 0 auto 24px;"></div>
      <h3 style="margin-bottom: 8px;">Processing Payment</h3>
      <p style="color: var(--color-text-secondary);">Please wait while we process your payment...</p>
    </div>
  `;
  document.body.appendChild(overlay);
  
  // Simulate payment processing
  setTimeout(() => {
    processPayment(data, overlay);
  }, 2000);
}

async function processPayment(orderData, overlay) {
  try {
    const response = await fetch('/payment/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderData.order_id })
    });
    
    const data = await response.json();
    
    if (data.success) {
      overlay.querySelector('.modal').innerHTML = `
        <div style="font-size: 64px; margin-bottom: 16px;">✓</div>
        <h3 style="color: var(--color-success); margin-bottom: 8px;">Payment Successful!</h3>
        <p style="color: var(--color-text-secondary); margin-bottom: 8px;">Order #${data.order_number}</p>
        <p style="color: var(--color-text-secondary); margin-bottom: 24px;">Transaction Ref: ${data.transaction_ref}</p>
        <a href="/orders" class="btn btn-primary">View Orders</a>
      `;
    } else {
      overlay.querySelector('.modal').innerHTML = `
        <div style="font-size: 64px; margin-bottom: 16px;">✕</div>
        <h3 style="color: var(--color-danger); margin-bottom: 8px;">Payment Failed</h3>
        <p style="color: var(--color-text-secondary); margin-bottom: 24px;">${data.message || 'Please try again'}</p>
        <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">Try Again</button>
      `;
    }
  } catch (err) {
    overlay.remove();
    showToast('Payment processing failed', 'error');
  }
}

/* ==================== ADDRESS FORM ==================== */
function initAddressForm() {
  const savedAddresses = document.querySelectorAll('.saved-address');
  
  savedAddresses.forEach(addr => {
    addr.addEventListener('click', () => {
      savedAddresses.forEach(a => a.classList.remove('selected'));
      addr.classList.add('selected');
      
      const radio = addr.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      
      // Fill shipping fields
      const data = JSON.parse(addr.dataset.address || '{}');
      fillAddressFields(data);
    });
  });
}

function fillAddressFields(data) {
  const fields = ['shipping_name', 'shipping_phone', 'shipping_address', 'shipping_city', 'shipping_state', 'shipping_pincode'];
  fields.forEach(field => {
    const input = document.querySelector(`[name="${field}"]`);
    if (input && data[field]) {
      input.value = data[field];
    }
  });
}
