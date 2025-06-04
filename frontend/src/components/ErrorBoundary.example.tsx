/**
 * ErrorBoundary Usage Examples
 * 
 * This file demonstrates how to use the ErrorBoundary component
 * in different scenarios throughout the Brain2Gain application.
 */

import React from 'react';
import ErrorBoundary, { useErrorBoundary } from './ErrorBoundary';
import { Box, Button, Text } from '@chakra-ui/react';

// Example 1: Basic ErrorBoundary usage
export const BasicExample: React.FC = () => {
  const ProblematicComponent = () => {
    const [shouldError, setShouldError] = React.useState(false);

    if (shouldError) {
      throw new Error('This is a test error!');
    }

    return (
      <Box>
        <Text>This component works fine until you click the button</Text>
        <Button onClick={() => setShouldError(true)} colorScheme="red" mt={2}>
          Trigger Error
        </Button>
      </Box>
    );
  };

  return (
    <ErrorBoundary>
      <ProblematicComponent />
    </ErrorBoundary>
  );
};

// Example 2: ErrorBoundary with custom fallback
export const CustomFallbackExample: React.FC = () => {
  const customFallback = (
    <Box p={8} textAlign="center" bg="orange.50" borderRadius="md">
      <Text fontSize="lg" color="orange.800">
        🚧 This section is temporarily unavailable
      </Text>
      <Text color="orange.600" mt={2}>
        Please try refreshing the page or contact support if the issue persists.
      </Text>
    </Box>
  );

  const BuggyComponent = () => {
    throw new Error('Custom fallback example error');
  };

  return (
    <ErrorBoundary fallback={customFallback}>
      <BuggyComponent />
    </ErrorBoundary>
  );
};

// Example 3: Using the useErrorBoundary hook
export const HookExample: React.FC = () => {
  const { captureError } = useErrorBoundary();

  const handleAsyncError = async () => {
    try {
      // Simulate an async operation that fails
      await new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Async operation failed')), 1000);
      });
    } catch (error) {
      // Capture the error and trigger the ErrorBoundary
      captureError(error as Error);
    }
  };

  const handleSyncError = () => {
    captureError(new Error('Manually triggered error'));
  };

  return (
    <Box p={4}>
      <Text mb={4}>This component uses the useErrorBoundary hook:</Text>
      <Button onClick={handleSyncError} colorScheme="red" mr={2}>
        Trigger Sync Error
      </Button>
      <Button onClick={handleAsyncError} colorScheme="orange">
        Trigger Async Error
      </Button>
    </Box>
  );
};

// Example 4: Component-level ErrorBoundary for cart operations
export const CartErrorBoundaryExample: React.FC = () => {
  const CartComponent = () => {
    const [items, setItems] = React.useState([]);

    const addToCart = (item: any) => {
      // Simulate an error when adding invalid items
      if (!item.id || !item.price) {
        throw new Error('Invalid item: missing required fields (id, price)');
      }
      setItems(prev => [...prev, item]);
    };

    return (
      <Box>
        <Text>Cart Items: {items.length}</Text>
        <Button
          onClick={() => addToCart({ name: 'Invalid Item' })} // Missing id and price
          colorScheme="blue"
          mt={2}
        >
          Add Invalid Item to Cart
        </Button>
      </Box>
    );
  };

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Custom error handling for cart operations
        console.error('Cart error:', error);
        // Could send to analytics: trackEvent('cart_error', { error: error.message });
      }}
      showDetails={false} // Hide technical details for users
    >
      <CartComponent />
    </ErrorBoundary>
  );
};

// Example 5: Route-level ErrorBoundary
export const RouteErrorBoundaryExample: React.FC = () => {
  const ProductPage = ({ productId }: { productId: string }) => {
    // Simulate a product that doesn't exist
    if (productId === 'invalid') {
      throw new Error(`Product with ID "${productId}" not found`);
    }

    return (
      <Box>
        <Text>Product Page for ID: {productId}</Text>
      </Box>
    );
  };

  return (
    <ErrorBoundary
      fallback={
        <Box p={8} textAlign="center">
          <Text fontSize="xl" mb={4}>Product Not Found</Text>
          <Text color="gray.600">
            The product you're looking for doesn't exist or has been removed.
          </Text>
          <Button mt={4} colorScheme="blue">
            Browse All Products
          </Button>
        </Box>
      }
    >
      <ProductPage productId="invalid" />
    </ErrorBoundary>
  );
};

// Example 6: Nested ErrorBoundaries for granular error handling
export const NestedErrorBoundariesExample: React.FC = () => {
  const Header = () => <Text>Header Component</Text>;
  
  const Sidebar = () => {
    throw new Error('Sidebar crashed!');
  };
  
  const MainContent = () => <Text>Main content is working fine</Text>;

  return (
    <Box>
      {/* Global ErrorBoundary for the entire layout */}
      <ErrorBoundary>
        <Header />
        
        <Box display="flex" mt={4}>
          {/* Specific ErrorBoundary for sidebar */}
          <ErrorBoundary
            fallback={
              <Box w="200px" p={4} bg="red.50" borderRadius="md">
                <Text color="red.600" fontSize="sm">
                  Sidebar unavailable
                </Text>
              </Box>
            }
          >
            <Sidebar />
          </ErrorBoundary>
          
          {/* Main content continues to work even if sidebar fails */}
          <Box flex={1} ml={4}>
            <MainContent />
          </Box>
        </Box>
      </ErrorBoundary>
    </Box>
  );
};

/**
 * Best Practices for ErrorBoundary Usage:
 * 
 * 1. Place ErrorBoundaries at strategic locations:
 *    - At the root level (already done in main.tsx)
 *    - Around route components
 *    - Around major feature sections
 *    - Around third-party components
 * 
 * 2. Provide meaningful fallback UIs:
 *    - Don't just show "Something went wrong"
 *    - Offer recovery actions (retry, reload, contact support)
 *    - Match your app's design language
 * 
 * 3. Log errors appropriately:
 *    - Include context (user ID, route, timestamp)
 *    - Send to error tracking services in production
 *    - Include reproduction steps when possible
 * 
 * 4. Test error scenarios:
 *    - Network failures
 *    - Invalid props
 *    - Missing data
 *    - Third-party service failures
 * 
 * 5. Consider user experience:
 *    - Progressive degradation
 *    - Graceful fallbacks
 *    - Clear communication
 *    - Recovery options
 */