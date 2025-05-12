// frontend/src/routes/_layout/index.tsx
import { createFileRoute } from '@tanstack/react-router';
import LandingPage from '../../components/Landing/LandingPage';

const LayoutIndex = () => {
  return <LandingPage />;
};

export const Route = createFileRoute('/_layout/')({
  component: LayoutIndex, // Usa el componente definido
});
