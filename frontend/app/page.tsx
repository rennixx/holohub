import { redirect } from "next/navigation";

export default function HomePage() {
  // Redirect to login or dashboard based on auth status
  // This will be handled by middleware, but we have a fallback here
  redirect("/dashboard");
}
