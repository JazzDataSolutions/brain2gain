import { Flex, Spacer, useDisclosure } from "@chakra-ui/react"

interface AdminNavbarProps {
  addModalAs: React.ComponentType<{ isOpen: boolean; onClose: () => void }>
}

const AdminNavbar = ({ addModalAs: AddModal }: AdminNavbarProps) => {
  const { isOpen, onClose } = useDisclosure()

  return (
    <Flex py={8} gap={4}>
      <Spacer />
      <AddModal isOpen={isOpen} onClose={onClose} />
    </Flex>
  )
}

export default AdminNavbar
