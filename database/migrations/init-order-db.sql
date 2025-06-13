-- ============================================================================
-- Brain2Gain Order Service Database Schema
-- Bounded Context: Order Processing & Management
-- ============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CUSTOMERS - Customer information (denormalized from auth service)
-- ============================================================================
CREATE TABLE customers (
    id UUID PRIMARY KEY, -- References users.id from auth service
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    
    -- Customer status
    status VARCHAR(20) DEFAULT 'active',
    is_verified BOOLEAN DEFAULT false,
    
    -- Customer metrics
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(12, 2) DEFAULT 0,
    average_order_value DECIMAL(10, 2) DEFAULT 0,
    
    -- Timestamps
    first_order_at TIMESTAMP WITH TIME ZONE,
    last_order_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT customers_status_check CHECK (status IN ('active', 'inactive', 'blocked'))
);

-- ============================================================================
-- ADDRESSES - Customer addresses
-- ============================================================================
CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Address details
    type VARCHAR(20) DEFAULT 'shipping',
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(100),
    address_line_1 VARCHAR(255) NOT NULL,
    address_line_2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) NOT NULL,
    
    -- Address flags
    is_default BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT addresses_type_check CHECK (type IN ('billing', 'shipping', 'both'))
);

-- ============================================================================
-- ORDERS - Main orders table
-- ============================================================================
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Customer information
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    customer_email VARCHAR(255) NOT NULL,
    
    -- Order status and workflow
    status VARCHAR(30) DEFAULT 'pending',
    fulfillment_status VARCHAR(30) DEFAULT 'unfulfilled',
    payment_status VARCHAR(30) DEFAULT 'pending',
    
    -- Financial information
    currency VARCHAR(3) DEFAULT 'USD',
    subtotal DECIMAL(12, 2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(12, 2) DEFAULT 0,
    shipping_amount DECIMAL(12, 2) DEFAULT 0,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    
    -- Addresses (denormalized for order history)
    billing_address JSONB,
    shipping_address JSONB,
    
    -- Shipping information
    shipping_method VARCHAR(100),
    tracking_number VARCHAR(100),
    tracking_url TEXT,
    
    -- Order metadata
    notes TEXT,
    tags TEXT[],
    source VARCHAR(50) DEFAULT 'web',
    
    -- Important dates
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    shipped_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT orders_status_check CHECK (status IN (
        'pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'
    )),
    CONSTRAINT orders_fulfillment_status_check CHECK (fulfillment_status IN (
        'unfulfilled', 'partial', 'fulfilled', 'cancelled'
    )),
    CONSTRAINT orders_payment_status_check CHECK (payment_status IN (
        'pending', 'authorized', 'paid', 'partially_paid', 'refunded', 'partially_refunded', 'failed'
    )),
    CONSTRAINT orders_amounts_positive CHECK (
        subtotal >= 0 AND tax_amount >= 0 AND shipping_amount >= 0 AND 
        discount_amount >= 0 AND total_amount >= 0
    )
);

-- ============================================================================
-- ORDER ITEMS - Items within orders
-- ============================================================================
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Product information (denormalized for order history)
    product_id UUID NOT NULL,
    variant_id UUID,
    sku VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    variant_name VARCHAR(255),
    
    -- Pricing
    unit_price DECIMAL(10, 2) NOT NULL,
    compare_price DECIMAL(10, 2),
    quantity INTEGER NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    
    -- Product attributes at time of order
    product_attributes JSONB DEFAULT '{}',
    
    -- Fulfillment
    fulfillment_status VARCHAR(20) DEFAULT 'unfulfilled',
    fulfilled_quantity INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT order_items_quantity_positive CHECK (quantity > 0),
    CONSTRAINT order_items_prices_positive CHECK (unit_price >= 0 AND total_price >= 0),
    CONSTRAINT order_items_fulfillment_status_check CHECK (fulfillment_status IN (
        'unfulfilled', 'fulfilled', 'cancelled'
    )),
    CONSTRAINT order_items_fulfilled_quantity_check CHECK (fulfilled_quantity >= 0 AND fulfilled_quantity <= quantity)
);

