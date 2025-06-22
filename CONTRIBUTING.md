# 🤝 Contributing to Brain2Gain

Thank you for your interest in contributing to Brain2Gain! This document provides guidelines and instructions for contributing to our sports supplements e-commerce platform.

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Microservices Guidelines](#microservices-guidelines)

## 🤖 Code of Conduct

### Our Pledge
We are committed to making participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards
- **Be respectful** and inclusive
- **Be collaborative** and help others learn
- **Be constructive** when giving feedback
- **Focus on what is best** for the community
- **Show empathy** towards other community members

## 🚀 Getting Started

### Prerequisites
1. **Development Environment**: Set up your local environment following our [Development Setup Guide](./docs/development/setup.md)
2. **Understanding the Architecture**: Review our [Microservices Architecture Plan](./docs/architecture/microservices-plan.md)
3. **Code Familiarity**: Familiarize yourself with our tech stack:
   - **Backend**: FastAPI, SQLModel, PostgreSQL
   - **Frontend**: React, TypeScript, TanStack Router
   - **Microservices**: Individual FastAPI services

### First-Time Setup
```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/brain2gain.git
cd brain2gain

# 3. Add upstream remote
git remote add upstream https://github.com/JazzDataSolutions/brain2gain.git

# 4. Set up development environment
make dev

# 5. Run tests to ensure everything works
make test
```

## 🔄 Development Process

### Branch Naming Convention
```bash
# Feature branches
feature/auth-service-improvements
feature/product-search-optimization

# Bug fixes
fix/cart-calculation-error
fix/auth-token-expiry

# Documentation
docs/api-documentation-update
docs/setup-guide-improvements

# Microservice-specific
service/auth-service/oauth2-integration
service/product-service/elasticsearch-search
```

### Commit Message Format
We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

# Examples
feat(auth): add OAuth2 Google integration
fix(product): resolve price calculation rounding error
docs(api): update authentication endpoints documentation
test(cart): add integration tests for checkout flow
refactor(inventory): optimize stock validation logic

# Breaking changes
feat(auth)!: migrate to new JWT token format

BREAKING CHANGE: JWT tokens now include additional claims
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, semicolons, etc)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes
- `perf`: Performance improvements
- `ci`: Continuous integration changes

## 📝 Coding Standards

### Python (Backend & Microservices)
```python
# Use ruff for linting and formatting
ruff check .
ruff format .

# Type checking with mypy
mypy app/

# Standards:
# - Use type hints everywhere
# - Follow PEP 8 naming conventions
# - Use descriptive variable names
# - Add docstrings for all public functions
# - Maximum line length: 88 characters

# Example:
async def create_product(
    session: AsyncSession,
    product_data: ProductCreate
) -> Product:
    """
    Create a new product in the database.
    
    Args:
        session: Database session
        product_data: Product creation data
        
    Returns:
        Created product instance
        
    Raises:
        ValueError: If product validation fails
    """
    # Implementation here
```

### TypeScript (Frontend)
```typescript
// Use Biome for linting and formatting
npm run lint
npm run format

// Standards:
// - Use strict TypeScript configuration
// - Prefer interfaces over types for object shapes
// - Use descriptive component and function names
// - Add JSDoc comments for complex functions
// - Use React functional components with hooks

// Example:
interface ProductCardProps {
  product: Product;
  onAddToCart: (productId: string) => void;
  isLoading?: boolean;
}

/**
 * Product card component displaying product information
 * and add to cart functionality.
 */
export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onAddToCart,
  isLoading = false
}) => {
  // Implementation here
};
```

### File Organization
```
# Backend/Microservices Structure
services/
├── auth-service/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── models.py         # Pydantic models
│   │   ├── service.py        # Business logic
│   │   ├── config.py         # Configuration
│   │   └── database.py       # Database connection
│   ├── tests/                # Service-specific tests
│   ├── Dockerfile
│   └── requirements.txt

# Frontend Structure
frontend/src/
├── components/
│   ├── Auth/                 # Authentication components
│   ├── Products/             # Product-related components
│   └── Common/               # Shared components
├── services/                 # API clients for microservices
├── hooks/                    # Custom React hooks
└── stores/                   # State management
```

## 🧪 Testing Requirements

