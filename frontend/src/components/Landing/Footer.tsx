// src/components/Footer.tsx
import { Box, Flex, Image, Link, Text } from "@chakra-ui/react"

const Footer = () => {
  return (
    <Box bg="black" color="white" py={4}>
      <Flex align="center" justify="center" mb={2}>
        <Link href="https://www.instagram.com/brain2.gain/" isExternal>
          <Image
            src="/imagenes/logo_footer.png"
            alt="Logo Brain2Gain"
            height="30px"
            mx={2}
          />
        </Link>
        <Link href="https://www.instagram.com/brain2.gain/" isExternal>
          <Image
            src="/imagenes/icono_instagram.png"
            alt="Instagram"
            height="30px"
            mx={2}
          />
        </Link>
      </Flex>
      <Text textAlign="center">Brain2Gain, 2025</Text>
    </Box>
  )
}

export default Footer
