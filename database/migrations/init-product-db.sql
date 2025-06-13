-- ============================================================================
-- Brain2Gain Product Service Database Schema
-- Bounded Context: Product Catalog & Pricing
-- ============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- CATEGORIES - Product categorization
-- ============================================================================
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    seo_title VARCHAR(160),
    seo_description VARCHAR(320),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BRANDS - Product brands/manufacturers
-- ============================================================================
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    logo_url TEXT,
    website_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCTS - Main product catalog
-- ============================================================================
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    short_description TEXT,
    
    -- Categorization
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    brand_id UUID REFERENCES brands(id) ON DELETE SET NULL,
    
    -- Pricing
    price DECIMAL(10, 2) NOT NULL,
    compare_price DECIMAL(10, 2),
    cost_price DECIMAL(10, 2),
    
    -- Physical attributes
    weight DECIMAL(8, 3),
    weight_unit VARCHAR(10) DEFAULT 'kg',
    dimensions JSONB, -- {length, width, height, unit}
    
    -- Inventory reference (actual stock handled by inventory service)
    track_inventory BOOLEAN DEFAULT true,
    
    -- Status and visibility
    status VARCHAR(20) DEFAULT 'draft',
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    
    -- SEO
    seo_title VARCHAR(160),
    seo_description VARCHAR(320),
    
    -- Metadata
    tags TEXT[],
    attributes JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT products_status_check CHECK (status IN ('draft', 'active', 'archived')),
    CONSTRAINT products_price_positive CHECK (price >= 0),
    CONSTRAINT products_compare_price_check CHECK (compare_price IS NULL OR compare_price >= price),
    CONSTRAINT products_weight_positive CHECK (weight IS NULL OR weight >= 0)
);

-- ============================================================================
-- PRODUCT VARIANTS - Size, flavor, etc.
-- ============================================================================
CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    -- Variant-specific pricing
    price DECIMAL(10, 2),
    compare_price DECIMAL(10, 2),
    cost_price DECIMAL(10, 2),
    
    -- Variant attributes (size, color, flavor, etc.)
    attributes JSONB DEFAULT '{}',
    
    -- Physical attributes
    weight DECIMAL(8, 3),
    weight_unit VARCHAR(10) DEFAULT 'kg',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT product_variants_price_positive CHECK (price IS NULL OR price >= 0)
);

-- ============================================================================
-- PRODUCT IMAGES
-- ============================================================================
CREATE TABLE product_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_id UUID REFERENCES product_variants(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    alt_text VARCHAR(255),
    sort_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRODUCT ATTRIBUTES - Dynamic attributes
-- ============================================================================
CREATE TABLE product_attribute_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE product_attributes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES product_attribute_groups(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    attribute_type VARCHAR(20) DEFAULT 'text',
    is_required BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    
    -- Constraints
    CONSTRAINT product_attributes_type_check CHECK (
        attribute_type IN ('text', 'number', 'boolean', 'select', 'multiselect', 'date')
    )
);

CREATE TABLE product_attribute_values (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    attribute_id UUID NOT NULL REFERENCES product_attributes(id) ON DELETE CASCADE,
    value TEXT NOT NULL,
    
    -- Constraints
    CONSTRAINT product_attribute_values_unique UNIQUE(product_id, attribute_id)
);

-- ============================================================================
-- PRICING RULES - Dynamic pricing, discounts
-- ============================================================================
CREATE TABLE pricing_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(20) NOT NULL,
    
    -- Conditions
    conditions JSONB NOT NULL DEFAULT '{}',
    
    -- Actions
    discount_type VARCHAR(20), -- percentage, fixed, buy_x_get_y
    discount_value DECIMAL(10, 2),
    
    -- Applicability
    applies_to VARCHAR(20) DEFAULT 'products', -- products, categories, collections
    target_ids UUID[],
    
    -- Date range
    starts_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage limits
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    usage_limit_per_customer INTEGER,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT pricing_rules_type_check CHECK (rule_type IN ('discount', 'promotion', 'bulk', 'tiered')),
    CONSTRAINT pricing_rules_discount_type_check CHECK (
        discount_type IN ('percentage', 'fixed', 'buy_x_get_y', 'free_shipping')
    ),
    CONSTRAINT pricing_rules_dates_check CHECK (starts_at IS NULL OR ends_at IS NULL OR starts_at < ends_at)
);

-- ============================================================================
-- PRODUCT COLLECTIONS - Curated product groups
-- ============================================================================
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    image_url TEXT,
    
    -- Collection type and rules
    collection_type VARCHAR(20) DEFAULT 'manual',
    conditions JSONB, -- For automated collections
    
    -- SEO
    seo_title VARCHAR(160),
    seo_description VARCHAR(320),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT collections_type_check CHECK (collection_type IN ('manual', 'automated'))
);

