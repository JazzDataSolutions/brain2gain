// frontend/src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Text } from '@chakra-ui/react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Actualiza el estado para renderizar la interfaz de error
    console.error('ErrorBoundary capturó un error:', error);
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Aquí puedes registrar el error a un servicio externo, si lo deseas
    console.error('Detalles del error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box p={4} textAlign="center">
          <Text fontSize="2xl" color="red.500" mb={2}>
            Algo salió mal.
          </Text>
          <Text>{this.state.error?.toString()}</Text>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
