import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Text, Button, VStack, Icon, Code, Collapse, useDisclosure } from '@chakra-ui/react';
import { MdError, MdRefresh, MdBugReport } from 'react-icons/md';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  eventId?: string;
}

// Error reporting function (can be extended to send to external services)
const reportError = (error: Error, errorInfo: ErrorInfo, eventId: string) => {
  // Here you can integrate with error reporting services like Sentry, LogRocket, etc.
  console.group('🚨 Error Boundary Report');
  console.error('Error:', error);
  console.error('Error Info:', errorInfo);
  console.error('Event ID:', eventId);
  console.error('Timestamp:', new Date().toISOString());
  console.error('User Agent:', navigator.userAgent);
  console.error('URL:', window.location.href);
  console.groupEnd();

  // In production, you might want to send this to your error tracking service
  if (process.env.NODE_ENV === 'production') {
    // Example: Sentry.captureException(error, { extra: errorInfo, tags: { eventId } });
  }
};

// Generate a unique error event ID
const generateEventId = () => {
  return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Error details component
const ErrorDetails: React.FC<{ error: Error; errorInfo: ErrorInfo; eventId: string }> = ({
  error,
  errorInfo,
  eventId,
}) => {
  const { isOpen, onToggle } = useDisclosure();

  return (
    <Box mt={4}>
      <Button size="sm" variant="outline" onClick={onToggle} leftIcon={<Icon as={MdBugReport} />}>
        {isOpen ? 'Hide' : 'Show'} Technical Details
      </Button>
      <Collapse in={isOpen} animateOpacity>
        <Box mt={4} p={4} bg="gray.50" borderRadius="md" border="1px" borderColor="gray.200">
          <VStack align="start" spacing={3}>
            <Box>
              <Text fontSize="sm" fontWeight="semibold" color="gray.700">
                Event ID:
              </Text>
              <Code fontSize="xs" colorScheme="gray">
                {eventId}
              </Code>
            </Box>
            <Box>
              <Text fontSize="sm" fontWeight="semibold" color="gray.700">
                Error Message:
              </Text>
              <Code fontSize="xs" colorScheme="red" display="block" whiteSpace="pre-wrap">
                {error.message}
              </Code>
            </Box>
            <Box>
              <Text fontSize="sm" fontWeight="semibold" color="gray.700">
                Stack Trace:
              </Text>
              <Code fontSize="xs" colorScheme="red" display="block" whiteSpace="pre-wrap" maxH="200px" overflowY="auto">
                {error.stack}
              </Code>
            </Box>
            {errorInfo.componentStack && (
              <Box>
                <Text fontSize="sm" fontWeight="semibold" color="gray.700">
                  Component Stack:
                </Text>
                <Code fontSize="xs" colorScheme="orange" display="block" whiteSpace="pre-wrap" maxH="200px" overflowY="auto">
                  {errorInfo.componentStack}
                </Code>
              </Box>
            )}
          </VStack>
        </Box>
      </Collapse>
    </Box>
  );
};

class ErrorBoundary extends Component<Props, State> {
  private eventId: string = '';

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.eventId = generateEventId();
    
    this.setState({
      error,
      errorInfo,
      eventId: this.eventId,
    });

    // Report error to external service and console
    reportError(error, errorInfo, this.eventId);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined, eventId: undefined });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorInfo, eventId } = this.state;

      return (
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          minH="400px"
          p={8}
          bg="gray.50"
          borderRadius="lg"
          border="1px"
          borderColor="gray.200"
        >
          <VStack spacing={6} textAlign="center" maxW="600px">
            <Icon as={MdError} boxSize={16} color="red.500" />
            
            <VStack spacing={2}>
              <Text fontSize="2xl" fontWeight="bold" color="gray.800">
                Oops! Something went wrong
              </Text>
              <Text color="gray.600" fontSize="md">
                We're sorry, but something unexpected happened. Our team has been notified and will fix this soon.
              </Text>
            </VStack>

            <VStack spacing={3}>
              <Button
                colorScheme="blue"
                leftIcon={<Icon as={MdRefresh} />}
                onClick={this.handleRetry}
                size="lg"
              >
                Try Again
              </Button>
              
              <Button
                variant="outline"
                onClick={this.handleReload}
                size="md"
              >
                Reload Page
              </Button>
            </VStack>

            {this.props.showDetails && error && errorInfo && eventId && (
              <ErrorDetails error={error} errorInfo={errorInfo} eventId={eventId} />
            )}

            <Text fontSize="xs" color="gray.500">
              If the problem persists, please contact support with Event ID: {eventId}
            </Text>
          </VStack>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Hook for functional components to create error boundaries
export const useErrorBoundary = () => {
  const [error, setError] = React.useState<Error | null>(null);

  const captureError = React.useCallback((error: Error) => {
    setError(error);
  }, []);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return { captureError };
};

export default ErrorBoundary;
