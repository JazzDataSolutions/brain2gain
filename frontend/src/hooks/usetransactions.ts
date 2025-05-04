// src/hooks/useTransactions.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { TransactionService } from "../services/transactionService";

const svc = new TransactionService();

export function useTransactions() {
  const qc = useQueryClient();
  const list = useQuery(["transactions"], () => svc.list());
  const create = useMutation(svc.create.bind(svc), {
    onSuccess: () => qc.invalidateQueries(["transactions"]),
  });
  return { list, create };
}

