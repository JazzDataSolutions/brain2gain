import { Box } from '@chakra-ui/react'

import Navbar from './Navbar'
import HeroSection from './HeroSection'
import FeaturedProducts from './FeaturedProducts'
import Conocenos from './Conocenos'
import Contacto from './Contacto'
import Footer from './Footer'

const LandingPage = () => {
  return (
    <Box>
      <Navbar />
      <HeroSection />
      <FeaturedProducts />
      <Box id="conocenos">
        <Conocenos />
      </Box>
      <Box id="contacto">
        <Contacto />
      </Box>
      <Footer />
    </Box>
  )
}

export default LandingPage;
