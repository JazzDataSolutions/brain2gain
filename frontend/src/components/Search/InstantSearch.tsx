import {
  Badge,
  Box,
  HStack,
  Image,
  Input,
  InputGroup,
  InputLeftElement,
  Kbd,
  Portal,
  Spinner,
  Text,
  VStack,
  useColorModeValue,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { AnimatePresence, motion } from "framer-motion"
import type React from "react"
import { useEffect, useMemo, useRef, useState } from "react"
import { FiSearch, FiShoppingCart } from "react-icons/fi"
import { debounce } from "../../utils"

interface Product {
  id: string
  name: string
  price: number
  image?: string
  category?: string
  stock?: number
  sku?: string
}

interface InstantSearchProps {
  placeholder?: string
  onProductSelect?: (product: Product) => void
  maxResults?: number
  categories?: string[]
}

const InstantSearch: React.FC<InstantSearchProps> = ({
  placeholder = "Buscar proteínas, creatina, pre-entrenos...",
  onProductSelect,
  maxResults = 8,
  categories = [],
}) => {
  const [query, setQuery] = useState("")
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const resultsRef = useRef<HTMLDivElement>(null)

  // Theme colors
  const bgColor = useColorModeValue("white", "gray.800")
  const borderColor = useColorModeValue("gray.200", "gray.600")
  const hoverBg = useColorModeValue("gray.50", "gray.700")
  const shadowColor = useColorModeValue(
    "rgba(0, 0, 0, 0.1)",
    "rgba(255, 255, 255, 0.1)",
  )

  // Debounced search query
  const debouncedQuery = useMemo(
    () => debounce((searchTerm: string) => searchTerm, 300),
    [],
  )

  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    if (query.length >= 2) {
      const debounced = debouncedQuery(query)
      if (typeof debounced === "string") {
        setSearchTerm(debounced)
      }
    } else {
      setSearchTerm("")
    }
  }, [query, debouncedQuery])

  // API call for search results
  const { data: results = [], isLoading } = useQuery({
    queryKey: ["search-products", searchTerm],
    queryFn: async () => {
      if (!searchTerm || searchTerm.length < 2) return []

      // Mock API call - replace with actual API endpoint
      const response = await fetch(
        `/api/v1/products/search?q=${encodeURIComponent(
          searchTerm,
        )}&limit=${maxResults}`,
      )
      if (!response.ok) throw new Error("Search failed")

      const data = await response.json()
      return data.products || []
    },
    enabled: searchTerm.length >= 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)
    setSelectedIndex(-1)
    setIsOpen(value.length >= 2)
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault()
        setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0))
        break
      case "ArrowUp":
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1))
        break
      case "Enter":
        e.preventDefault()
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleProductSelect(results[selectedIndex])
        } else if (query.trim()) {
          // Navigate to search results page
          navigate({
            to: "/store/products",
            search: { q: query.trim() },
          })
          setIsOpen(false)
        }
        break
      case "Escape":
        setIsOpen(false)
        inputRef.current?.blur()
        break
    }
  }

  // Handle product selection
  const handleProductSelect = (product: Product) => {
    if (onProductSelect) {
      onProductSelect(product)
    } else {
      navigate({ to: `/store/products/${product.id}` })
    }
    setIsOpen(false)
    setQuery("")
  }

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        resultsRef.current &&
        !resultsRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  // Format price
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      minimumFractionDigits: 0,
    }).format(price)
  }

  // Highlight matching text
  const highlightMatch = (text: string, query: string) => {
    if (!query.trim()) return text

    const regex = new RegExp(`(${query})`, "gi")
    const parts = text.split(regex)

    return parts.map((part, index) =>
      regex.test(part) ? (
        <Text
          as="span"
          key={index}
          bg="yellow.200"
          color="black"
          px={1}
          borderRadius="sm"
        >
          {part}
        </Text>
      ) : (
        part
      ),
    )
  }

  return (
    <Box position="relative" w="full" maxW="500px">
      {/* Search Input */}
      <InputGroup size="lg">
        <InputLeftElement pointerEvents="none">
          <FiSearch color="gray.300" />
        </InputLeftElement>
        <Input
          ref={inputRef}
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          borderRadius="full"
          bg={bgColor}
          border="2px solid"
          borderColor={borderColor}
          _focus={{
            borderColor: "brand.500",
            boxShadow: "0 0 0 1px var(--chakra-colors-brand-500)",
          }}
          _hover={{
            borderColor: "brand.300",
          }}
        />
      </InputGroup>

      {/* Search Results Dropdown */}
      <Portal>
        <AnimatePresence>
          {isOpen && (
            <motion.div
              ref={resultsRef}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              style={{
                position: "absolute",
                top: `${
                  inputRef.current?.getBoundingClientRect().bottom || 0
                }px`,
                left: `${
                  inputRef.current?.getBoundingClientRect().left || 0
                }px`,
                width: `${
                  inputRef.current?.getBoundingClientRect().width || 0
                }px`,
                zIndex: 1000,
                backgroundColor: bgColor,
                border: `1px solid ${borderColor}`,
                borderRadius: "12px",
                boxShadow: `0 10px 30px ${shadowColor}`,
                maxHeight: "400px",
                overflow: "hidden",
                marginTop: "8px",
              }}
            >
              <VStack spacing={0} align="stretch">
                {/* Loading State */}
                {isLoading && (
                  <Box p={4} textAlign="center">
                    <Spinner size="sm" color="brand.500" mr={2} />
                    <Text display="inline" fontSize="sm" color="gray.500">
                      Buscando productos...
                    </Text>
                  </Box>
                )}

                {/* Results */}
                {!isLoading && results.length > 0 && (
                  <>
                    <Box
                      p={2}
                      borderBottom="1px solid"
                      borderColor={borderColor}
                    >
                      <Text
                        fontSize="xs"
                        color="gray.500"
                        textTransform="uppercase"
                      >
                        Productos ({results.length})
                      </Text>
                    </Box>

                    <VStack
                      spacing={0}
                      align="stretch"
                      maxH="300px"
                      overflowY="auto"
                    >
                      {results.map((product, index) => (
                        <Box
                          key={product.id}
                          p={3}
                          cursor="pointer"
                          bg={selectedIndex === index ? hoverBg : "transparent"}
                          _hover={{ bg: hoverBg }}
                          onClick={() => handleProductSelect(product)}
                          borderBottom={
                            index < results.length - 1 ? "1px solid" : "none"
                          }
                          borderColor={borderColor}
                        >
                          <HStack spacing={3}>
                            {/* Product Image */}
                            {product.image ? (
                              <Image
                                src={product.image}
                                alt={product.name}
                                boxSize="40px"
                                objectFit="cover"
                                borderRadius="md"
                                fallback={
                                  <Box
                                    boxSize="40px"
                                    bg="gray.200"
                                    borderRadius="md"
                                    display="flex"
                                    alignItems="center"
                                    justifyContent="center"
                                  >
                                    <FiShoppingCart size={16} />
                                  </Box>
                                }
                              />
                            ) : (
                              <Box
                                boxSize="40px"
                                bg="gray.200"
                                borderRadius="md"
                                display="flex"
                                alignItems="center"
                                justifyContent="center"
                              >
                                <FiShoppingCart size={16} />
                              </Box>
                            )}

                            {/* Product Info */}
                            <VStack flex={1} align="start" spacing={1}>
                              <Text
                                fontSize="sm"
                                fontWeight="medium"
                                noOfLines={1}
                              >
                                {highlightMatch(product.name, query)}
                              </Text>
                              <HStack spacing={2}>
                                <Text
                                  fontSize="sm"
                                  color="brand.500"
                                  fontWeight="bold"
                                >
                                  {formatPrice(product.price)}
                                </Text>
                                {product.category && (
                                  <Badge size="sm" colorScheme="gray">
                                    {product.category}
                                  </Badge>
                                )}
                                {product.stock !== undefined &&
                                  product.stock < 10 && (
                                    <Badge size="sm" colorScheme="orange">
                                      Stock bajo
                                    </Badge>
                                  )}
                              </HStack>
                            </VStack>
                          </HStack>
                        </Box>
                      ))}
                    </VStack>
                  </>
                )}

                {/* No Results */}
                {!isLoading && query.length >= 2 && results.length === 0 && (
                  <Box p={4} textAlign="center">
                    <Text fontSize="sm" color="gray.500" mb={2}>
                      No encontramos productos para "{query}"
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                      Intenta con términos como "proteína", "creatina" o
                      "pre-entreno"
                    </Text>
                  </Box>
                )}

                {/* Keyboard Shortcuts */}
                {query.length >= 2 && (
                  <Box
                    p={2}
                    borderTop="1px solid"
                    borderColor={borderColor}
                    bg={hoverBg}
                  >
                    <HStack
                      justify="space-between"
                      fontSize="xs"
                      color="gray.500"
                    >
                      <HStack spacing={2}>
                        <HStack>
                          <Kbd>↵</Kbd>
                          <Text>seleccionar</Text>
                        </HStack>
                        <HStack>
                          <Kbd>↑↓</Kbd>
                          <Text>navegar</Text>
                        </HStack>
                      </HStack>
                      <HStack>
                        <Kbd>esc</Kbd>
                        <Text>cerrar</Text>
                      </HStack>
                    </HStack>
                  </Box>
                )}
              </VStack>
            </motion.div>
          )}
        </AnimatePresence>
      </Portal>
    </Box>
  )
}

export default InstantSearch
