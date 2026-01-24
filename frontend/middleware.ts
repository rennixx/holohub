import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for authentication and route protection
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const authCookie = request.cookies.get("holohub-auth")?.value;

  // Parse auth cookie - handle both formats
  let isAuthenticated = false;
  if (authCookie) {
    try {
      const parsed = JSON.parse(authCookie);
      // Handle nested format: { accessToken: { accessToken: "..." } }
      // or flat format: { accessToken: "..." }
      isAuthenticated = !!(
        parsed?.accessToken?.accessToken ||
        parsed?.accessToken
      );
    } catch {
      // Invalid JSON, not authenticated
    }
  }

  // Define public routes that don't require authentication
  const publicRoutes = ["/login", "/register", "/api/v1/auth"];
  const isPublicRoute = publicRoutes.some((route) => pathname.startsWith(route));

  // Define auth routes that should redirect if already authenticated
  const authRoutes = ["/login", "/register"];
  const isAuthRoute = authRoutes.some((route) => pathname === route);

  // Redirect to login if trying to access protected route while not authenticated
  if (!isPublicRoute && !isAuthenticated) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  // Redirect to dashboard if trying to access auth route while already authenticated
  if (isAuthRoute && isAuthenticated) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
