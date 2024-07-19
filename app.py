from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, IntegerField, FloatField, DateField, PasswordField
from wtforms.validators import DataRequired, Optional
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Analyst@10'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tailor.db'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://u1ifbaupkdcsc9:p62ff6a5ca8e2b602fe2e9a7d9ab02c41baae28b5191db0b5a9947c3e9668e136@c1i13pt05ja4ag.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/de4qhno8h1om0q"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(80), nullable=True)

    measurement = db.relationship('Measurement', backref=db.backref('Customer', lazy=True), cascade="all, delete-orphan")

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    bust = db.Column(db.Integer)
    chest = db.Column(db.Integer)
    waist = db.Column(db.Integer)
    hips = db.Column(db.Integer)
    thigh = db.Column(db.Integer)
    neck = db.Column(db.Integer)
    sleeve = db.Column(db.Integer)
    inseam = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CustomerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Create Customer')

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.String(20), nullable=False)

class ItemForm(FlaskForm):
    item_name = StringField('Item', validators=[DataRequired()])
    price = StringField('Item Price (NGN)', validators=[DataRequired()])
    submit = SubmitField('Add Item')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(80), nullable=False)
    item_name = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_charged = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    expected_at = db.Column(db.DateTime, nullable=False)
    amount_paid = db.Column(db.String(20), nullable=False)
    to_balance = db.Column(db.String(20), nullable=True)
    delivered = db.Column(db.Integer, default=0)

class OrderForm(FlaskForm):
    customer_name = SelectField('Customer Name', validators=[DataRequired()])
    item_name = SelectField('Item', validators=[DataRequired()])
    quantity = IntegerField('Quantity', default=1, validators=[DataRequired()])
    price_charged = StringField('Price Charged (NGN)', validators=[DataRequired()])
    created_at = DateField('Order Date', format='%Y-%m-%d', validators=[DataRequired()])
    expected_at = DateField('Delivery Date', format='%Y-%m-%d', validators=[DataRequired()])
    amount_paid = StringField('Amount Paid (NGN)', validators=[DataRequired()])
    submit = SubmitField('Create Order')

class OrdExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), nullable=True)
    expense = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.String(80), nullable=True)
    price = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

class OrdExpenseForm(FlaskForm):
    order_id = StringField('Order ID', validators=[Optional()])
    expense = StringField('Expenses', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[Optional()])
    price = StringField('Price (NGN)', validators=[DataRequired()])
    submit = SubmitField('Add Expenses')

class IncExpenses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inc_item = db.Column(db.String(100), nullable=True)
    inc_date = db.Column(db.DateTime, nullable=False)
    inc_price = db.Column(db.String(80), nullable=True)
    inc_vol = db.Column(db.String(80), nullable=True)
    amount_made = db.Column(db.String(20), nullable=False)
    vol_sold = db.Column(db.String(80), nullable=False)
    date_sold = db.Column(db.DateTime, nullable=True)

