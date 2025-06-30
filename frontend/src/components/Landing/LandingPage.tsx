import { Box } from "@chakra-ui/react"

import Conocenos from "./Conocenos"
import Contacto from "./Contacto"
import FeaturedProducts from "./FeaturedProducts"
import Footer from "./Footer"
import HeroSection from "./HeroSection"
import Navbar from "./Navbar"

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

export default LandingPage
