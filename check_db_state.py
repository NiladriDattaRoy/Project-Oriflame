from app import app
from models import Transaction, Order, User

with app.app_context():
    print("--- Transactions ---")
    for t in Transaction.query.all():
        print(f"Ref: {t.transaction_ref}, Status: {t.status}, Amount: {t.amount}, Order ID: {t.order_id}")
    
    print("\n--- Orders ---")
    for o in Order.query.all():
        print(f"Number: {o.order_number}, Status: {o.status}, Payment Status: {o.payment_status}, Total: {o.total}")
    
    print("\n--- Users Sales ---")
    for u in User.query.filter(User.total_sales > 0).all():
        print(f"Email: {u.email}, Total Sales: {u.total_sales}")
