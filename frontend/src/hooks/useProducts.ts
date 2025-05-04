import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ProductService } from "../services/productService";
import { createContext, useContext } from "react";

const ProductServiceCtx = createContext<ProductService | null>(null);
export const ProductServiceProvider = ProductServiceCtx.Provider;

export function useProducts() {
  const svc = useContext(ProductServiceCtx)!; // LSP: ctx puede sustituirse por mock
  const queryClient = useQueryClient();

  const list = useQuery(["products"], () => svc.list());
  const create = useMutation(svc.create, {
    onSuccess: () => queryClient.invalidateQueries(["products"]),
  });

  return { list, create };
}