-- ============================================================================
-- ORDER DISCOUNTS - Applied discounts
-- ============================================================================
CREATE TABLE order_discounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Discount information
    code VARCHAR(100),
    discount_type VARCHAR(20) NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL,
    
    -- Application scope
    applies_to VARCHAR(20) DEFAULT 'order',
    target_item_ids UUID[],
    
    -- Metadata
    rule_id UUID, -- Reference to pricing rule
    description TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT order_discounts_type_check CHECK (discount_type IN ('percentage', 'fixed', 'shipping')),
    CONSTRAINT order_discounts_applies_to_check CHECK (applies_to IN ('order', 'items', 'shipping'))
);

-- ============================================================================
-- ORDER PAYMENTS - Payment transactions
-- ============================================================================
CREATE TABLE order_payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Payment details
    payment_method VARCHAR(50) NOT NULL,
    payment_provider VARCHAR(50),
    transaction_id VARCHAR(255),
    
    -- Amount information
    currency VARCHAR(3) DEFAULT 'USD',
    amount DECIMAL(12, 2) NOT NULL,
    
    -- Payment status
    status VARCHAR(20) DEFAULT 'pending',
    
    -- Provider response
    provider_response JSONB,
    failure_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT order_payments_status_check CHECK (status IN (
        'pending', 'processing', 'successful', 'failed', 'cancelled', 'refunded'
    )),
    CONSTRAINT order_payments_amount_positive CHECK (amount > 0)
);

-- ============================================================================
-- ORDER FULFILLMENTS - Shipping and fulfillment tracking
-- ============================================================================
CREATE TABLE order_fulfillments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Fulfillment details
    status VARCHAR(20) DEFAULT 'pending',
    tracking_number VARCHAR(100),
    tracking_url TEXT,
    carrier VARCHAR(100),
    service VARCHAR(100),
    
    -- Shipping address (can be different from order shipping address)
    shipping_address JSONB,
    
    -- Items being fulfilled
    fulfillment_items JSONB, -- Array of {order_item_id, quantity}
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    shipped_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT order_fulfillments_status_check CHECK (status IN (
        'pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned'
    ))
);

-- ============================================================================
-- ORDER HISTORY - Audit trail for order changes
-- ============================================================================
CREATE TABLE order_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Change information
    action VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    
    -- User who made the change
    changed_by UUID, -- Reference to user from auth service
    change_reason TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SHOPPING CARTS - Customer shopping carts
-- ============================================================================
CREATE TABLE shopping_carts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    session_id VARCHAR(255), -- For guest carts
    
    -- Cart metadata
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT shopping_carts_customer_or_session CHECK (
        (customer_id IS NOT NULL AND session_id IS NULL) OR
        (customer_id IS NULL AND session_id IS NOT NULL)
    )
);

-- ============================================================================
-- CART ITEMS - Items in shopping carts
-- ============================================================================
CREATE TABLE cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id UUID NOT NULL REFERENCES shopping_carts(id) ON DELETE CASCADE,
    
    -- Product information
    product_id UUID NOT NULL,
    variant_id UUID,
    sku VARCHAR(100) NOT NULL,
    
    -- Quantity and pricing
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT cart_items_quantity_positive CHECK (quantity > 0),
    CONSTRAINT cart_items_product_variant_unique UNIQUE(cart_id, product_id, variant_id)
);

-- ============================================================================
-- INDEXES for performance
-- ============================================================================

-- Customers indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_total_orders ON customers(total_orders);
CREATE INDEX idx_customers_total_spent ON customers(total_spent);

-- Addresses indexes
CREATE INDEX idx_addresses_customer_id ON addresses(customer_id);
CREATE INDEX idx_addresses_type ON addresses(type);
CREATE INDEX idx_addresses_is_default ON addresses(is_default);

