/**
 * Oriflame E-Commerce — Main JavaScript
 * Handles navigation, hero carousel, scroll animations, search, and toasts.
 */

document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initHeroCarousel();
  initScrollAnimations();
  initProductTabs();
  initMobileNav();
  initSearch();
});

/* ==================== HEADER ==================== */
function initHeader() {
  const header = document.querySelector('.header');
  if (!header) return;
  
  let lastScrollY = 0;
  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    if (scrollY > 50) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
    lastScrollY = scrollY;
  });
}

/* ==================== HERO CAROUSEL ==================== */
function initHeroCarousel() {
  const slides = document.querySelectorAll('.hero-slide');
  const dots = document.querySelectorAll('.hero-dot');
  const prevBtn = document.querySelector('.hero-nav.prev');
  const nextBtn = document.querySelector('.hero-nav.next');
  
  if (slides.length === 0) return;
  
  let currentSlide = 0;
  let interval;
  
  function showSlide(index) {
    slides.forEach(s => s.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    
    currentSlide = (index + slides.length) % slides.length;
    slides[currentSlide].classList.add('active');
    if (dots[currentSlide]) dots[currentSlide].classList.add('active');
  }
  
  function nextSlide() {
    showSlide(currentSlide + 1);
  }
  
  function prevSlide() {
    showSlide(currentSlide - 1);
  }
  
  function startAutoplay() {
    interval = setInterval(nextSlide, 5000);
  }
  
  function stopAutoplay() {
    clearInterval(interval);
  }
  
  if (nextBtn) nextBtn.addEventListener('click', () => { stopAutoplay(); nextSlide(); startAutoplay(); });
  if (prevBtn) prevBtn.addEventListener('click', () => { stopAutoplay(); prevSlide(); startAutoplay(); });
  
  dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
      stopAutoplay();
      showSlide(index);
      startAutoplay();
    });
  });
  
  startAutoplay();
}

/* ==================== SCROLL ANIMATIONS ==================== */
function initScrollAnimations() {
  const elements = document.querySelectorAll('.fade-in, .slide-in-left, .scale-in');
  if (elements.length === 0) return;
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  });
  
  elements.forEach(el => observer.observe(el));
}

/* ==================== PRODUCT TABS ==================== */
function initProductTabs() {
  const tabs = document.querySelectorAll('.product-tab');
  const tabContents = document.querySelectorAll('.tab-content');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      tabContents.forEach(content => {
        content.style.display = content.dataset.tab === target ? 'block' : 'none';
      });
    });
  });
}

/* ==================== MOBILE NAV ==================== */
function initMobileNav() {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav-main');
  
  if (!toggle || !nav) return;
  
  toggle.addEventListener('click', () => {
    nav.classList.toggle('open');
    toggle.classList.toggle('active');
  });
  
  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!toggle.contains(e.target) && !nav.contains(e.target)) {
      nav.classList.remove('open');
      toggle.classList.remove('active');
    }
  });
}

/* ==================== SEARCH ==================== */
function initSearch() {
  const searchForm = document.querySelector('.search-bar');
  if (!searchForm) return;
  
  const input = searchForm.querySelector('input');
  
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (query) {
      window.location.href = `/products?search=${encodeURIComponent(query)}`;
    }
  });
}

/* ==================== TOAST NOTIFICATIONS ==================== */
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${icons[type] || icons.info}</div>
    <span class="toast-message">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;
  
  container.appendChild(toast);
  
  // Auto-remove after 4 seconds
  setTimeout(() => {
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/* ==================== UTILITIES ==================== */
function formatCurrency(amount) {
  return '₹' + Number(amount).toLocaleString('en-IN');
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
