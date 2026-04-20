/**
 * Oriflame E-Commerce — MLM Network JavaScript
 * Handles network tree visualization and commission display.
 */

document.addEventListener('DOMContentLoaded', () => {
  initMLMTree();
  initCommissionTable();
});

/* ==================== MLM TREE VISUALIZATION ==================== */
function initMLMTree() {
  const treeContainer = document.querySelector('.mlm-tree');
  if (!treeContainer) return;
  
  // Tree is rendered server-side, add interactivity
  const nodes = document.querySelectorAll('.mlm-node-card');
  
  nodes.forEach(node => {
    node.addEventListener('click', () => {
      const userId = node.dataset.userId;
      if (userId) {
        showUserDetails(userId);
      }
    });
  });
}

/* ==================== USER DETAILS POPUP ==================== */
async function showUserDetails(userId) {
  try {
    const response = await fetch(`/mlm/user/${userId}`);
    const data = await response.json();
    
    if (data.success) {
      const user = data.user;
      
      const overlay = document.createElement('div');
      overlay.className = 'modal-overlay active';
      overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
      overlay.innerHTML = `
        <div class="modal">
          <div class="modal-header">
            <h3>${user.name}</h3>
            <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
          </div>
          <div class="modal-body">
            <div style="display: flex; gap: 16px; margin-bottom: 20px;">
              <div style="width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #c9a96e, #b08d4a); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 24px; font-weight: 700;">
                ${user.name.charAt(0)}
              </div>
              <div>
                <h4 style="margin-bottom: 4px;">${user.name}</h4>
                <p style="color: var(--color-text-secondary); font-size: 14px;">${user.email}</p>
                <span class="status-badge status-${user.role === 'partner' ? 'delivered' : 'confirmed'}" style="margin-top: 4px;">
                  ${user.role}
                </span>
              </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
              <div class="stat-card" style="padding: 16px;">
                <div class="stat-card-value" style="font-size: 20px;">${formatCurrency(user.total_sales || 0)}</div>
                <div class="stat-card-label">Total Sales</div>
              </div>
              <div class="stat-card" style="padding: 16px;">
                <div class="stat-card-value" style="font-size: 20px;">${formatCurrency(user.total_commission || 0)}</div>
                <div class="stat-card-label">Commission Earned</div>
              </div>
              <div class="stat-card" style="padding: 16px;">
                <div class="stat-card-value" style="font-size: 20px;">${user.downline_count || 0}</div>
                <div class="stat-card-label">Direct Downlines</div>
              </div>
              <div class="stat-card" style="padding: 16px;">
                <div class="stat-card-value" style="font-size: 20px;">${user.join_date || 'N/A'}</div>
                <div class="stat-card-label">Joined</div>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
    }
  } catch (err) {
    showToast('Failed to load user details', 'error');
  }
}

/* ==================== COMMISSION TABLE ==================== */
function initCommissionTable() {
  const filterBtns = document.querySelectorAll('.commission-filter');
  
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      const level = btn.dataset.level;
      const rows = document.querySelectorAll('.commission-row');
      
      rows.forEach(row => {
        if (level === 'all' || row.dataset.level === level) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  });
}
