from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import text
from models import db, Medicine, Category, Customer, Order

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:mysecretpassword@localhost:5434/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'some_secret_key'
db.init_app(app)

# -----------------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------------

@app.before_request
def require_login():
    allowed_routes = ['login', 'logout']
    if request.endpoint not in allowed_routes and 'role' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Demo hard-coded credentials
        if username == 'root' and password == 'rootp':
            session['role'] = 'root'
            return redirect(url_for('index'))
        elif username == 'test' and password == 'testp':
            session['role'] = 'test'
            return redirect(url_for('test_view'))
        else:
            flash('Wrong username/password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# -----------------------------------------------------------
# ROOT USER ROUTES
# -----------------------------------------------------------

# 1) MEDICINES (INDEX) --------------------------------------

@app.route('/')
def index():
    if session.get('role') != 'root':
        return redirect(url_for('test_view'))
    medicines = Medicine.query.all()
    categories = Category.query.all()
    return render_template('index.html', medicines=medicines, categories=categories)

@app.route('/create_medicine', methods=['POST'])
def create_medicine():
    if session.get('role') != 'root':
        return "Forbidden"
    name = request.form.get('name')
    price = request.form.get('price')
    category_id = request.form.get('category_id')
    quantity = request.form.get('quantity', 0)

    if not name or not price or not category_id:
        flash("Please fill all required fields.")
        return redirect(url_for('index'))

    try:
        new_medicine = Medicine(
            name=name,
            price=price,
            category_id=category_id,
            quantity=quantity
        )
        db.session.add(new_medicine)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating medicine: {e}")
    return redirect(url_for('index'))

@app.route('/update_medicine/<int:medicine_id>', methods=['POST'])
def update_medicine(medicine_id):
    if session.get('role') != 'root':
        return "Forbidden"
    med = Medicine.query.get(medicine_id)
    if med:
        med.name = request.form.get('name', med.name)
        med.price = request.form.get('price', med.price)
        med.category_id = request.form.get('category_id', med.category_id)
        med.quantity = request.form.get('quantity', med.quantity)
        db.session.commit()
        flash(f"Medicine #{med.id} updated successfully!")
    return redirect(url_for('index'))

@app.route('/delete_medicine/<int:medicine_id>')
def delete_medicine(medicine_id):
    if session.get('role') != 'root':
        return "Forbidden"
    med = Medicine.query.get(medicine_id)
    if not med:
        flash("Medicine not found.")
        return redirect(url_for('index'))

    # Prevent deleting if there are orders referencing this medicine
    if med.orders:
        flash("Cannot delete medicine that has existing orders.")
        return redirect(url_for('index'))

    try:
        db.session.delete(med)
        db.session.commit()
        flash(f"Medicine '{med.name}' deleted successfully!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting medicine: {e}")

    return redirect(url_for('index'))


# 2) CUSTOMERS ----------------------------------------------

@app.route('/customers')
def customers():
    if session.get('role') != 'root':
        return "Forbidden"
    cust_list = Customer.query.all()
    return render_template('customers.html', customers=cust_list)

@app.route('/create_customer', methods=['POST'])
def create_customer():
    if session.get('role') != 'root':
        return "Forbidden"
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    address = request.form.get('address')

    if not full_name:
        flash("Customer name is required.")
        return redirect(url_for('customers'))

    try:
        new_cust = Customer(full_name=full_name, phone=phone, address=address)
        db.session.add(new_cust)
        db.session.commit()
        flash(f"Customer '{full_name}' added successfully!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating customer: {e}")
    return redirect(url_for('customers'))

@app.route('/update_customer/<int:customer_id>', methods=['POST'])
def update_customer(customer_id):
    if session.get('role') != 'root':
        return "Forbidden"
    cust = Customer.query.get(customer_id)
    if not cust:
        flash("Customer not found.")
        return redirect(url_for('customers'))

    cust.full_name = request.form.get('full_name', cust.full_name)
    cust.phone = request.form.get('phone', cust.phone)
    cust.address = request.form.get('address', cust.address)

    db.session.commit()
    flash(f"Customer #{cust.id} updated successfully!")
    return redirect(url_for('customers'))

@app.route('/delete_customer/<int:customer_id>')
def delete_customer(customer_id):
    if session.get('role') != 'root':
        return "Forbidden"
    cust = Customer.query.get(customer_id)
    if not cust:
        flash("Customer not found.")
        return redirect(url_for('customers'))

    # Prevent deleting if the customer has orders
    if cust.orders:
        flash("Cannot delete customer who has existing orders.")
        return redirect(url_for('customers'))

    try:
        db.session.delete(cust)
        db.session.commit()
        flash(f"Customer '{cust.full_name}' deleted successfully.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting customer: {e}")

    return redirect(url_for('customers'))


# 3) ORDERS -------------------------------------------------

@app.route('/orders')
def orders():
    if session.get('role') != 'root':
        return "Forbidden"
    orders_rows = db.session.execute(text("SELECT * FROM orders_details")).fetchall()
    customers = Customer.query.all()
    medicines = Medicine.query.all()
    return render_template('orders.html', orders=orders_rows, customers=customers, medicines=medicines)

@app.route('/create_order', methods=['POST'])
def create_order():
    if session.get('role') != 'root':
        return "Forbidden"
    customer_id = request.form.get('customer_id')
    medicine_id = request.form.get('medicine_id')
    quantity = request.form.get('quantity', 1)

    try:
        quantity = int(quantity)
    except:
        quantity = 1

    if not customer_id or not medicine_id:
        flash("Choose a customer and medicine.")
        return redirect(url_for('orders'))

    new_order = Order(
        customer_id=customer_id,
        medicine_id=medicine_id,
        quantity=quantity
    )
    try:
        db.session.add(new_order)
        db.session.commit()
        flash("Order created successfully!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating order: {e}")
    return redirect(url_for('orders'))

@app.route('/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    if session.get('role') != 'root':
        return "Forbidden"
    ord_obj = Order.query.get(order_id)
    if not ord_obj:
        flash("Order not found.")
        return redirect(url_for('orders'))

    customer_id = request.form.get('customer_id')
    medicine_id = request.form.get('medicine_id')
    quantity = request.form.get('quantity', 1)

    try:
        quantity = int(quantity)
    except:
        quantity = 1

    ord_obj.customer_id = customer_id
    ord_obj.medicine_id = medicine_id
    ord_obj.quantity = quantity

    db.session.commit()
    flash(f"Order #{ord_obj.id} updated successfully!")
    return redirect(url_for('orders'))

@app.route('/delete_order/<int:order_id>')
def delete_order(order_id):
    if session.get('role') != 'root':
        return "Forbidden"
    ord_obj = Order.query.get(order_id)
    if not ord_obj:
        flash("Order not found.")
        return redirect(url_for('orders'))

    try:
        db.session.delete(ord_obj)
        db.session.commit()
        flash(f"Order #{order_id} deleted successfully.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting order: {e}")

    return redirect(url_for('orders'))


# -----------------------------------------------------------
# TEST USER ROUTES (READ-ONLY)
# -----------------------------------------------------------
@app.route('/view')
def test_view():
    if session.get('role') == 'test':
        rows = db.session.execute(text("SELECT * FROM medicines_with_categories")).fetchall()
        return render_template('view.html', rows=rows)
    return redirect(url_for('index'))

@app.route('/view_orders')
def test_orders():
    if session.get('role') == 'test':
        rows = db.session.execute(text("SELECT * FROM orders_details")).fetchall()
        return render_template('view_order.html', rows=rows)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
