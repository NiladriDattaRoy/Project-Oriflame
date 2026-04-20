/**
 * Oriflame E-Commerce — Checkout JavaScript
 * Payment methods, Razorpay (UPI / cards) hosted checkout, COD / wallet simulation.
 */

document.addEventListener('DOMContentLoaded', () => {
  initPaymentMethods();
  initCheckoutForm();
  initAddressForm();
});

function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) {
      resolve();
      return;
    }
    const s = document.createElement('script');
    s.src = 'https://checkout.razorpay.com/v1/checkout.js';
    s.onload = () => resolve();
    s.onerror = () => reject(new Error('Could not load Razorpay checkout script'));
    document.body.appendChild(s);
  });
}

/* ==================== PAYMENT METHOD SELECTION ==================== */
function initPaymentMethods() {
  const methods = document.querySelectorAll('.payment-method');

  methods.forEach((method) => {
    method.addEventListener('click', () => {
      methods.forEach((m) => m.classList.remove('selected'));
      method.classList.add('selected');

      const radio = method.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;

      const allDetails = document.querySelectorAll('.payment-details');
      allDetails.forEach((d) => {
        d.style.display = 'none';
      });

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
    const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML =
        '<span class="spinner" style="width:20px;height:20px;border-width:2px;"></span> Processing...';
    }

    try {
      const formData = new FormData(form);
      const response = await fetch('/checkout', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        showToast(data.message || 'Checkout failed', 'error');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalBtnHtml;
        }
        return;
      }

      if (data.razorpay) {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalBtnHtml;
        }
        await openRazorpayCheckout(data, form);
      } else {
        showPaymentProcessing(data, submitBtn, originalBtnHtml);
      }
    } catch (err) {
      showToast('Something went wrong. Please try again.', 'error');
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnHtml;
      }
    }
  });
}

async function openRazorpayCheckout(data, form) {
  try {
    await loadRazorpayScript();
  } catch {
    showToast('Could not load payment gateway. Check your network.', 'error');
    return;
  }

  const name = form.querySelector('[name="shipping_name"]')?.value?.trim() || '';
  const phone = form.querySelector('[name="shipping_phone"]')?.value?.trim() || '';
  const email = form.dataset.userEmail || '';

  const options = {
    key: data.razorpay.key_id,
    amount: String(data.razorpay.amount),
    currency: data.razorpay.currency || 'INR',
    order_id: data.razorpay.order_id,
    name: 'Oriflame Store',
    description: `Order ${data.order_number}`,
    image: '/static/images/placeholder.png',
    prefill: {
      name,
      email,
      contact: phone.replace(/\D/g, '').slice(-10),
    },
    theme: { color: '#e4002b' },
    modal: {
      ondismiss() {
        showToast('Payment window closed. Your order is saved — complete payment from order history when ready.', 'info');
      },
    },
    handler(response) {
      verifyRazorpayPayment(data, response);
    },
  };

  const rzp = new window.Razorpay(options);
  rzp.open();
}

async function verifyRazorpayPayment(orderData, rpResponse) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  overlay.innerHTML = `
    <div class="modal" style="text-align:center; padding: 48px;">
      <div class="spinner" style="margin: 0 auto 24px;"></div>
      <h3 style="margin-bottom: 8px;">Verifying payment</h3>
      <p style="color: var(--color-text-secondary);">Please wait…</p>
    </div>
  `;
  document.body.appendChild(overlay);

  try {
    const res = await fetch('/payment/razorpay/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        order_id: orderData.order_id,
        razorpay_order_id: rpResponse.razorpay_order_id,
        razorpay_payment_id: rpResponse.razorpay_payment_id,
        razorpay_signature: rpResponse.razorpay_signature,
      }),
    });
    const result = await res.json();

    if (result.success) {
      overlay.querySelector('.modal').innerHTML = `
        <h3 style="color: var(--color-success); margin-bottom: 8px;">Payment successful</h3>
        <p style="color: var(--color-text-secondary); margin-bottom: 8px;">Order #${result.order_number}</p>
        <p style="color: var(--color-text-secondary); margin-bottom: 24px;">Payment ID: ${result.transaction_ref}</p>
        <a href="/orders" class="btn btn-primary">View orders</a>
      `;
    } else {
      overlay.querySelector('.modal').innerHTML = `
        <h3 style="color: var(--color-danger); margin-bottom: 8px;">Payment verification failed</h3>
        <p style="color: var(--color-text-secondary); margin-bottom: 24px;">${result.message || 'Please contact support if money was debited.'}</p>
        <button type="button" class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">Close</button>
      `;
    }
  } catch {
    overlay.remove();
    showToast('Verification request failed', 'error');
  }
}

