// Note: the `PrivateService` is only available when generating the client
// for local environments
// TODO: Fix PrivateService export issue - temporarily commented out
// import { OpenAPI, PrivateService } from "../../src/client"

// OpenAPI.BASE = `${process.env.VITE_API_URL}`

export const createUser = async ({
  email,
  password,
}: {
  email: string
  password: string
}) => {
  // TODO: Re-enable when PrivateService is available
  console.warn("PrivateService temporarily disabled for E2E tests")
  return Promise.resolve({ message: "Mock user creation" })
  // return await PrivateService.createUser({
  //   requestBody: {
  //     email,
  //     password,
  //     is_verified: true,
  //     full_name: "Test User",
  //   },
  // })
}
