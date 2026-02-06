"""
Test suite for app_aws.py using moto to mock AWS services
Run with: pytest test_app_aws.py -v
"""
import pytest
import boto3
from moto import mock_aws
from werkzeug.security import generate_password_hash
from decimal import Decimal
import sys
import os

# Set dummy AWS credentials for testing
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function", autouse=True)
def mock_aws_services():
    """Set up mocked AWS services - runs before each test"""
    with mock_aws():
        # Create DynamoDB tables
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Users table
        users_table = dynamodb.create_table(
            TableName="stylelane-users",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Stores table
        stores_table = dynamodb.create_table(
            TableName="stylelane-stores",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Products table
        products_table = dynamodb.create_table(
            TableName="stylelane-products",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Inventory table
        inventory_table = dynamodb.create_table(
            TableName="stylelane-inventory",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Sales table
        sales_table = dynamodb.create_table(
            TableName="stylelane-sales",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Restock requests table
        restock_table = dynamodb.create_table(
            TableName="stylelane-restock-requests",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Shipments table
        shipments_table = dynamodb.create_table(
            TableName="stylelane-shipments",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Create SNS topic
        sns_client = boto3.client("sns", region_name="us-east-1")
        topic_response = sns_client.create_topic(Name="stylelane-notifications")
        
        # Wait for tables to be ready
        users_table.wait_until_exists()
        stores_table.wait_until_exists()
        products_table.wait_until_exists()
        inventory_table.wait_until_exists()
        sales_table.wait_until_exists()
        restock_table.wait_until_exists()
        shipments_table.wait_until_exists()
        
        # Import app_aws after mocks are set up
        import importlib
        if 'app_aws' in sys.modules:
            importlib.reload(sys.modules['app_aws'])
        import app_aws
        
        # Set SNS topic ARN
        app_aws.SNS_TOPIC_ARN = topic_response["TopicArn"]
        
        yield {
            "users": users_table,
            "stores": stores_table,
            "products": products_table,
            "inventory": inventory_table,
            "sales": sales_table,
            "restock": restock_table,
            "shipments": shipments_table,
            "app": app_aws
        }


@pytest.fixture
def client(mock_aws_services):
    """Create a test client"""
    app = mock_aws_services["app"]
    app.app.config['TESTING'] = True
    app.app.config['SECRET_KEY'] = 'test-secret-key'
    return app.app.test_client()


@pytest.fixture
def aws_mock(mock_aws_services):
    """Alias for mock_aws_services"""
    return mock_aws_services


@pytest.fixture
def test_admin_user(aws_mock):
    """Create a test admin user"""
    import uuid
    user_id = str(uuid.uuid4())
    aws_mock["users"].put_item(Item={
        "id": user_id,
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "role": "admin"
    })
    return user_id


@pytest.fixture
def test_manager_user(aws_mock):
    """Create a test manager user with store"""
    import uuid
    # Create store first
    store_id = str(uuid.uuid4())
    aws_mock["stores"].put_item(Item={
        "id": store_id,
        "name": "Test Store",
        "location": "Test Location"
    })
    
    # Create manager
    manager_id = str(uuid.uuid4())
    aws_mock["users"].put_item(Item={
        "id": manager_id,
        "username": "manager1",
        "password": generate_password_hash("manager123"),
        "role": "manager",
        "store_id": store_id
    })
    return manager_id, store_id


@pytest.fixture
def test_supplier_user(aws_mock):
    """Create a test supplier user"""
    import uuid
    supplier_id = str(uuid.uuid4())
    aws_mock["users"].put_item(Item={
        "id": supplier_id,
        "username": "supplier1",
        "password": generate_password_hash("supplier123"),
        "role": "supplier"
    })
    return supplier_id


# ============================================================
# Authentication Tests
# ============================================================

def test_index_redirects_to_login_when_not_logged_in(client):
    """Test that index redirects to login when not authenticated"""
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.location


def test_login_page_loads(client):
    """Test that login page loads correctly"""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in" in response.data or b"Login" in response.data


def test_login_with_valid_credentials(client, aws_mock, test_admin_user):
    """Test login with valid credentials"""
    response = client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_login_with_invalid_credentials(client, aws_mock):
    """Test login with invalid credentials"""
    response = client.post("/login", data={
        "username": "wronguser",
        "password": "wrongpass"
    })
    
    assert response.status_code == 200
    assert b"Invalid credentials" in response.data or b"Invalid" in response.data


def test_logout(client, aws_mock, test_admin_user):
    """Test logout functionality"""
    # Login first
    client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    })
    
    # Logout
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200


# ============================================================
# Admin Dashboard Tests
# ============================================================

def test_admin_dashboard_requires_login(client):
    """Test that admin dashboard requires authentication"""
    response = client.get("/admin/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location


def test_admin_dashboard_requires_admin_role(client, aws_mock, test_manager_user):
    """Test that admin dashboard requires admin role"""
    # Login as manager
    client.post("/login", data={
        "username": "manager1",
        "password": "manager123"
    })
    
    # Try to access admin dashboard
    response = client.get("/admin/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location


def test_admin_can_create_store(client, aws_mock, test_admin_user):
    """Test admin can create a store"""
    # Login as admin
    client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    })
    
    # Create store
    response = client.post("/admin/dashboard", data={
        "action": "create_store",
        "name": "New Store",
        "location": "New Location"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Store created" in response.data or b"created" in response.data.lower()
    
    # Verify store was created
    stores = aws_mock["stores"].scan().get("Items", [])
    assert len(stores) > 0
    assert any(s.get("name") == "New Store" for s in stores)


def test_admin_can_create_manager(client, aws_mock, test_admin_user):
    """Test admin can create a manager"""
    import uuid
    
    # Create a store first
    store_id = str(uuid.uuid4())
    aws_mock["stores"].put_item(Item={
        "id": store_id,
        "name": "Test Store",
        "location": "Test Location"
    })
    
    # Login as admin
    client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    })
    
    # Create manager
    response = client.post("/admin/dashboard", data={
        "action": "create_manager",
        "username": "newmanager",
        "password": "newpass123",
        "store_id": store_id
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Manager created" in response.data or b"created" in response.data.lower()
    
    # Verify manager was created
    users = aws_mock["users"].scan(
        FilterExpression="username = :u",
        ExpressionAttributeValues={":u": "newmanager"}
    ).get("Items", [])
    
    assert len(users) > 0
    assert users[0].get("role") == "manager"


# ============================================================
# Manager Dashboard Tests
# ============================================================

def test_manager_dashboard_requires_login(client):
    """Test that manager dashboard requires authentication"""
    response = client.get("/manager/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location


def test_manager_can_add_product(client, aws_mock, test_manager_user):
    """Test manager can add a product"""
    manager_id, store_id = test_manager_user
    
    # Login as manager
    client.post("/login", data={
        "username": "manager1",
        "password": "manager123"
    })
    
    # Add product
    response = client.post("/manager/dashboard", data={
        "action": "add_product",
        "name": "Test Product",
        "sku": "TEST-001",
        "price": "29.99"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Product added" in response.data or b"added" in response.data.lower()
    
    # Verify product was created
    products = aws_mock["products"].scan().get("Items", [])
    assert len(products) > 0
    assert any(p.get("name") == "Test Product" for p in products)


def test_manager_can_update_inventory_quantity(client, aws_mock, test_manager_user):
    """Test manager can update inventory quantity"""
    import uuid
    manager_id, store_id = test_manager_user
    
    # Create a product and inventory item
    product_id = str(uuid.uuid4())
    aws_mock["products"].put_item(Item={
        "id": product_id,
        "name": "Test Product",
        "sku": "TEST-001",
        "price": Decimal("29.99")
    })
    
    inventory_id = str(uuid.uuid4())
    aws_mock["inventory"].put_item(Item={
        "id": inventory_id,
        "store_id": store_id,
        "product_id": product_id,
        "quantity": 10,
        "low_stock_threshold": 5
    })
    
    # Login as manager
    client.post("/login", data={
        "username": "manager1",
        "password": "manager123"
    })
    
    # Update quantity
    response = client.post("/manager/dashboard", data={
        "action": "update_quantity",
        "inventory_id": inventory_id,
        "quantity": "25"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Quantity updated" in response.data or b"updated" in response.data.lower()
    
    # Verify quantity was updated
    inventory = aws_mock["inventory"].get_item(Key={"id": inventory_id}).get("Item")
    assert inventory.get("quantity") == 25


# ============================================================
# Supplier Dashboard Tests
# ============================================================

def test_supplier_dashboard_requires_login(client):
    """Test that supplier dashboard requires authentication"""
    response = client.get("/supplier/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location


def test_supplier_can_approve_restock_request(client, aws_mock, test_supplier_user, test_manager_user):
    """Test supplier can approve restock request"""
    import uuid
    manager_id, store_id = test_manager_user
    
    # Create a product
    product_id = str(uuid.uuid4())
    aws_mock["products"].put_item(Item={
        "id": product_id,
        "name": "Test Product",
        "sku": "TEST-001",
        "price": Decimal("29.99")
    })
    
    # Create inventory
    inventory_id = str(uuid.uuid4())
    aws_mock["inventory"].put_item(Item={
        "id": inventory_id,
        "store_id": store_id,
        "product_id": product_id,
        "quantity": 2,
        "low_stock_threshold": 5
    })
    
    # Create restock request
    request_id = str(uuid.uuid4())
    aws_mock["restock"].put_item(Item={
        "id": request_id,
        "inventory_id": inventory_id,
        "store_id": store_id,
        "product_id": product_id,
        "quantity_requested": 20,
        "status": "pending",
        "manager_id": manager_id
    })
    
    # Login as supplier
    client.post("/login", data={
        "username": "supplier1",
        "password": "supplier123"
    })
    
    # Approve request
    response = client.post("/supplier/dashboard", data={
        "request_id": request_id
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify request was approved
    request = aws_mock["restock"].get_item(Key={"id": request_id}).get("Item")
    assert request.get("status") == "approved"


# ============================================================
# Integration Tests
# ============================================================

def test_full_workflow(client, aws_mock):
    """Test a complete workflow: login -> add product -> update inventory"""
    import uuid
    
    # Create admin user
    admin_id = str(uuid.uuid4())
    aws_mock["users"].put_item(Item={
        "id": admin_id,
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "role": "admin"
    })
    
    # Create store
    store_id = str(uuid.uuid4())
    aws_mock["stores"].put_item(Item={
        "id": store_id,
        "name": "Test Store",
        "location": "Test Location"
    })
    
    # Create manager
    manager_id = str(uuid.uuid4())
    aws_mock["users"].put_item(Item={
        "id": manager_id,
        "username": "manager1",
        "password": generate_password_hash("manager123"),
        "role": "manager",
        "store_id": store_id
    })
    
    # Login as manager
    login_response = client.post("/login", data={
        "username": "manager1",
        "password": "manager123"
    })
    assert login_response.status_code in [200, 302]
    
    # Add product
    product_response = client.post("/manager/dashboard", data={
        "action": "add_product",
        "name": "Workflow Product",
        "sku": "WF-001",
        "price": "49.99"
    }, follow_redirects=True)
    assert product_response.status_code == 200
    
    # Verify product exists
    products = aws_mock["products"].scan().get("Items", [])
    assert any(p.get("name") == "Workflow Product" for p in products)


# ============================================================
# Error Handling Tests
# ============================================================

def test_login_with_empty_fields(client):
    """Test login with empty username/password"""
    response = client.post("/login", data={
        "username": "",
        "password": ""
    })
    assert response.status_code == 200


def test_admin_dashboard_without_action(client, aws_mock, test_admin_user):
    """Test admin dashboard GET request"""
    client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    })
    
    response = client.get("/admin/dashboard")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
