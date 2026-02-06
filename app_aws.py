from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import boto3
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from botocore.exceptions import ClientError

# --------------------------------------------------
# Flask App Configuration
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-for-aws")

# --------------------------------------------------
# AWS Configuration
# --------------------------------------------------
REGION = "us-east-1"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

# --------------------------------------------------
# DynamoDB Tables (MUST be created manually in AWS)
# --------------------------------------------------
users_table = dynamodb.Table("stylelane-users")
stores_table = dynamodb.Table("stylelane-stores")
products_table = dynamodb.Table("stylelane-products")
inventory_table = dynamodb.Table("stylelane-inventory")
sales_table = dynamodb.Table("stylelane-sales")
restock_table = dynamodb.Table("stylelane-restock-requests")
shipments_table = dynamodb.Table("stylelane-shipments")

# --------------------------------------------------
# SNS Topic ARN
# (Paste real ARN during deployment OR use env variable)
# --------------------------------------------------
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:122610488902:stylelane_aws_project")

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def send_notification(subject, message):
    if not SNS_TOPIC_ARN:
        return
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except ClientError as e:
        print("SNS Error:", e)


def current_user():
    return session.get("user_id"), session.get("user_role")


# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        role = session.get("user_role")
        if role == "admin":
            return redirect(url_for("admin_dashboard"))
        if role == "manager":
            return redirect(url_for("manager_dashboard"))
        if role == "supplier":
            return redirect(url_for("supplier_dashboard"))
    return redirect(url_for("login"))


# --------------------------------------------------
# Authentication
# --------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password", "danger")
            return render_template("login.html")

        try:
            response = users_table.scan(
                FilterExpression="username = :u",
                ExpressionAttributeValues={":u": username}
            )

            items = response.get("Items", [])
            if items and check_password_hash(items[0].get("password", ""), password):
                session["user_id"] = items[0]["id"]
                session["user_role"] = items[0].get("role", "")
                flash("Login successful", "success")
                return redirect(url_for("index"))

            flash("Invalid credentials", "danger")
        except Exception as e:
            print(f"Login error: {e}")
            flash("Error connecting to database. Please check AWS credentials.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# --------------------------------------------------
# Admin Dashboard
# --------------------------------------------------
@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if session.get("user_role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "create_store":
            store_id = str(uuid.uuid4())
            stores_table.put_item(Item={
                "id": store_id,
                "name": request.form["name"],
                "location": request.form["location"]
            })
            flash("Store created", "success")

        elif action == "create_manager":
            user_id = str(uuid.uuid4())
            users_table.put_item(Item={
                "id": user_id,
                "username": request.form["username"],
                "password": generate_password_hash(request.form["password"]),
                "role": "manager",
                "store_id": request.form["store_id"]
            })
            flash("Manager created", "success")

    stores = stores_table.scan().get("Items", [])
    managers = users_table.scan(
        FilterExpression="role = :r",
        ExpressionAttributeValues={":r": "manager"}
    ).get("Items", [])

    return render_template(
        "admin_dashboard.html",
        stores=stores,
        managers=managers
    )


# --------------------------------------------------
# Manager Dashboard
# --------------------------------------------------
@app.route("/manager/dashboard", methods=["GET", "POST"])
def manager_dashboard():
    if session.get("user_role") != "manager":
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = users_table.get_item(Key={"id": user_id}).get("Item")

    store_id = user.get("store_id")
    inventory = inventory_table.scan(
        FilterExpression="store_id = :s",
        ExpressionAttributeValues={":s": store_id}
    ).get("Items", [])

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_product":
            product_id = str(uuid.uuid4())
            products_table.put_item(Item={
                "id": product_id,
                "name": request.form["name"],
                "sku": request.form["sku"],
                "price": float(request.form["price"])
            })

            inventory_table.put_item(Item={
                "id": str(uuid.uuid4()),
                "store_id": store_id,
                "product_id": product_id,
                "quantity": 0,
                "low_stock_threshold": 5
            })
            flash("Product added", "success")

        elif action == "update_quantity":
            inventory_table.update_item(
                Key={"id": request.form["inventory_id"]},
                UpdateExpression="SET quantity = :q",
                ExpressionAttributeValues={":q": int(request.form["quantity"])}
            )
            flash("Quantity updated", "success")

    return render_template("manager_dashboard.html", inventory=inventory)


# --------------------------------------------------
# Supplier Dashboard
# --------------------------------------------------
@app.route("/supplier/dashboard", methods=["GET", "POST"])
def supplier_dashboard():
    if session.get("user_role") != "supplier":
        return redirect(url_for("login"))

    requests = restock_table.scan().get("Items", [])

    if request.method == "POST":
        req_id = request.form["request_id"]
        restock_table.update_item(
            Key={"id": req_id},
            UpdateExpression="SET #s = :v",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":v": "approved"}
        )

        send_notification(
            "Restock Approved",
            f"Restock request {req_id} approved"
        )

    return render_template("supplier_dashboard.html", requests=requests)


# --------------------------------------------------
# App Runner
# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
