
css_to_append = """
/* ---------- Empty State Styles ---------- */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    background: var(--color-white);
    border-radius: var(--radius-lg);
    border: 1px dashed var(--color-border);
    margin: 40px 0;
}

.empty-state-icon {
    font-size: 64px;
    margin-bottom: 24px;
    opacity: 0.5;
}

.empty-state h3 {
    font-size: 24px;
    margin-bottom: 12px;
}

.empty-state p {
    color: var(--color-text-muted);
    margin-bottom: 32px;
}
"""

with open(r"c:\Users\nilad\OneDrive\Desktop\Oriflame\static\css\main.css", "a", encoding="utf-8") as f:
    f.write(css_to_append)
print("Empty state CSS appended successfully!")
