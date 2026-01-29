from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
)
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import inspect, func


app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-for-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///stylelane.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_SUPPLIER = "supplier"


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    managers = db.relationship("User", backref="store", lazy=True)
    inventory_items = db.relationship("Inventory", backref="store_rel", lazy=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=True)
    supplier_name = db.Column(db.String(120), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(80), unique=True, nullable=False)
    category = db.Column(db.String(80), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    price = db.Column(db.Float, nullable=True)
    cost_price = db.Column(db.Float, nullable=True)
    size = db.Column(db.String(20), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    inventory_items = db.relationship("Inventory", backref="product_rel", lazy=True)
    
    @property
    def profit_margin(self):
        if self.price and self.cost_price:
            return ((self.price - self.cost_price) / self.price) * 100
        return 0


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=10, nullable=False)

    sales = db.relationship("Sale", backref="inventory_item", lazy=True)
    restock_requests = db.relationship(
        "RestockRequest", backref="inventory_item", lazy=True
    )

    @property
    def is_low(self) -> bool:
        return self.quantity <= self.low_stock_threshold


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class RestockRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("store.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="pending", nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    shipment = db.relationship("Shipment", backref="restock_request", uselist=False)


class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restock_request_id = db.Column(
        db.Integer, db.ForeignKey("restock_request.id"), nullable=False
    )
    status = db.Column(db.String(50), default="preparing", nullable=False)
    tracking_info = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if "user_role" not in session or session["user_role"] not in roles:
                flash("You do not have permission for that action.", "danger")
                return redirect(url_for("login"))
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def ensure_db_initialized():
    """Create tables if the database is empty to avoid login failures."""
    inspector = inspect(db.engine)
    if not inspector.has_table("user"):
        db.create_all()


@app.before_request
def _bootstrap_db():
    ensure_db_initialized()


def seed_demo_data():
    """Idempotent seed data for demo usage."""
    if not User.query.filter_by(role=ROLE_ADMIN).first():
        admin = User(username="admin", role=ROLE_ADMIN)
        admin.set_password("admin123")
        db.session.add(admin)

    if not Store.query.first():
        store = Store(name="Flagship Store", location="Downtown")
        db.session.add(store)
        manager = User(username="manager1", role=ROLE_MANAGER, store=store)
        manager.set_password("manager123")
        db.session.add(manager)

    if not User.query.filter_by(role=ROLE_SUPPLIER).first():
        supplier = User(
            username="supplier1",
            role=ROLE_SUPPLIER,
            supplier_name="Universal Fashions",
            contact_email="contact@supplier.test",
        )
        supplier.set_password("supplier123")
        db.session.add(supplier)

    if not Product.query.first():
        # Use a local static placeholder image; templates will resolve relative paths via url_for('static', ...)
        product = Product(
            name="Classic Tee",
            sku="TEE-001",
            category="Tops",
            price=29.99,
            cost_price=12.00,
            size="M",
            color="White",
            description="Classic cotton t-shirt",
            image_url="https://images.pexels.com/photos/996329/pexels-photo-996329.jpeg?auto=compress&cs=tinysrgb&w=400&h=500&fit=crop",
        )
        db.session.add(product)
        db.session.flush()
        inv = Inventory(
            store_id=1, product_id=product.id, quantity=25, low_stock_threshold=5
        )
        db.session.add(inv)
        
        # Add more demo products
        product2 = Product(
            name="Denim Jeans",
            sku="JNS-001",
            category="Bottoms",
            price=79.99,
            cost_price=35.00,
            size="32",
            color="Blue",
            description="Classic fit denim jeans",
            image_url="https://images.pexels.com/photos/1598507/pexels-photo-1598507.jpeg?auto=compress&cs=tinysrgb&w=400&h=500&fit=crop",
        )
        db.session.add(product2)
        db.session.flush()
        inv2 = Inventory(
            store_id=1, product_id=product2.id, quantity=15, low_stock_threshold=5
        )
        db.session.add(inv2)
        
        product3 = Product(
            name="Winter Jacket",
            sku="JKT-001",
            category="Outerwear",
            price=149.99,
            cost_price=65.00,
            size="L",
            color="Black",
            description="Warm winter jacket",
            image_url="https://images.pexels.com/photos/1040945/pexels-photo-1040945.jpeg?auto=compress&cs=tinysrgb&w=400&h=500&fit=crop",
        )
        db.session.add(product3)
        db.session.flush()
        inv3 = Inventory(
            store_id=1, product_id=product3.id, quantity=8, low_stock_threshold=3
        )
        db.session.add(inv3)

    db.session.commit()


@app.route("/")
def index():
    if "user_role" not in session:
        # Show splash only once per anonymous session
        if not session.get("splash_seen"):
            session["splash_seen"] = True
            return redirect(url_for("splash"))
        return redirect(url_for("login"))
    role = session["user_role"]
    if role == ROLE_ADMIN:
        return redirect(url_for("admin_dashboard"))
    if role == ROLE_MANAGER:
        return redirect(url_for("manager_dashboard"))
    if role == ROLE_SUPPLIER:
        return redirect(url_for("supplier_dashboard"))
    return redirect(url_for("login"))


@app.route("/splash")
def splash():
    """Splash screen that shows the app branding before redirecting to login."""
    if "user_role" in session:
        # If already logged in, redirect to appropriate dashboard
        role = session["user_role"]
        if role == ROLE_ADMIN:
            return redirect(url_for("admin_dashboard"))
        if role == ROLE_MANAGER:
            return redirect(url_for("manager_dashboard"))
        if role == ROLE_SUPPLIER:
            return redirect(url_for("supplier_dashboard"))
    # Mark splash as seen so we do not show it repeatedly in the same session
    session["splash_seen"] = True
    return render_template("splash.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_role"] = user.role
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("index"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Signed out.", "info")
    return redirect(url_for("login"))


@app.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def admin_dashboard():
    stores = Store.query.order_by(Store.name).all()
    managers = User.query.filter_by(role=ROLE_MANAGER).all()
    suppliers = User.query.filter_by(role=ROLE_SUPPLIER).all()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create_store":
            name = request.form.get("store_name")
            location = request.form.get("store_location")
            if name:
                store = Store(name=name, location=location)
                db.session.add(store)
                db.session.commit()
                flash("Store created.", "success")
            else:
                flash("Store name is required.", "warning")
        elif action == "create_manager":
            username = request.form.get("manager_username")
            password = request.form.get("manager_password")
            store_id = request.form.get("manager_store_id")
            if username and password and store_id:
                if User.query.filter_by(username=username).first():
                    flash("Username already exists.", "warning")
                else:
                    manager = User(
                        username=username, role=ROLE_MANAGER, store_id=store_id
                    )
                    manager.set_password(password)
                    db.session.add(manager)
                    db.session.commit()
                    flash("Store manager created.", "success")
            else:
                flash("All fields are required for manager.", "warning")
        elif action == "create_supplier":
            username = request.form.get("supplier_username")
            password = request.form.get("supplier_password")
            supplier_name = request.form.get("supplier_name")
            contact_email = request.form.get("supplier_email")
            if username and password:
                if User.query.filter_by(username=username).first():
                    flash("Username already exists.", "warning")
                else:
                    supplier = User(
                        username=username,
                        role=ROLE_SUPPLIER,
                        supplier_name=supplier_name,
                        contact_email=contact_email,
                    )
                    supplier.set_password(password)
                    db.session.add(supplier)
                    db.session.commit()
                    flash("Supplier created.", "success")
            else:
                flash("Username and password are required for supplier.", "warning")
        return redirect(url_for("admin_dashboard"))

    inventory = (
        db.session.query(Inventory, Store, Product)
        .join(Store, Inventory.store_id == Store.id)
        .join(Product, Inventory.product_id == Product.id)
        .all()
    )
    sales_total = db.session.query(db.func.sum(Sale.total_amount)).scalar() or 0
    low_stock = [item for item, _, _ in inventory if item.is_low]
    return render_template(
        "admin_dashboard.html",
        stores=stores,
        managers=managers,
        suppliers=suppliers,
        inventory=inventory,
        sales_total=sales_total,
        low_stock_count=len(low_stock),
    )


@app.route("/manager/dashboard", methods=["GET", "POST"])
@login_required
@role_required(ROLE_MANAGER)
def manager_dashboard():
    user = current_user()
    if not user.store_id:
        flash("Manager is not assigned to a store.", "danger")
        return redirect(url_for("logout"))

    inventory_items = (
        Inventory.query.filter_by(store_id=user.store_id)
        .join(Product, Inventory.product_id == Product.id)
        .all()
    )
    products = Product.query.order_by(Product.name).all()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_product":
            name = request.form.get("product_name")
            sku = request.form.get("product_sku")
            category = request.form.get("product_category")
            size = request.form.get("product_size")
            color = request.form.get("product_color")
            price = request.form.get("product_price")
            cost_price = request.form.get("product_cost_price")
            image_url = request.form.get("product_image_url")
            description = request.form.get("product_description")
            
            if not name or not sku:
                flash("Product name and SKU are required.", "warning")
            else:
                product = Product.query.filter_by(sku=sku).first()
                if not product:
                    product = Product(
                        name=name,
                        sku=sku,
                        category=category if category else None,
                        size=size if size else None,
                        color=color if color else None,
                        price=float(price) if price else None,
                        cost_price=float(cost_price) if cost_price else None,
                        image_url=image_url if image_url else None,
                        description=description if description else None
                    )
                    db.session.add(product)
                    db.session.commit()
                else:
                    # Update existing product with new information if provided
                    if category:
                        product.category = category
                    if size:
                        product.size = size
                    if color:
                        product.color = color
                    if price:
                        product.price = float(price)
                    if cost_price:
                        product.cost_price = float(cost_price)
                    if image_url:
                        product.image_url = image_url
                    if description:
                        product.description = description
                    db.session.commit()
                    
                inv = Inventory.query.filter_by(
                    store_id=user.store_id, product_id=product.id
                ).first()
                if not inv:
                    inv = Inventory(
                        store_id=user.store_id, product_id=product.id, quantity=0
                    )
                    db.session.add(inv)
                flash("Product added to store inventory.", "success")
                db.session.commit()
        elif action == "update_quantity":
            inventory_id = request.form.get("inventory_id")
            quantity = request.form.get("quantity")
            threshold = request.form.get("threshold")
            inv = Inventory.query.get(inventory_id)
            if inv and inv.store_id == user.store_id:
                inv.quantity = int(quantity)
                if threshold:
                    inv.low_stock_threshold = int(threshold)
                db.session.commit()
                flash("Quantity updated.", "success")
        elif action == "record_sale":
            inventory_id = request.form.get("inventory_id")
            quantity = int(request.form.get("sale_quantity", 0))
            price = float(request.form.get("sale_price", 0))
            inv = Inventory.query.get(inventory_id)
            if inv and inv.store_id == user.store_id and quantity > 0:
                inv.quantity = max(inv.quantity - quantity, 0)
                sale = Sale(
                    inventory_id=inv.id,
                    store_id=inv.store_id,
                    product_id=inv.product_id,
                    quantity=quantity,
                    total_amount=quantity * price,
                )
                db.session.add(sale)
                db.session.commit()
                flash("Sale recorded.", "success")
        elif action == "request_restock":
            inventory_id = request.form.get("inventory_id")
            qty = int(request.form.get("request_quantity", 0))
            notes = request.form.get("request_notes")
            inv = Inventory.query.get(inventory_id)
            if inv and inv.store_id == user.store_id and qty > 0:
                req = RestockRequest(
                    inventory_id=inv.id,
                    store_id=inv.store_id,
                    product_id=inv.product_id,
                    quantity_requested=qty,
                    manager_id=user.id,
                    status="pending",
                    notes=notes,
                )
                db.session.add(req)
                db.session.commit()
                flash("Restock request submitted.", "success")
        return redirect(url_for("manager_dashboard"))

    restocks = (
        RestockRequest.query.filter_by(store_id=user.store_id)
        .order_by(RestockRequest.created_at.desc())
        .all()
    )
    return render_template(
        "manager_dashboard.html",
        inventory_items=inventory_items,
        restocks=restocks,
        products=products,
    )


@app.route("/supplier/dashboard", methods=["GET", "POST"])
@login_required
@role_required(ROLE_SUPPLIER)
def supplier_dashboard():
    user = current_user()
    if request.method == "POST":
        action = request.form.get("action")
        req_id = request.form.get("request_id")
        req = RestockRequest.query.get(req_id)
        if not req:
            flash("Request not found.", "warning")
            return redirect(url_for("supplier_dashboard"))

        if action == "accept":
            req.status = "approved"
            req.supplier_id = user.id
            req.updated_at = datetime.utcnow()
            flash("Restock request accepted.", "success")
        elif action == "reject":
            req.status = "rejected"
            req.supplier_id = user.id
            req.updated_at = datetime.utcnow()
            flash("Restock request rejected.", "info")
        elif action == "ship":
            tracking = request.form.get("tracking_info")
            req.status = "shipped"
            req.supplier_id = user.id
            req.updated_at = datetime.utcnow()
            shipment = req.shipment
            if not shipment:
                shipment = Shipment(restock_request_id=req.id)
                db.session.add(shipment)
            shipment.status = "shipped"
            shipment.tracking_info = tracking
            shipment.updated_at = datetime.utcnow()
            inventory = Inventory.query.get(req.inventory_id)
            if inventory:
                inventory.quantity += req.quantity_requested
            flash("Shipment marked as shipped and stock updated.", "success")
        db.session.commit()
        return redirect(url_for("supplier_dashboard"))

    pending = RestockRequest.query.filter(
        RestockRequest.status.in_(["pending", "approved", "shipped"])
    ).order_by(RestockRequest.created_at.desc())
    requests = pending.all()
    return render_template("supplier_dashboard.html", requests=requests, user=user)


@app.route("/analytics")
@login_required
def analytics():
    """Analytics dashboard with charts and insights."""
    # Sales data for charts
    sales_last_30 = Sale.query.filter(
        Sale.timestamp >= datetime.utcnow() - timedelta(days=30)
    ).all()
    
    # Top products by sales
    top_products = (
        db.session.query(
            Product.name,
            Product.sku,
            func.sum(Sale.quantity).label('total_sold'),
            func.sum(Sale.total_amount).label('total_revenue')
        )
        .join(Sale, Product.id == Sale.product_id)
        .group_by(Product.id)
        .order_by(func.sum(Sale.total_amount).desc())
        .limit(10)
        .all()
    )
    
    # Sales by store
    sales_by_store = (
        db.session.query(
            Store.name,
            func.sum(Sale.total_amount).label('revenue'),
            func.count(Sale.id).label('transactions')
        )
        .join(Sale, Store.id == Sale.store_id)
        .group_by(Store.id)
        .all()
    )
    
    # Recent sales trend (last 7 days)
    daily_sales = {}
    for i in range(7):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        date_str = date.strftime('%Y-%m-%d')
        # SQLite-compatible date filtering
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        daily_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.timestamp >= start_of_day,
            Sale.timestamp <= end_of_day
        ).scalar() or 0
        daily_sales[date_str] = float(daily_revenue)
    
    # Category performance
    category_sales = (
        db.session.query(
            Product.category,
            func.sum(Sale.total_amount).label('revenue'),
            func.sum(Sale.quantity).label('units_sold')
        )
        .join(Sale, Product.id == Sale.product_id)
        .filter(Product.category.isnot(None))
        .group_by(Product.category)
        .all()
    )
    
    total_revenue = db.session.query(func.sum(Sale.total_amount)).scalar() or 0
    total_sales = Sale.query.count()
    
    return render_template(
        "analytics.html",
        top_products=top_products,
        sales_by_store=sales_by_store,
        daily_sales=daily_sales,
        category_sales=category_sales,
        total_revenue=total_revenue,
        total_sales=total_sales,
    )


@app.route("/products/search")
@login_required
def product_search():
    """Advanced product search with filters."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    size = request.args.get('size', '')
    color = request.args.get('color', '')
    
    products_query = Product.query
    
    if query:
        products_query = products_query.filter(
            db.or_(
                Product.name.ilike(f'%{query}%'),
                Product.sku.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%') if Product.description else False
            )
        )
    
    if category:
        products_query = products_query.filter(Product.category == category)
    if size:
        products_query = products_query.filter(Product.size == size)
    if color:
        products_query = products_query.filter(Product.color.ilike(f'%{color}%'))
    
    products = products_query.order_by(Product.name).all()
    
    # Get available filters
    categories = db.session.query(Product.category).distinct().filter(
        Product.category.isnot(None)
    ).all()
    sizes = db.session.query(Product.size).distinct().filter(
        Product.size.isnot(None)
    ).all()
    colors = db.session.query(Product.color).distinct().filter(
        Product.color.isnot(None)
    ).all()
    
    # Get inventory info for each product
    products_with_inventory = []
    for product in products:
        inventory_data = (
            db.session.query(Store.name, Inventory.quantity, Inventory.is_low)
            .join(Inventory, Store.id == Inventory.store_id)
            .filter(Inventory.product_id == product.id)
            .all()
        )
        products_with_inventory.append({
            'product': product,
            'inventory': inventory_data
        })
    
    return render_template(
        "product_search.html",
        products=products_with_inventory,
        query=query,
        selected_category=category,
        selected_size=size,
        selected_color=color,
        categories=[c[0] for c in categories],
        sizes=[s[0] for s in sizes],
        colors=[c[0] for c in colors],
    )


@app.route("/products/<int:product_id>/barcode")
@login_required
def product_barcode(product_id):
    """Generate barcode/QR code for a product."""
    product = Product.query.get_or_404(product_id)
    return render_template("barcode.html", product=product)


@app.route("/reports/sales")
@login_required
def sales_report():
    """Sales report with date filtering."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Sale.query
    
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Sale.timestamp >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Sale.timestamp < end)
        except ValueError:
            pass
    
    sales = (
        query
        .join(Product, Sale.product_id == Product.id)
        .join(Store, Sale.store_id == Store.id)
        .order_by(Sale.timestamp.desc())
        .all()
    )
    
    total_revenue = sum(sale.total_amount for sale in sales)
    total_quantity = sum(sale.quantity for sale in sales)
    
    return render_template(
        "sales_report.html",
        sales=sales,
        total_revenue=total_revenue,
        total_quantity=total_quantity,
        start_date=start_date,
        end_date=end_date,
    )


@app.route("/recommendations")
@login_required
def recommendations():
    """Product recommendations based on sales trends."""
    # Products with low stock that are selling well
    fast_selling = (
        db.session.query(
            Product.id,
            Product.name,
            Product.sku,
            Product.category,
            func.sum(Sale.quantity).label('sold_last_30')
        )
        .join(Sale, Product.id == Sale.product_id)
        .filter(Sale.timestamp >= datetime.utcnow() - timedelta(days=30))
        .group_by(Product.id)
        .having(func.sum(Sale.quantity) >= 5)
        .all()
    )
    
    # Check which ones have low stock
    recommendations = []
    for product_id, name, sku, category, sold_qty in fast_selling:
        low_stock_stores = []
        inventories = Inventory.query.filter_by(product_id=product_id).all()
        for inv in inventories:
            if inv.is_low:
                store = Store.query.get(inv.store_id)
                low_stock_stores.append({
                    'store': store.name,
                    'current_qty': inv.quantity,
                    'threshold': inv.low_stock_threshold
                })
        
        if low_stock_stores:
            recommendations.append({
                'product': Product.query.get(product_id),
                'sold_last_30': sold_qty,
                'low_stock_stores': low_stock_stores
            })
    
    # Also recommend top products that might need restocking
    top_products = (
        db.session.query(
            Product.id,
            func.sum(Sale.total_amount).label('revenue')
        )
        .join(Sale, Product.id == Sale.product_id)
        .filter(Sale.timestamp >= datetime.utcnow() - timedelta(days=30))
        .group_by(Product.id)
        .order_by(func.sum(Sale.total_amount).desc())
        .limit(5)
        .all()
    )
    
    return render_template(
        "recommendations.html",
        fast_selling_low_stock=recommendations,
        top_products=[Product.query.get(pid) for pid, _ in top_products],
    )


@app.route("/initdb")
def initdb():
    """Initialize the database with seed data for demo purposes."""
    db.create_all()
    seed_demo_data()
    return "Database initialized with demo data. Default admin: admin/admin123"


@app.route("/resetdb")
def resetdb():
    """Drop and recreate all tables, then seed demo data (dev-only helper)."""
    db.drop_all()
    db.create_all()
    seed_demo_data()
    return "Database reset + seeded. Default admin: admin/admin123"


@app.route("/update-product-images")
@login_required
@role_required(ROLE_ADMIN)
def update_product_images():
    """Update existing product images to correct URLs."""
    products = Product.query.all()
    updated = 0
    
    for product in products:
        if product.sku == "TEE-001" and product.color == "White":
            product.image_url = "https://images.pexels.com/photos/996329/pexels-photo-996329.jpeg?auto=compress&cs=tinysrgb&w=400&h=500&fit=crop"
            updated += 1
        elif product.sku == "JNS-001" and product.color == "Blue":
            product.image_url = "https://images.pexels.com/photos/1598507/pexels-photo-1598507.jpeg?auto=compress&cs=tinysrgb&w=400&h=500&fit=crop"
            updated += 1
        elif product.sku == "JKT-001" and product.color == "Black":
            product.image_url = "https://images.pexels.com/photos/1040945/pexels-photo-1040945.jpeg?auto=compress&cs=tinysrgb&w=400&h=500&fit=crop"
            updated += 1
    
    db.session.commit()
    return f"Updated {updated} product images. <a href='/admin/dashboard'>Go to Dashboard</a>"


if __name__ == "__main__":
    app.run(debug=True)

# Image references for clothing items
# T-Shirt: static/images/white-tshirt.jpg
# Jeans: static/images/blue-jeans.jpg
# Jacket: static/images/black-winter-jacket.jpg
