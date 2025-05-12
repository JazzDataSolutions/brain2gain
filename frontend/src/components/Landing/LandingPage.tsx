// frontend/src/components/Landing/LandingPage.tsx
import { useEffect } from 'react';
import Navbar from './Navbar';
import HeroSection from './HeroSection';
import CatalogoPage from './CatalogoPage';
import Conocenos from './Conocenos';
import Contacto from './Contacto';
import Footer from './Footer';
import { Box } from '@chakra-ui/react';

const LandingPage = () => {
  useEffect(() => {
    console.log('LandingPage montada');
  }, []);

  return (
    <Box>
      <Navbar />
      <HeroSection />
      <CatalogoPage />
      <Conocenos />
      <Contacto />
      <Footer />
    </Box>
  );
};

export default LandingPage;
