import { Button, Flex, Spacer } from "@chakra-ui/react"

interface AdminNavbarProps {
  type: string
  addModalAs: React.ComponentType
}

const AdminNavbar = ({ type, addModalAs: AddModal }: AdminNavbarProps) => {
  return (
    <Flex py={8} gap={4}>
      <Spacer />
      <AddModal />
    </Flex>
  )
}

export default AdminNavbar