### Test Coverage Standards
- **Minimum coverage**: 80% for all new code
- **Critical paths**: 95% coverage required
- **Microservices**: Each service must have independent tests

### Testing Pyramid
```bash
# Unit Tests (Fast, Isolated)
pytest tests/unit/
npm run test:unit

# Integration Tests (Database, APIs)
pytest tests/integration/
npm run test:integration

# End-to-End Tests (Full User Flows)
npm run test:e2e

# Contract Tests (Service Communication)
pytest tests/contracts/
```

### Writing Tests
```python
# Backend Test Example
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_product():
    """Test product creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/products",
            json={
                "name": "Test Product",
                "price": 29.99,
                "sku": "TEST-001"
            }
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["price"] == 29.99
```

```typescript
// Frontend Test Example
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from './ProductCard';

describe('ProductCard', () => {
  it('should call onAddToCart when button is clicked', () => {
    const mockProduct = {
      id: '1',
      name: 'Test Product',
      price: 29.99
    };
    const mockOnAddToCart = jest.fn();

    render(
      <ProductCard 
        product={mockProduct} 
        onAddToCart={mockOnAddToCart} 
      />
    );

    const addButton = screen.getByText('Add to Cart');
    fireEvent.click(addButton);

    expect(mockOnAddToCart).toHaveBeenCalledWith('1');
  });
});
```

## 🔄 Pull Request Process

### Before Submitting
1. **Update your branch** with latest changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   make lint     # Code formatting and linting
   make test     # All tests
   make build    # Build verification
   ```

3. **Update documentation** if needed
4. **Add tests** for new functionality

### PR Template
When creating a PR, include:
```markdown
## 🎯 Description
Brief description of changes and motivation.

## 🔧 Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## 🧪 Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass (if applicable)
- [ ] New tests added for new functionality

## 📋 Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes without migration guide

## 🔗 Related Issues
Fixes #(issue number)

## 📸 Screenshots (if applicable)
```

### Review Process
1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by at least one maintainer
3. **Testing verification** in review environment
4. **Documentation review** if docs were changed
5. **Final approval** and merge

## 🏗️ Microservices Guidelines

### Creating New Services
1. **Follow the established pattern**:
   ```bash
   services/
   └── your-service/
       ├── app/
       │   ├── main.py
       │   ├── models.py
       │   ├── service.py
       │   └── config.py
       ├── tests/
       ├── Dockerfile
       └── requirements.txt
   ```

2. **Use standard ports**: 8001, 8002, 8003, etc.
3. **Include health checks**: `/health` endpoint
4. **Add comprehensive tests**: Unit, integration, and contract tests
5. **Document APIs**: OpenAPI/Swagger documentation

### Service Communication
- **Prefer async communication** for non-critical operations
- **Use HTTP for synchronous** service-to-service calls
- **Implement circuit breakers** for resilience
- **Add proper error handling** and retries

### Configuration Management
```python
# Use environment-based configuration
class Settings(BaseSettings):
    service_name: str = "your-service"
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    class Config:
        env_file = ".env"
```

## 🎯 Areas Needing Contributions

### High Priority
- **Order Service** implementation
- **Inventory Service** development
- **API Gateway** setup with Kong
- **Service-to-service** authentication

### Medium Priority
- **Payment Service** integration
- **Notification Service** (email, SMS)
- **Analytics Service** enhancements
- **Mobile app** development

### Documentation
- **API documentation** improvements
- **Setup guides** for different platforms
- **Architecture diagrams** updates
- **Performance optimization** guides

## 🆘 Getting Help

### Questions?
- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bug reports and feature requests
- **Discord/Slack**: Real-time chat (link in main README)

### Useful Resources
- [Development Setup Guide](./docs/development/setup.md)
- [Architecture Documentation](./docs/architecture/)
- [Testing Guide](./TESTING_COMPREHENSIVE_GUIDE.md)
- [API Documentation](http://localhost:8000/docs)

## 🙏 Recognition

Contributors will be recognized in:
- **README.md** contributor section
- **Release notes** for their contributions
- **GitHub** contributor graphs
- **Special thanks** in documentation

---

**Thank you for contributing to Brain2Gain! Every contribution, no matter how small, helps make our platform better for the fitness community.**