/* ==================== FORM VALIDATION ==================== */
function validateCheckoutForm(form) {
  const required = form.querySelectorAll('[required]');
  let valid = true;

  required.forEach((field) => {
    const group = field.closest('.form-group');
    const error = group ? group.querySelector('.form-error') : null;

    if (!field.value.trim()) {
      field.style.borderColor = '#e4002b';
      if (error) error.textContent = 'This field is required';
      valid = false;
    } else {
      field.style.borderColor = '';
      if (error) error.textContent = '';
    }
  });

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

/* ==================== PAYMENT PROCESSING (COD / wallet) ==================== */
function showPaymentProcessing(data, submitBtn, originalBtnHtml) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  overlay.innerHTML = `
    <div class="modal" style="text-align:center; padding: 48px;">
      <div class="spinner" style="margin: 0 auto 24px;"></div>
      <h3 style="margin-bottom: 8px;">Processing payment</h3>
      <p style="color: var(--color-text-secondary);">Please wait…</p>
    </div>
  `;
  document.body.appendChild(overlay);

  setTimeout(() => {
    processSimulatedPayment(data, overlay, submitBtn, originalBtnHtml);
  }, 1200);
}

async function processSimulatedPayment(orderData, overlay, submitBtn, originalBtnHtml) {
  try {
    const response = await fetch('/payment/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderData.order_id }),
    });

    const data = await response.json();

    if (data.success) {
      overlay.querySelector('.modal').innerHTML = `
        <h3 style="color: var(--color-success); margin-bottom: 8px;">Order confirmed</h3>
        <p style="color: var(--color-text-secondary); margin-bottom: 8px;">Order #${data.order_number}</p>
        <p style="color: var(--color-text-secondary); margin-bottom: 24px;">Reference: ${data.transaction_ref}</p>
        <a href="/orders" class="btn btn-primary">View orders</a>
      `;
    } else {
      overlay.querySelector('.modal').innerHTML = `
        <h3 style="color: var(--color-danger); margin-bottom: 8px;">Could not complete payment</h3>
        <p style="color: var(--color-text-secondary); margin-bottom: 24px;">${data.message || 'Please try again'}</p>
        <button type="button" class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">Close</button>
      `;
    }
  } catch {
    overlay.remove();
    showToast('Payment processing failed', 'error');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHtml || 'Place order';
    }
  }
}

/* ==================== ADDRESS FORM ==================== */
function initAddressForm() {
  const savedAddresses = document.querySelectorAll('.saved-address');

  savedAddresses.forEach((addr) => {
    addr.addEventListener('click', () => {
      savedAddresses.forEach((a) => a.classList.remove('selected'));
      addr.classList.add('selected');

      const radio = addr.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;

      const raw = addr.dataset.address || '{}';
      let data;
      try {
        data = JSON.parse(raw);
      } catch {
        data = {};
      }
      fillAddressFields(data);
    });
  });
}

function fillAddressFields(data) {
  const fields = [
    'shipping_name',
    'shipping_phone',
    'shipping_address',
    'shipping_city',
    'shipping_state',
    'shipping_pincode',
  ];
  fields.forEach((field) => {
    const input = document.querySelector(`[name="${field}"]`);
    if (input && data[field]) {
      input.value = data[field];
    }
  });
}
