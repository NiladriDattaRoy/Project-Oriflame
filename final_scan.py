
from app import app, db, Product
import re

def check_for_inconsistencies():
    with app.app_context():
        all_products = Product.query.all()
        
        print(f"--- Scanning {len(all_products)} products ---")
        
        fixed_count = 0
        duo_pattern = re.compile(r'\bduo\b', re.IGNORECASE)
        
        for p in all_products:
            # 1. Clear empty strings to None
            if p.shade_color_2 == '':
                print(f"[FIX] Clearing empty shade_color_2 for ID {p.id} ({p.name})")
                p.shade_color_2 = None
                fixed_count += 1
            
            # 2. Check for suspicious #000000 (default black)
            # Only if it's NOT explicitly marked as duo or has 'duo' in name?
            # Actually, let's just report these for now.
            if p.shade_color_2 == '#000000':
                is_likely_duo = duo_pattern.search(p.name) or (p.shade_name and duo_pattern.search(p.shade_name))
                if not is_likely_duo:
                    print(f"[WARN] ID {p.id} ({p.name}) has default black color 2 but name doesn't suggest Duo.")
                else:
                    print(f"[INFO] ID {p.id} ({p.name}) has black color 2 and name suggests Duo. Keeping it.")

            # 3. Check for Duo in name but NO color 2
            if duo_pattern.search(p.name) or (p.shade_name and duo_pattern.search(p.shade_name)):
                if not p.shade_color_2:
                    print(f"[WARN] ID {p.id} ({p.name}) name suggests Duo but shade_color_2 is missing.")

        if fixed_count > 0:
            db.session.commit()
            print(f"\n--- Committed {fixed_count} fixes ---")
        else:
            print("\n--- No automated fixes applied ---")

if __name__ == "__main__":
    check_for_inconsistencies()
