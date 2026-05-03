import sys
import os
sys.path.append(os.getcwd())

from app import app, db, Product

with app.app_context():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    
    # 1. First pass: Separate by parent_id
    parents = []
    variants_map = {}
    for p in all_products:
        if p.parent_id:
            if p.parent_id not in variants_map:
                variants_map[p.parent_id] = []
            variants_map[p.parent_id].append(p)
        else:
            parents.append(p)
            
    # 2. Second pass: Consolidate orphans with exact same name
    final_parents = []
    processed_ids = set()
    name_to_parent = {} # name.lower() -> parent_id
    
    for p in parents:
        if p.id in processed_ids: continue
        
        name_key = p.name.strip().lower()
        if name_key in name_to_parent:
            parent_id = name_to_parent[name_key]
            if parent_id not in variants_map: variants_map[parent_id] = []
            variants_map[parent_id].append(p)
            processed_ids.add(p.id)
        else:
            final_parents.append(p)
            name_to_parent[name_key] = p.id
            processed_ids.add(p.id)
            
    print(f"Total Parents: {len(final_parents)}")
    pout_parents = [p for p in final_parents if 'Super Pout' in p.name]
    print(f"Super Pout Parents: {len(pout_parents)}")
    for pp in pout_parents:
        vs = variants_map.get(pp.id, [])
        print(f"  Parent: {pp.name} (ID: {pp.id}, Code: {pp.code}) - Variants: {len(vs)}")
        for v in vs:
            print(f"    - Variant: {v.name} (ID: {v.id}, Code: {v.code})")
