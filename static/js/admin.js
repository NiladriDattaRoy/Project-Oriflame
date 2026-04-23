/**
 * Oriflame E-Commerce — Admin Panel JavaScript
 * Handles admin CRUD operations, modals, and dashboard analytics.
 */

document.addEventListener('DOMContentLoaded', () => {
  initAdminModals();
  initAdminTables();
  initAdminCharts();
  initAdminSidebar();
});

/* ==================== ADMIN SIDEBAR ==================== */
function initAdminSidebar() {
  const toggle = document.querySelector('#admin-sidebar-toggle');
  const sidebar = document.querySelector('.admin-sidebar');
  
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
}

/* ==================== ADMIN MODALS ==================== */
function initAdminModals() {
  // Open modal buttons
  document.querySelectorAll('[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.dataset.modal;
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add('active');
        
        // If edit, populate form
        if (btn.dataset.id) {
          populateForm(modal, btn.dataset);
        }
      }
    });
  });
  
  // Close modal
  document.querySelectorAll('.admin-modal-close, .admin-modal-overlay').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target === el) {
        el.closest('.admin-modal-overlay').classList.remove('active');
      }
    });
  });
}

function populateForm(modal, data) {
  Object.keys(data).forEach(key => {
    if (key === 'modal' || key === 'id') return;
    // Convert camelCase to snake_case for input names (e.g. categoryId -> category_id)
    const nameAttr = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    const input = modal.querySelector(`[name="${nameAttr}"]`);
    if (input) {
      input.value = data[key];
    }
  });
  
  const idInput = modal.querySelector('[name="id"]');
  if (idInput) idInput.value = data.id;

  // Special handling for color picker sync
  if (data.shadeColor) {
    const picker = modal.querySelector('#shade-color-picker');
    if (picker) picker.value = data.shadeColor;
  }
}

/* ==================== ADMIN CRUD ==================== */
async function adminSaveProduct(form) {
  const formData = new FormData(form);
  const id = formData.get('id');
  const url = id ? `/oriflame-admin-panel-x9k2/products/${id}` : '/oriflame-admin-panel-x9k2/products';
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (data.success) {
      showToast(data.message || 'Product saved!', 'success');
      
      if (form.dataset.stayOpen === 'true') {
        form.dataset.stayOpen = 'false';
        // Clear only id and code, keep the rest for variants
        form.querySelector('[name="id"]').value = '';
        form.querySelector('[name="code"]').value = '';
        form.querySelector('[name="code"]').focus();
        showToast('Now enter the code for the next variant.', 'info');
      } else {
        setTimeout(() => location.reload(), 1000);
      }
    } else {
      showToast(data.message || 'Failed to save product', 'error');
    }
  } catch (err) {
    showToast('Something went wrong', 'error');
  }
}

async function adminDeleteProduct(id) {
  if (!confirm('Are you sure you want to delete this product?')) return;
  
  try {
    const response = await fetch(`/oriflame-admin-panel-x9k2/products/${id}/delete`, {
      method: 'POST'
    });
    
    const data = await response.json();
    
    if (data.success) {
      showToast('Product deleted!', 'success');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.message || 'Failed to delete', 'error');
    }
  } catch (err) {
    showToast('Something went wrong', 'error');
  }
}

async function adminUpdateOrderStatus(orderId, status) {
  try {
    const response = await fetch(`/oriflame-admin-panel-x9k2/orders/${orderId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showToast(`Order status updated to ${status}!`, 'success');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.message || 'Failed to update', 'error');
    }
  } catch (err) {
    showToast('Something went wrong', 'error');
  }
}

async function adminUpdateUserRole(userId, role) {
  try {
    const response = await fetch(`/oriflame-admin-panel-x9k2/users/${userId}/role`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role })
    });
    
    const data = await response.json();
    
    if (data.success) {
      showToast(`User role updated to ${role}!`, 'success');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.message || 'Failed to update', 'error');
    }
  } catch (err) {
    showToast('Something went wrong', 'error');
  }
}

async function adminToggleUser(userId) {
  try {
    const response = await fetch(`/oriflame-admin-panel-x9k2/users/${userId}/toggle`, {
      method: 'POST'
    });
    
    const data = await response.json();
    
    if (data.success) {
      showToast(data.message, 'success');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.message || 'Failed to update', 'error');
    }
  } catch (err) {
    showToast('Something went wrong', 'error');
  }
}

/* ==================== ADMIN TABLES ==================== */
function initAdminTables() {
  // Search filtering
  const searchInput = document.querySelector('.admin-search input');
  if (searchInput) {
    searchInput.addEventListener('input', debounce((e) => {
      const query = e.target.value.toLowerCase();
      const rows = document.querySelectorAll('.admin-table tbody tr');
      
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    }, 300));
  }
}

/* ==================== ADMIN CHARTS ==================== */
function initAdminCharts() {
  const chartContainer = document.querySelector('.admin-chart-bars');
  if (!chartContainer) return;
  
  // Simple bar chart
  const data = [65, 45, 80, 55, 90, 70, 85, 60, 75, 50, 95, 68];
  const maxVal = Math.max(...data);
  
  chartContainer.innerHTML = data.map((val, i) => `
    <div class="admin-chart-bar" style="height: ${(val / maxVal) * 100}%;" title="Month ${i + 1}: ₹${val}K"></div>
  `).join('');
}
