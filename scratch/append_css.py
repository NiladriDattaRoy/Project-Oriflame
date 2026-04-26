
css_to_append = """
/* ---------- Orders & Status Styles ---------- */
.status-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: var(--radius-full);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.status-pending { background: var(--color-warning-bg); color: var(--color-warning); }
.status-confirmed { background: var(--color-info-bg); color: var(--color-info); }
.status-shipped { background: var(--color-primary-dark); color: var(--color-white); }
.status-delivered { background: var(--color-success-bg); color: var(--color-success); }
.status-cancelled { background: var(--color-danger-bg); color: var(--color-danger); }
.status-paid { background: var(--color-success-bg); color: var(--color-success); }
.status-refunded { background: var(--color-danger-bg); color: var(--color-danger); }

.checkout-section {
    background: var(--color-white);
    border-radius: var(--radius-lg);
    padding: var(--space-xl);
    border: 1px solid var(--color-border-light);
    margin-bottom: var(--space-xl);
    box-shadow: var(--shadow-sm);
}

.order-status-steps {
    display: flex;
    justify-content: space-between;
    margin: var(--space-xl) 0 var(--space-2xl);
    position: relative;
    padding: 0 10px;
}

.order-status-steps::before {
    content: '';
    position: absolute;
    top: 20px;
    left: 40px;
    right: 40px;
    height: 2px;
    background: var(--color-border-light);
    z-index: 1;
}

.order-step {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    width: 80px;
}

.order-step-dot {
    width: 40px;
    height: 40px;
    background: var(--color-white);
    border: 2px solid var(--color-border-light);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    transition: all var(--transition-base);
}

.order-step.completed .order-step-dot {
    background: var(--color-success);
    border-color: var(--color-success);
    color: var(--color-white);
}

.order-step.active .order-step-dot {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 4px var(--color-accent-glow);
}

.order-step-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-text-muted);
}

.order-step.completed .order-step-label,
.order-step.active .order-step-label {
    color: var(--color-text);
}

.breadcrumb {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--color-text-muted);
    margin-bottom: var(--space-xl);
}

.breadcrumb a {
    color: var(--color-text-muted);
}

.breadcrumb .separator {
    color: var(--color-border);
}
"""

with open(r"c:\Users\nilad\OneDrive\Desktop\Oriflame\static\css\main.css", "a", encoding="utf-8") as f:
    f.write(css_to_append)
print("CSS appended successfully!")
