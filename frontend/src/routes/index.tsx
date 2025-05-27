import { createFileRoute } from '@tanstack/react-router'
import LandingPage from '../components/Landing/LandingPage'

export const Route = createFileRoute('/')({
  component: LandingPage,
})