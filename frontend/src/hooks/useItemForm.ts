import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  type DefaultValues,
  type FieldValues,
  type SubmitHandler,
  useForm,
} from "react-hook-form"
import type { ApiError } from "../client"
import { handleError } from "../utils"
import useCustomToast from "./useCustomToast"

interface UseItemFormOptions<T> {
  defaultValues: T
  mutationFn: (data: T) => Promise<unknown>
  successMessage: string
  onSuccess?: () => void
}

function useItemForm<T extends FieldValues>(options: UseItemFormOptions<T>) {
  const queryClient = useQueryClient()
  const showToast = useCustomToast()

  const { register, handleSubmit, reset, formState } = useForm<T>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: options.defaultValues as DefaultValues<T>,
  })

  const mutation = useMutation({
    mutationFn: options.mutationFn,
    onSuccess: () => {
      showToast("Success!", options.successMessage, "success")
      options.onSuccess?.()
      reset()
    },
    onError: (err: ApiError) => handleError(err, showToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
    },
  })

  const onSubmit: SubmitHandler<T> = (data) => mutation.mutate(data)

  return {
    register,
    handleSubmit,
    formState,
    onSubmit,
    isSubmitting: formState.isSubmitting,
  }
}

export default useItemForm
