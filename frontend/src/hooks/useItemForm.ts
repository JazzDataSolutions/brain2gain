import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm, type SubmitHandler } from "react-hook-form";
import type { ApiError } from "../client";
import useCustomToast from "./useCustomToast";
import { handleError } from "../utils";

interface UseItemFormOptions<T> {
  defaultValues: T;
  mutationFn: (data: T) => Promise<unknown>;
  successMessage: string;
  onSuccess?: () => void;
}

function useItemForm<T>(options: UseItemFormOptions<T>) {
  const queryClient = useQueryClient();
  const showToast = useCustomToast();

  const {
    register,
    handleSubmit,
    reset,
    formState,
  } = useForm<T>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: options.defaultValues,
  });

  const mutation = useMutation({
    mutationFn: options.mutationFn,
    onSuccess: () => {
      showToast("Success!", options.successMessage, "success");
      options.onSuccess?.();
      reset();
    },
    onError: (err: ApiError) => handleError(err, showToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] });
    },
  });

  const onSubmit: SubmitHandler<T> = (data) => mutation.mutate(data);

  return { register, handleSubmit, formState, onSubmit, isSubmitting: formState.isSubmitting };
}

export default useItemForm;