-- Orders indexes
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_fulfillment_status ON orders(fulfillment_status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_total_amount ON orders(total_amount);
CREATE INDEX idx_orders_customer_email ON orders(customer_email);

-- Order items indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_sku ON order_items(sku);
CREATE INDEX idx_order_items_fulfillment_status ON order_items(fulfillment_status);

-- Order payments indexes
CREATE INDEX idx_order_payments_order_id ON order_payments(order_id);
CREATE INDEX idx_order_payments_status ON order_payments(status);
CREATE INDEX idx_order_payments_transaction_id ON order_payments(transaction_id);

-- Shopping carts indexes
CREATE INDEX idx_shopping_carts_customer_id ON shopping_carts(customer_id);
CREATE INDEX idx_shopping_carts_session_id ON shopping_carts(session_id);
CREATE INDEX idx_shopping_carts_expires_at ON shopping_carts(expires_at);

-- Cart items indexes
CREATE INDEX idx_cart_items_cart_id ON cart_items(cart_id);
CREATE INDEX idx_cart_items_product_id ON cart_items(product_id);

-- ============================================================================
-- TRIGGERS for updated_at and calculations
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_addresses_updated_at BEFORE UPDATE ON addresses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shopping_carts_updated_at BEFORE UPDATE ON shopping_carts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate order totals
CREATE OR REPLACE FUNCTION calculate_order_totals()
RETURNS TRIGGER AS $$
BEGIN
    -- Recalculate subtotal from order items
    NEW.subtotal := (
        SELECT COALESCE(SUM(total_price), 0)
        FROM order_items
        WHERE order_id = NEW.id
    );
    
    -- Calculate total amount
    NEW.total_amount := NEW.subtotal + NEW.tax_amount + NEW.shipping_amount - NEW.discount_amount;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger for order total calculation
CREATE TRIGGER calculate_order_totals_trigger BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION calculate_order_totals();

-- Function to update customer metrics
CREATE OR REPLACE FUNCTION update_customer_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update customer order count and spending
    IF TG_OP = 'INSERT' AND NEW.status = 'confirmed' THEN
        UPDATE customers
        SET 
            total_orders = total_orders + 1,
            total_spent = total_spent + NEW.total_amount,
            last_order_at = NEW.created_at,
            first_order_at = COALESCE(first_order_at, NEW.created_at)
        WHERE id = NEW.customer_id;
        
        -- Update average order value
        UPDATE customers
        SET average_order_value = total_spent / GREATEST(1, total_orders)
        WHERE id = NEW.customer_id;
    END IF;
    
    IF TG_OP = 'UPDATE' AND OLD.status != 'confirmed' AND NEW.status = 'confirmed' THEN
        UPDATE customers
        SET 
            total_orders = total_orders + 1,
            total_spent = total_spent + NEW.total_amount,
            last_order_at = NEW.updated_at
        WHERE id = NEW.customer_id;
        
        -- Update average order value
        UPDATE customers
        SET average_order_value = total_spent / GREATEST(1, total_orders)
        WHERE id = NEW.customer_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Apply trigger for customer metrics
CREATE TRIGGER update_customer_metrics_trigger 
    AFTER INSERT OR UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_customer_metrics();

-- ============================================================================
-- VIEWS for common queries
-- ============================================================================

-- Order summary view
CREATE VIEW order_summary AS
SELECT 
    o.id,
    o.order_number,
    o.customer_email,
    o.status,
    o.payment_status,
    o.fulfillment_status,
    o.total_amount,
    o.currency,
    o.created_at,
    o.confirmed_at,
    
    -- Customer info
    c.first_name as customer_first_name,
    c.last_name as customer_last_name,
    
    -- Item count
    (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id = o.id) as item_count,
    
    -- Payment info
    (SELECT status FROM order_payments op WHERE op.order_id = o.id ORDER BY created_at DESC LIMIT 1) as latest_payment_status

FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id;

-- Customer order history
CREATE VIEW customer_order_history AS
SELECT 
    c.id as customer_id,
    c.email,
    c.first_name,
    c.last_name,
    c.total_orders,
    c.total_spent,
    c.average_order_value,
    
    -- Recent orders
    json_agg(
        json_build_object(
            'order_id', o.id,
            'order_number', o.order_number,
            'status', o.status,
            'total_amount', o.total_amount,
            'created_at', o.created_at
        ) ORDER BY o.created_at DESC
    ) FILTER (WHERE o.id IS NOT NULL) as recent_orders

FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id;

-- ============================================================================
-- FUNCTIONS for common operations
-- ============================================================================

-- Function to generate order number
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TEXT AS $$
DECLARE
    order_number TEXT;
    counter INTEGER;
BEGIN
    -- Get today's date
    SELECT INTO counter COUNT(*) + 1
    FROM orders
    WHERE DATE(created_at) = CURRENT_DATE;
    
    -- Format: BG-YYYYMMDD-XXXX
    order_number := 'BG-' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' || LPAD(counter::TEXT, 4, '0');
    
    RETURN order_number;
END;
$$ LANGUAGE plpgsql;

-- Function to create order from cart
CREATE OR REPLACE FUNCTION create_order_from_cart(
    p_cart_id UUID,
    p_customer_email VARCHAR,
    p_billing_address JSONB,
    p_shipping_address JSONB,
    p_shipping_method VARCHAR DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_order_id UUID;
    v_customer_id UUID;
    cart_item RECORD;
BEGIN
    -- Get customer ID
    SELECT id INTO v_customer_id FROM customers WHERE email = p_customer_email;
    
    -- Create order
    INSERT INTO orders (
        order_number,
        customer_id,
        customer_email,
        billing_address,
        shipping_address,
        shipping_method,
        status
    ) VALUES (
        generate_order_number(),
        v_customer_id,
        p_customer_email,
        p_billing_address,
        p_shipping_address,
        p_shipping_method,
        'pending'
    ) RETURNING id INTO v_order_id;
    
    -- Add cart items to order
    FOR cart_item IN
        SELECT ci.*, sc.customer_id
        FROM cart_items ci
        JOIN shopping_carts sc ON ci.cart_id = sc.id
        WHERE ci.cart_id = p_cart_id
    LOOP
        INSERT INTO order_items (
            order_id,
            product_id,
            variant_id,
            sku,
            product_name,
            quantity,
            unit_price,
            total_price
        ) VALUES (
            v_order_id,
            cart_item.product_id,
            cart_item.variant_id,
            cart_item.sku,
            'Product Name', -- TODO: Get from product service
            cart_item.quantity,
            cart_item.unit_price,
            cart_item.quantity * cart_item.unit_price
        );
    END LOOP;
    
    -- Clear cart
    DELETE FROM cart_items WHERE cart_id = p_cart_id;
    DELETE FROM shopping_carts WHERE id = p_cart_id;
    
    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update order status with history
CREATE OR REPLACE FUNCTION update_order_status(
    p_order_id UUID,
    p_new_status VARCHAR,
    p_changed_by UUID DEFAULT NULL,
    p_reason TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_old_status VARCHAR;
BEGIN
    -- Get current status
    SELECT status INTO v_old_status FROM orders WHERE id = p_order_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Update order status
    UPDATE orders 
    SET 
        status = p_new_status,
        confirmed_at = CASE WHEN p_new_status = 'confirmed' THEN CURRENT_TIMESTAMP ELSE confirmed_at END,
        shipped_at = CASE WHEN p_new_status = 'shipped' THEN CURRENT_TIMESTAMP ELSE shipped_at END,
        delivered_at = CASE WHEN p_new_status = 'delivered' THEN CURRENT_TIMESTAMP ELSE delivered_at END,
        cancelled_at = CASE WHEN p_new_status = 'cancelled' THEN CURRENT_TIMESTAMP ELSE cancelled_at END
    WHERE id = p_order_id;
    
    -- Add to history
    INSERT INTO order_history (
        order_id,
        action,
        field_name,
        old_value,
        new_value,
        changed_by,
        change_reason
    ) VALUES (
        p_order_id,
        'status_change',
        'status',
        v_old_status,
        p_new_status,
        p_changed_by,
        p_reason
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON DATABASE order_db IS 'Brain2Gain Order Service Database - Handles order processing, payments, and fulfillment';