CREATE TABLE collection_products (
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    PRIMARY KEY (collection_id, product_id)
);

-- ============================================================================
-- PRODUCT REVIEWS (basic structure, detailed reviews in separate service)
-- ============================================================================
CREATE TABLE product_reviews_summary (
    product_id UUID PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    total_reviews INTEGER DEFAULT 0,
    average_rating DECIMAL(3, 2) DEFAULT 0,
    rating_distribution JSONB DEFAULT '{"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES for performance
-- ============================================================================

-- Categories indexes
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_is_active ON categories(is_active);

-- Brands indexes
CREATE INDEX idx_brands_slug ON brands(slug);
CREATE INDEX idx_brands_is_active ON brands(is_active);

-- Products indexes
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_products_is_featured ON products(is_featured);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_created_at ON products(created_at);

-- Full-text search indexes
CREATE INDEX idx_products_name_gin ON products USING gin(name gin_trgm_ops);
CREATE INDEX idx_products_description_gin ON products USING gin(description gin_trgm_ops);
CREATE INDEX idx_products_tags_gin ON products USING gin(tags);

-- Product variants indexes
CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_product_variants_sku ON product_variants(sku);
CREATE INDEX idx_product_variants_is_active ON product_variants(is_active);

-- Product images indexes
CREATE INDEX idx_product_images_product_id ON product_images(product_id);
CREATE INDEX idx_product_images_variant_id ON product_images(variant_id);
CREATE INDEX idx_product_images_is_primary ON product_images(is_primary);

-- Collections indexes
CREATE INDEX idx_collections_slug ON collections(slug);
CREATE INDEX idx_collections_is_active ON collections(is_active);
CREATE INDEX idx_collections_type ON collections(collection_type);

-- ============================================================================
-- TRIGGERS for updated_at
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
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_variants_updated_at BEFORE UPDATE ON product_variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS for common queries
-- ============================================================================

-- Product catalog view with all related data
CREATE VIEW product_catalog AS
SELECT 
    p.id,
    p.name,
    p.slug,
    p.sku,
    p.description,
    p.short_description,
    p.price,
    p.compare_price,
    p.weight,
    p.status,
    p.is_active,
    p.is_featured,
    p.created_at,
    p.published_at,
    
    -- Category info
    c.name as category_name,
    c.slug as category_slug,
    
    -- Brand info
    b.name as brand_name,
    b.slug as brand_slug,
    
    -- Image info
    (
        SELECT json_agg(
            json_build_object(
                'url', url,
                'alt_text', alt_text,
                'is_primary', is_primary
            ) ORDER BY sort_order
        )
        FROM product_images pi 
        WHERE pi.product_id = p.id
    ) as images,
    
    -- Variant count
    (
        SELECT COUNT(*) 
        FROM product_variants pv 
        WHERE pv.product_id = p.id AND pv.is_active = true
    ) as variant_count,
    
    -- Review summary
    COALESCE(prs.total_reviews, 0) as total_reviews,
    COALESCE(prs.average_rating, 0) as average_rating

FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id
LEFT JOIN product_reviews_summary prs ON p.id = prs.product_id
WHERE p.is_active = true;

-- Active products with variants
CREATE VIEW products_with_variants AS
SELECT 
    p.*,
    json_agg(
        json_build_object(
            'id', pv.id,
            'sku', pv.sku,
            'name', pv.name,
            'price', pv.price,
            'attributes', pv.attributes,
            'is_active', pv.is_active
        ) ORDER BY pv.sort_order
    ) FILTER (WHERE pv.id IS NOT NULL) as variants
FROM products p
LEFT JOIN product_variants pv ON p.id = pv.product_id AND pv.is_active = true
WHERE p.is_active = true
GROUP BY p.id;

-- ============================================================================
-- FUNCTIONS for common operations
-- ============================================================================

-- Function to calculate product final price with discounts
CREATE OR REPLACE FUNCTION calculate_product_price(
    p_product_id UUID,
    p_variant_id UUID DEFAULT NULL,
    p_quantity INTEGER DEFAULT 1
) RETURNS TABLE(
    base_price DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    final_price DECIMAL(10,2),
    applied_rules JSON
) AS $$
DECLARE
    v_base_price DECIMAL(10,2);
    v_discount_amount DECIMAL(10,2) := 0;
    v_applied_rules JSON := '[]'::json;
BEGIN
    -- Get base price
    IF p_variant_id IS NOT NULL THEN
        SELECT COALESCE(pv.price, p.price) INTO v_base_price
        FROM products p
        LEFT JOIN product_variants pv ON pv.id = p_variant_id
        WHERE p.id = p_product_id;
    ELSE
        SELECT price INTO v_base_price
        FROM products
        WHERE id = p_product_id;
    END IF;
    
    -- TODO: Apply pricing rules logic here
    -- For now, return base price
    
    RETURN QUERY SELECT 
        v_base_price,
        v_discount_amount,
        v_base_price - v_discount_amount,
        v_applied_rules;
END;
$$ LANGUAGE plpgsql;

-- Function to update product reviews summary
CREATE OR REPLACE FUNCTION update_product_reviews_summary(
    p_product_id UUID,
    p_rating INTEGER,
    p_operation VARCHAR DEFAULT 'add' -- 'add' or 'remove'
) RETURNS VOID AS $$
DECLARE
    v_rating_key TEXT := p_rating::TEXT;
    v_distribution JSONB;
BEGIN
    -- Ensure summary record exists
    INSERT INTO product_reviews_summary (product_id)
    VALUES (p_product_id)
    ON CONFLICT (product_id) DO NOTHING;
    
    -- Get current distribution
    SELECT rating_distribution INTO v_distribution
    FROM product_reviews_summary
    WHERE product_id = p_product_id;
    
    -- Update distribution
    IF p_operation = 'add' THEN
        UPDATE product_reviews_summary
        SET 
            total_reviews = total_reviews + 1,
            rating_distribution = jsonb_set(
                rating_distribution,
                ARRAY[v_rating_key],
                ((rating_distribution->>v_rating_key)::INTEGER + 1)::TEXT::jsonb
            ),
            last_updated = CURRENT_TIMESTAMP
        WHERE product_id = p_product_id;
    ELSE
        UPDATE product_reviews_summary
        SET 
            total_reviews = GREATEST(0, total_reviews - 1),
            rating_distribution = jsonb_set(
                rating_distribution,
                ARRAY[v_rating_key],
                GREATEST(0, (rating_distribution->>v_rating_key)::INTEGER - 1)::TEXT::jsonb
            ),
            last_updated = CURRENT_TIMESTAMP
        WHERE product_id = p_product_id;
    END IF;
    
    -- Recalculate average rating
    UPDATE product_reviews_summary
    SET average_rating = (
        (rating_distribution->>'1')::INTEGER * 1 +
        (rating_distribution->>'2')::INTEGER * 2 +
        (rating_distribution->>'3')::INTEGER * 3 +
        (rating_distribution->>'4')::INTEGER * 4 +
        (rating_distribution->>'5')::INTEGER * 5
    )::DECIMAL / GREATEST(1, total_reviews)
    WHERE product_id = p_product_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Default categories
INSERT INTO categories (name, slug, description) VALUES
    ('Proteínas', 'proteinas', 'Suplementos proteicos para el desarrollo muscular'),
    ('Creatinas', 'creatinas', 'Suplementos de creatina para fuerza y potencia'),
    ('Pre-Entrenos', 'pre-entrenos', 'Suplementos pre-entreno para energía'),
    ('Vitaminas', 'vitaminas', 'Vitaminas y minerales esenciales'),
    ('Quemadores', 'quemadores', 'Suplementos para la quema de grasa');

-- Default brands
INSERT INTO brands (name, slug, description) VALUES
    ('Optimum Nutrition', 'optimum-nutrition', 'Líder mundial en suplementos deportivos'),
    ('MuscleTech', 'muscletech', 'Innovación en nutrición deportiva'),
    ('BSN', 'bsn', 'Suplementos de alta calidad'),
    ('Dymatize', 'dymatize', 'Nutrición deportiva de élite');

-- Attribute groups
INSERT INTO product_attribute_groups (name, display_name) VALUES
    ('nutritional', 'Información Nutricional'),
    ('physical', 'Características Físicas'),
    ('usage', 'Modo de Uso');

-- Basic attributes
INSERT INTO product_attributes (group_id, name, display_name, attribute_type) VALUES
    ((SELECT id FROM product_attribute_groups WHERE name = 'nutritional'), 'protein_per_serving', 'Proteína por Porción', 'text'),
    ((SELECT id FROM product_attribute_groups WHERE name = 'nutritional'), 'servings_per_container', 'Porciones por Envase', 'number'),
    ((SELECT id FROM product_attribute_groups WHERE name = 'physical'), 'flavor', 'Sabor', 'select'),
    ((SELECT id FROM product_attribute_groups WHERE name = 'physical'), 'size', 'Tamaño', 'select'),
    ((SELECT id FROM product_attribute_groups WHERE name = 'usage'), 'recommended_use', 'Uso Recomendado', 'text');

COMMENT ON DATABASE product_db IS 'Brain2Gain Product Service Database - Handles product catalog, pricing, and related data';