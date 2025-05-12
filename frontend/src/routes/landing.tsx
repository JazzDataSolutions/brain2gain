// frontend/src/routes/landing.tsx
import { createFileRoute } from '@tanstack/react-router';
import LandingPage from '../components/Landing/LandingPage';


export const Route = createFileRoute('/landing')({
  component: LandingPage,
});