class IncExpensesForm(FlaskForm):
    inc_item = StringField('Incurred Item', validators=[DataRequired()])
    inc_price = StringField('Incurred Price (NGN)', validators=[DataRequired()])
    inc_vol = StringField('Volume (NGN)', validators=[Optional()])
    amount_made = StringField('Amount Made (NGN)', validators=[Optional()])
    vol_sold = StringField('Volume Sold (NGN)', validators=[Optional()])
    date_sold = DateField('Date Sold', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Add Record')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)  # Add this line
    role = db.Column(db.String(20), default="member", nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Ensure the other required methods are present
    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Create tables
with app.app_context():
    db.create_all()
    
    # add new user
    #new_user = User(username='oyinlola')
    #new_user.set_password('Oyinlolareb1')
    #db.session.add(new_user)
    #db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    inc_cost = []
    for inc in IncExpenses.query.all():
        inc_cost.append(inc)

    orders_due = []
    orders = Order.query.filter_by(delivered=0).order_by(Order.expected_at).all()
    for order in orders:
        if abs(datetime.now()-order.expected_at).days in range(0,8):
            orders_due.append(order)
    
    # Format dates before sending to the template
    formatted_orders_due = []
    for order in orders_due:
        order_due_dict = {
            'id': order.id,
            'customer_name': order.customer_name,
            'item_name': order.item_name,
            'quantity': order.quantity,
            'price_charged': order.price_charged,
            'amount_paid': order.amount_paid,
            'to_balance': order.to_balance,
            'delivered': order.delivered,
            'created_at': order.created_at.strftime('%d-%m-%Y'),
            'expected_at': order.expected_at.strftime('%d-%m-%Y')
        }
        formatted_orders_due.append(order_due_dict)
        
    rec_orders = []
    for order in Order.query.order_by(Order.created_at.desc()).limit(5).all():
        if abs(datetime.now()-order.created_at).days in range(0,3):
            rec_orders.append(order)
    
    # Format dates before sending to the template
    formatted_rec_orders = []
    for order in rec_orders:
        rec_order_dict = {
            'id': order.id,
            'customer_name': order.customer_name,
            'item_name': order.item_name,
            'quantity': order.quantity,
            'price_charged': order.price_charged,
            'amount_paid': order.amount_paid,
            'to_balance': order.to_balance,
            'delivered': order.delivered,
            'created_at': order.created_at.strftime('%d-%m-%Y'),
            'expected_at': order.expected_at.strftime('%d-%m-%Y')
        }
        formatted_rec_orders.append(rec_order_dict)

    # Calculate the start of the current month
    today = datetime.today()
    today = datetime.combine(today, datetime.max.time())
    start_of_month = datetime(today.year, today.month, 1)
    start_of_month = datetime.combine(start_of_month, datetime.min.time())

    # Calculate the start and end of the previous month till the same date as today
    first_day_of_current_month = start_of_month
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    start_of_previous_month = datetime(last_day_of_previous_month.year, last_day_of_previous_month.month, 1)
    start_of_previous_month = datetime.combine(start_of_previous_month, datetime.min.time())

    # Calculate the day in the previous month corresponding to today's date
    if today.day <= last_day_of_previous_month.day:
        end_of_previous_month_mtd = datetime(last_day_of_previous_month.year, last_day_of_previous_month.month, today.day)
    else:
        end_of_previous_month_mtd = last_day_of_previous_month
    
    end_of_previous_month_mtd = datetime.combine(end_of_previous_month_mtd, datetime.max.time())

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        # Set time to the beginning of the start date and the end of the end date
        start_date_obj = datetime.combine(start_date, datetime.min.time())
        end_date_obj = datetime.combine(end_date, datetime.max.time())
        
        total_orders = Order.query.filter(Order.created_at.between(start_date, end_date)).all()
        inc_cost = IncExpenses.query.filter(IncExpenses.inc_date.between(start_date_obj, end_date_obj)).all()
        expenses_data = OrdExpense.query.filter(OrdExpense.created_at.between(start_date_obj, end_date_obj)).all()
        pending_orders = Order.query.filter(and_(Order.created_at.between(start_date, end_date), Order.delivered == 0)).all()
        delivered_orders = Order.query.filter(and_(Order.created_at.between(start_date, end_date), Order.delivered == 1)).all()

        start_date_prev_month = datetime(last_day_of_previous_month.year, last_day_of_previous_month.month, start_date.day)
        start_date_prev_month = datetime.combine(start_date_prev_month, datetime.min.time())
        last_date_prev_month = datetime(last_day_of_previous_month.year, last_day_of_previous_month.month, end_date.day)
        last_date_prev_month = datetime.combine(last_date_prev_month, datetime.max.time())

        # Last month till today's date in the previous month
        total_orders_last = Order.query.filter(Order.created_at.between(start_date_prev_month, last_date_prev_month)).all()
        inc_cost_last = IncExpenses.query.filter(IncExpenses.inc_date.between(start_date_prev_month, last_date_prev_month)).all()
        expenses_data_last = OrdExpense.query.filter(OrdExpense.created_at.between(start_date_prev_month, last_date_prev_month)).all()
        pending_orders_last = Order.query.filter(and_(Order.created_at.between(start_date_prev_month, last_date_prev_month), Order.delivered == 0)).all()
        delivered_orders_last = Order.query.filter(and_(Order.created_at.between(start_date_prev_month, last_date_prev_month), Order.delivered == 1)).all()
    else:
        total_orders = Order.query.filter(Order.created_at.between(start_of_month, today)).all()
        inc_cost = IncExpenses.query.filter(IncExpenses.inc_date.between(start_of_month, today)).all()
        expenses_data = OrdExpense.query.filter(OrdExpense.created_at.between(start_of_month, today)).all()
        pending_orders = Order.query.filter(and_(Order.created_at.between(start_of_month, today), Order.delivered == 0)).all()
        delivered_orders = Order.query.filter(and_(Order.created_at.between(start_of_month, today), Order.delivered == 1)).all()

        # Last month till today's date in the previous month
        total_orders_last = Order.query.filter(Order.created_at.between(start_of_previous_month, end_of_previous_month_mtd)).all()
        inc_cost_last = IncExpenses.query.filter(IncExpenses.inc_date.between(start_of_previous_month, end_of_previous_month_mtd)).all()
        expenses_data_last = OrdExpense.query.filter(OrdExpense.created_at.between(start_of_previous_month, end_of_previous_month_mtd)).all()
        pending_orders_last = Order.query.filter(and_(Order.created_at.between(start_of_previous_month, end_of_previous_month_mtd), Order.delivered == 0)).all()
        delivered_orders_last = Order.query.filter(and_(Order.created_at.between(start_of_previous_month, end_of_previous_month_mtd), Order.delivered == 1)).all()

    tot_order = len(total_orders)
    pending_orders = len(pending_orders)
    delivered_orders = len(delivered_orders)
    revenue = f'{sum([int(rev.price_charged.replace(",","")) for rev in total_orders]):,.0f}'
    expenses = f'{sum([int(exp.price.replace(",","")) for exp in expenses_data]):,.0f}'
    balance = f'{sum([int(bal.to_balance.replace(",","")) for bal in total_orders]):,.0f}'
    inc_value = f'{sum([int(inc.inc_price.replace(",","")) for inc in inc_cost]):,.0f}'
    inc_gain = f'{sum([int(inc.amount_made.replace(",","")) for inc in inc_cost]):,.0f}'
    net_revenue = f'{int(revenue.replace(",","")) - (int(expenses.replace(",","")) + int(balance.replace(",","")) + int(inc_value.replace(",",""))):,.0f}'

    tot_order_last = len(total_orders_last)
    pending_orders_last = len(pending_orders_last)
    delivered_orders_last = len(delivered_orders_last)
    revenue_last = f'{sum([int(rev.price_charged.replace(",","")) for rev in total_orders_last]):,.0f}'
    expenses_last = f'{sum([int(exp.price.replace(",","")) for exp in expenses_data_last]):,.0f}'
    balance_last = f'{sum([int(bal.to_balance.replace(",","")) for bal in total_orders_last]):,.0f}'
    inc_value_last = f'{sum([int(inc.inc_price.replace(",","")) for inc in inc_cost_last]):,.0f}'
    net_revenue_last = f'{int(revenue_last.replace(",","")) - (int(expenses_last.replace(",","")) + int(balance_last.replace(",","")) + int(inc_value_last.replace(",",""))):,.0f}'

    try:
        del_mtd = f"{((delivered_orders - delivered_orders_last)/delivered_orders_last) * 100:.2f}"
        tot_ord_mtd = f"{((tot_order - tot_order_last)/tot_order_last) * 100:.2f}"
        net_rev_mtd = f'{((int(net_revenue.replace(",","")) - int(net_revenue_last.replace(",","")))/int(net_revenue_last.replace(",",""))) * 100:.2f}'
    except ZeroDivisionError:
        del_mtd = "0"
        tot_ord_mtd = "0"
        net_rev_mtd = "0"

    if current_user.role == 'admin':  # Replace 'admin' with the role you want to check
        return render_template('index.html', orders_due=formatted_orders_due, rec_orders=formatted_rec_orders, revenue=revenue,
                           tot_order=tot_order, expenses=expenses, pending_orders=pending_orders,
                           balance=balance, net_revenue=net_revenue, delivered_orders=delivered_orders,
                           del_mtd=del_mtd, tot_ord_mtd=tot_ord_mtd, net_rev_mtd=net_rev_mtd,
                           inc_value=inc_value, inc_gain=inc_gain)
    else:
        return render_template('index.html', orders_due=formatted_orders_due, rec_orders=formatted_rec_orders,
                           tot_order=tot_order, expenses=expenses, pending_orders=pending_orders,
                           balance=balance, delivered_orders=delivered_orders,
                           del_mtd=del_mtd, tot_ord_mtd=tot_ord_mtd, net_rev_mtd=net_rev_mtd,
                           inc_value=inc_value, inc_gain=inc_gain)


@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    orders = []
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').lower()
        search_type = request.form.get('search_type')

        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        orders = []
        
        for order in Order.query.filter_by(delivered=0).order_by(Order.created_at.desc()).all():
            if search_type == 'customer_name' and search_query in order.customer_name.lower():
                orders.append(order)
            elif search_type == 'item' and search_query in order.item_name.lower():
                orders.append(order)
            if search_type == 'order_id' and search_query in str(order.id):
                orders.append(order)
            elif search_type == 'date':
                if start_date and end_date:
                    try:
                        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                        if start_date_obj <= order.created_at <= end_date_obj:
                            orders.append(order)
                    except ValueError:
                        print("Invalid date")
                elif search_query in str(order.created_at):
                    orders.append(order)
    
    else:
        for order in Order.query.filter_by(delivered=0).order_by(Order.created_at.desc()).all():
            orders.append(order)

    # Format dates before sending to the template
    formatted_orders = []
    for order in orders:
        order_dict = {
            'id': order.id,
            'customer_name': order.customer_name,
            'item_name': order.item_name,
            'quantity': order.quantity,
            'price_charged': order.price_charged,
            'amount_paid': order.amount_paid,
            'to_balance': order.to_balance,
            'delivered': order.delivered,
            'created_at': order.created_at.strftime('%d-%m-%Y'),
            'expected_at': order.expected_at.strftime('%d-%m-%Y')
        }

        formatted_orders.append(order_dict)


    return render_template('create_order.html', orders=formatted_orders)

@app.route('/delivered_order', methods=['GET', 'POST'])
def delivered_order():
    orders = []
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').lower()
        search_type = request.form.get('search_type')

        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        orders = []
        
        for order in Order.query.filter_by(delivered=1).order_by(Order.created_at.desc()).all():
            if search_type == 'customer_name' and search_query in order.customer_name.lower():
                orders.append(order)
            elif search_type == 'item' and search_query in order.item_name.lower():
                orders.append(order)
            if search_type == 'order_id' and search_query in str(order.id):
                orders.append(order)
            elif search_type == 'date':
                if start_date and end_date:
                    try:
                        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                        if start_date_obj <= order.created_at <= end_date_obj:
                            orders.append(order)
                    except ValueError:
                        print("Invalid date")
                elif search_query in str(order.created_at):
                    orders.append(order)
    
    else:
        for order in Order.query.filter_by(delivered=1).order_by(Order.created_at.desc()).all():
            orders.append(order)

    # Format dates before sending to the template
    formatted_orders = []
    for order in orders:
        order_dict = {
            'id': order.id,
            'customer_name': order.customer_name,
            'item_name': order.item_name,
            'quantity': order.quantity,
            'price_charged': order.price_charged,
            'amount_paid': order.amount_paid,
            'to_balance': order.to_balance,
            'delivered': order.delivered,
            'created_at': order.created_at.strftime('%d-%m-%Y'),
            'expected_at': order.expected_at.strftime('%d-%m-%Y')
        }

        formatted_orders.append(order_dict)

    return render_template('delivered.html', del_orders=formatted_orders)

@app.route('/view_expenses', methods=['GET', 'POST'])
def view_expenses():
    expenses = []
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').lower()
        search_type = request.form.get('search_type')

        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        expenses = []
        
        for exp in OrdExpense.query.order_by(OrdExpense.created_at.desc()).all():
            if search_type == 'order_id' and search_query in str(exp.order_id):
                expenses.append(exp)
            elif search_type == 'date':
                if start_date and end_date:
                    try:
                        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

                        # Set time to the beginning of the start date and the end of the end date
                        start_date_obj = datetime.combine(start_date_obj, datetime.min.time())
                        end_date_obj = datetime.combine(end_date_obj, datetime.max.time())

                        if start_date_obj <= exp.created_at <= end_date_obj:
                            expenses.append(exp)
                    except ValueError:
                        print("Invalid date")
                elif search_query in exp.created_at:
                    expenses.append(exp)
    
    else:
        for exp in OrdExpense.query.order_by(OrdExpense.created_at.desc()).all():
            expenses.append(exp)

    # Format dates before sending to the template
    formatted_expenses = []
    for exp in expenses:
        exp_dict = {
            'id': exp.id,
            'order_id': exp.order_id,
            'expense': exp.expense,
            'quantity': exp.quantity,
            'price': exp.price,
            'created_at': exp.created_at.strftime('%d-%m-%Y')
        }
        formatted_expenses.append(exp_dict)
        
    return render_template('expenses.html', expenses=formatted_expenses)

@app.route('/ready_order', methods=['GET', 'POST'])
def ready_order():
    inc_expenses = []
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').lower()
        search_type = request.form.get('search_type')

        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        inc_expenses = []
        
        for exp in IncExpenses.query.all():
            if search_type == 'item' and search_query in exp.inc_item:
                inc_expenses.append(exp)
            elif search_type == 'date':
                if start_date and end_date:
                    try:
                        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

                        # Set time to the beginning of the start date and the end of the end date
                        start_date_obj = datetime.combine(start_date_obj, datetime.min.time())
                        end_date_obj = datetime.combine(end_date_obj, datetime.max.time())

                        if start_date_obj <= exp.inc_date <= end_date_obj:
                            inc_expenses.append(exp)
                    except ValueError:
                        print("Invalid date")
                elif search_query in exp.inc_date:
                    inc_expenses.append(exp)
    
    else:
        for exp in IncExpenses.query.all():
            inc_expenses.append(exp)
        
    # Format dates before sending to the template
    formatted_inc = []
    for inc in inc_expenses:
        try:
            inc_dict = {
                'id': inc.id,
                'inc_item': inc.inc_item,
                'inc_date': inc.inc_date.strftime('%d-%m-%Y'),
                'inc_price': inc.inc_price,
                'inc_vol': inc.inc_vol,
                'amount_made': inc.amount_made,
                'vol_sold': inc.vol_sold,
                'date_sold': inc.date_sold.strftime('%d-%m-%Y')
            }
        except AttributeError:
            inc_dict = {
                'id': inc.id,
                'inc_item': inc.inc_item,
                'inc_date': inc.inc_date.strftime('%d-%m-%Y'),
                'inc_price': inc.inc_price,
                'inc_vol': inc.inc_vol,
                'amount_made': inc.amount_made,
                'vol_sold': inc.vol_sold,
                'date_sold': None
            }
        
        formatted_inc.append(inc_dict)

    return render_template('ready_made.html', inc_expenses=formatted_inc)

@app.route('/add_ready', methods=['GET', 'POST'])
def add_ready():
    form = IncExpensesForm()

    if form.validate_on_submit():
        new_inc_expense = IncExpenses(
            inc_item=form.inc_item.data,
            inc_date=datetime.utcnow(),
            inc_price=form.inc_price.data,
            inc_vol=form.inc_vol.data,
            amount_made=form.amount_made.data,
            vol_sold=form.vol_sold.data,
            date_sold=form.date_sold.data
        )
        db.session.add(new_inc_expense)
        db.session.commit()
        flash('Expenses added successfully!', 'success')
        return redirect(url_for('ready_order'))
    
    return render_template('add_ready.html', form=form)

@app.route('/edit_inc_expenses/<int:id>', methods=['GET', 'POST'])
def edit_inc_expenses(id:int):
    exp = IncExpenses.query.get_or_404(id)
    if request.method == 'POST':
        exp.inc_item = request.form['inc_item']
        exp.inc_price = request.form['inc_price']
        exp.inc_vol = request.form['inc_vol']
        exp.amount_made = request.form['amount_made']
        exp.vol_sold = request.form['vol_sold']
        try:
            exp.date_sold = datetime.strptime(request.form['date_sold'], "%Y-%m-%d")
        except ValueError:
            exp.date_sold = None
        db.session.commit()
        return redirect(url_for('ready_order'))
    return render_template('edit_ready.html', exp=exp)

@app.route('/delete_inc_expenses/<int:id>')
def delete_inc_expenses(id:int):
    delete_expenses_obj = IncExpenses.query.get_or_404(id)
    db.session.delete(delete_expenses_obj)
    db.session.commit()
    return redirect(url_for("ready_order"))

@app.route('/view_customer', methods=['GET', 'POST'])
def view_customer():
    customers = []
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').lower()
        search_type = request.form.get('search_type')

        for customer in Customer.query.all():
            if search_type == 'name' and search_query in customer.name.lower():
                customers.append(customer)
            elif search_type == 'phone' and search_query in customer.phone:
                customers.append(customer)
    
    else:
        for customer in Customer.query.all():
            customers.append(customer)
        
    return render_template('customer_page.html', customers=customers)

@app.route('/create_customer', methods=['GET', 'POST'])
def create_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        new_customer = Customer(
            name=form.name.data,
            phone=form.phone.data,
            gender=form.gender.data,
            address=form.address.data
        )
        db.session.add(new_customer)
        db.session.commit()
        flash('Customer created successfully!', 'success')
        return redirect(url_for('measurement_page', customer_id=new_customer.id))
    return render_template('create_customer.html', form=form)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    form = ItemForm()
    if form.validate_on_submit():
        new_item = Item(
            item_name=form.item_name.data,
            price=form.price.data
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('items'))
    return render_template('add_item.html', form=form)

@app.route('/items', methods=['GET', 'POST'])
def items():
    items = []
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').lower()

        for item in Item.query.all():
            if search_query in item.item_name.lower():
                items.append(item)

    else:
        for item in Item.query.all():
            items.append(item)

    return render_template('item_page.html', items=items)

@app.route('/measurement/<int:customer_id>', methods=['GET', 'POST'])
def measurement_page(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        new_measurement = Measurement(
            customer_id=customer.id,
            bust=request.form.get('bust'),
            chest=request.form.get('chest'),
            waist=request.form.get('waist'),
            hips=request.form.get('hips'),
            thigh=request.form.get('thigh'),
            neck=request.form.get('neck'),
            sleeve=request.form.get('sleeve'),
            inseam=request.form.get('inseam'),
            created_at=datetime.utcnow()
        )
        db.session.add(new_measurement)
        db.session.commit()
        return redirect(url_for('view_customer'))  # Redirect to the dashboard or another page after saving
    return render_template('measurement.html', customer=customer)

@app.route('/create_new_order', methods=['GET', 'POST'])
def create_new_order():
    form = OrderForm()

    # Populate item choices and customer name
    form.item_name.choices = [item.item_name for item in Item.query.all()]
    form.customer_name.choices = [customer.name for customer in Customer.query.all()]

    if form.validate_on_submit():
        # Convert the price_charged and amount_paid to numeric values
        price_charged_v = int(form.price_charged.data.replace(',', '')) 
        amount_paid_v = int(form.amount_paid.data.replace(',', '')) 
        
        # Calculate the to_balance value
        to_balance = f'{(price_charged_v - amount_paid_v):,.0f}'

        new_order = Order(
            customer_name=form.customer_name.data,
            item_name=form.item_name.data,
            quantity=form.quantity.data,
            price_charged=form.price_charged.data,
            created_at=form.created_at.data,
            expected_at=form.expected_at.data,
            amount_paid=form.amount_paid.data,
            to_balance=to_balance
        )
        
        db.session.add(new_order)
        db.session.commit()
        flash('Order created successfully!', 'success')
        return redirect(url_for('create_order'))
    
    return render_template('order.html', form=form)

@app.route('/add_expenses', methods=['GET', 'POST'])
def add_expenses():
    form = OrdExpenseForm()

    if form.validate_on_submit():
        new_expense = OrdExpense(
            order_id=form.order_id.data,
            expense=form.expense.data,
            quantity=form.quantity.data,
            price=form.price.data,
            created_at=datetime.utcnow()
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expenses added successfully!', 'success')
        return redirect(url_for('view_expenses'))
    
    return render_template('add_expenses.html', form=form)

@app.route('/delete_item/<int:id>')
def delete_item(id:int):
    delete_item_obj = Item.query.get_or_404(id)
    db.session.delete(delete_item_obj)
    db.session.commit()
    return redirect(url_for("items"))

@app.route('/edit_item/<int:id>', methods=['GET', 'POST'])
def edit_item(id:int):
    item = Item.query.get_or_404(id)
    if request.method == 'POST':
        item.item_name = request.form['item_name']
        item.price = request.form['price']
        db.session.commit()
        return redirect(url_for('items'))
    return render_template('edit_item.html', item=item)

@app.route('/delete_customer/<int:id>')
def delete_customer(id:int):
    delete_customer_obj = Customer.query.get_or_404(id)
    db.session.delete(delete_customer_obj)
    db.session.commit()
    return redirect(url_for("view_customer"))

@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
def edit_customer(id:int):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.phone = request.form['phone']
        customer.address = request.form['address']
        db.session.commit()
        return redirect(url_for('view_customer'))
    return render_template('edit_customer.html', customer=customer)

@app.route('/delete_order/<int:id>')
def delete_order(id:int):
    delete_order_obj = Order.query.get_or_404(id)
    db.session.delete(delete_order_obj)
    db.session.commit()
    return redirect(url_for("create_order"))

@app.route('/edit_order/<int:id>', methods=['GET', 'POST'])
def edit_order(id:int):
    order = Order.query.get_or_404(id)
    if request.method == 'POST':
        # Convert the price_charged and amount_paid to numeric values
        price_charged_v = int(request.form["price"].replace(',', '')) 
        amount_paid_v = int(request.form["amount"].replace(',', '')) 
        
        # Calculate the to_balance value
        to_balance = f'{(price_charged_v - amount_paid_v):,.0f}'
        try:
            order.item_name = request.form['item_name']
            order.quantity = request.form['quantity']
            order.price_charged = request.form['price']
            order.amount_paid = request.form['amount']
            order.to_balance = to_balance
            db.session.commit()
        except:
            pass
        return redirect(url_for('create_order'))
    return render_template('edit_order.html', order=order)

@app.route('/view_measurement/<int:customer_id>', methods=['GET', 'POST'])
def view_measurement(customer_id:int):
    customer = Customer.query.get_or_404(customer_id)
    measurement = Measurement.query.get_or_404(customer.id)
    db.session.commit()

    return render_template('view_measurement.html', measurement=measurement, customer=customer)

@app.route('/edit_measurement/<int:id>', methods=['GET', 'POST'])
def edit_measurement(id:int):
    measurement = Measurement.query.get_or_404(id)
    if request.method == 'POST':
        measurement.bust = request.form['bust']
        measurement.chest = request.form['chest']
        measurement.waist = request.form['waist']
        measurement.hips = request.form['hips']
        measurement.thigh = request.form['thigh']
        measurement.neck = request.form['neck']
        measurement.sleeve = request.form['sleeve']
        measurement.inseam = request.form['inseam']
        measurement.created_at = datetime.utcnow()
        
        db.session.commit()
        return redirect(url_for('view_measurement', customer_id=measurement.customer_id))
    return render_template('edit_measurement.html', measurement=measurement)

@app.route('/delete_expenses/<int:id>')
def delete_expenses(id:int):
    delete_expenses_obj = OrdExpense.query.get_or_404(id)
    db.session.delete(delete_expenses_obj)
    db.session.commit()
    return redirect(url_for("view_expenses"))

@app.route('/edit_expenses/<int:id>', methods=['GET', 'POST'])
def edit_expenses(id:int):
    exp = OrdExpense.query.get_or_404(id)
    if request.method == 'POST':
        exp.order_id = request.form['order_id']
        exp.expense = request.form['expense']
        exp.quantity = request.form['quantity']
        exp.price = request.form['price']

        db.session.commit()
        return redirect(url_for('view_expenses'))
    return render_template('edit_expenses.html', exp=exp)

@app.route('/update_delivery_status/<int:order_id>', methods=['POST'])
def update_delivery_status(order_id):
    order = Order.query.get_or_404(order_id)
    delivered = request.form.get('delivered')
    
    if delivered == 'yes':
        order.delivered = 1

        db.session.commit()
        return redirect(url_for('create_order'))


# dashboard reports

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/api/orders')
def orders_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    data = []

    if start_date and end_date:
        for order in Order.query.all():
            order_date = order.created_at.strftime("%Y-%m-%d")
            if start_date <= order_date <= end_date:
                data.append({
                    'created_at': order.created_at.strftime('%Y-%m-%d'),
                })
        df = pd.DataFrame(data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.set_index('created_at').resample('D').size()

    else:
        for order in Order.query.order_by(Order.created_at.desc()).all():
            data.append({
                'created_at': order.created_at.strftime('%Y-%m-%d'),
            })
        df = pd.DataFrame(data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.set_index('created_at').resample('D').size()
        df = df.tail(7)

    # Convert the index to strings
    df.index = df.index.strftime('%m-%d')
    return jsonify(df.to_dict())

@app.route('/api/items')
def items_data():
    item_orders = Order.query.all()
    data = {}
    for item in item_orders:
        category = item.item_name
        if category in data:
            data[category] += 1
        else:
            data[category] = 1
    
    sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:5])

    return jsonify(sorted_data)

@app.route('/api/expenses_vs_paid')
def expenses_vs_paid_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    orders = Order.query.all()
    expenses = OrdExpense.query.all()

    total_paid = []
    total_expenses = []

    for order in orders:
        if start_date and end_date:
            order_date = order.created_at.strftime("%Y-%m-%d")
            if start_date <= order_date <= end_date:
                total_paid.append(int(order.amount_paid.replace(",","")))
        else:
            total_paid.append(int(order.amount_paid.replace(",","")))

    for expense in expenses:
        if start_date and end_date:
            expense_date = expense.created_at.strftime("%Y-%m-%d")
            if start_date <= expense_date <= end_date:
                total_expenses.append(int(expense.price.replace(",","")))
        else:
            total_expenses.append(int(expense.price.replace(",","")))
    

    data = {
        'Amount Paid': sum(total_paid),
        'Expenses': sum(total_expenses)
    }
    return jsonify(data)

@app.route('/api/top_customers')
def top_customers():
    orders = Order.query.all()
    customer_orders = {}

    for order in orders:
        customer_name = order.customer_name
        if customer_name in customer_orders:
            customer_orders[customer_name] += 1
        else:
            customer_orders[customer_name] = 1

    sorted_customers = sorted(customer_orders.items(), key=lambda x: x[1], reverse=True)[:5]
    top_customers_data = []

    for customer_name, order_count in sorted_customers:
        top_customers_data.append({
            'name': customer_name,
            'order_count': order_count
        })

    return jsonify(top_customers_data)


# login

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'login')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
