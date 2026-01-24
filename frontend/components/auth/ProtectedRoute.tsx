"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { Loader2 } from "lucide-react";
import { UserRole } from "@/types";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requiredRoles?: UserRole[];
  redirectTo?: string;
}

/**
 * Protected Route Wrapper
 * Redirects unauthenticated users to login and checks role permissions
 */
export function ProtectedRoute({
  children,
  requireAuth = true,
  requiredRoles,
  redirectTo = "/login",
}: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, user, isLoading, accessToken, setLoading } = useAuthStore();

  useEffect(() => {
    // If we have an access token but no user data, clear loading state
    // This can happen after page refresh when tokens are loaded from localStorage
    if (accessToken && !user && isLoading) {
      setLoading(false);
    }

    // Redirect to login if auth is required but user is not authenticated
    if (requireAuth && !isAuthenticated && !isLoading) {
      router.push(`${redirectTo}?redirect=${encodeURIComponent(pathname)}`);
      return;
    }

    // Check role permissions
    if (requiredRoles && user && !requiredRoles.includes(user.role)) {
      router.push("/dashboard");
      return;
    }
  }, [isAuthenticated, user, isLoading, requireAuth, requiredRoles, router, pathname, redirectTo, accessToken, setLoading]);

  // Show loading state while checking auth (but not if we have a token)
  if (isLoading && !accessToken) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />
          <p className="mt-2 text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // If auth is not required, render children
  if (!requireAuth) {
    return <>{children}</>;
  }

  // If auth is required and user is authenticated, render children
  if (isAuthenticated) {
    if (requiredRoles && user && !requiredRoles.includes(user.role)) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold">Access Denied</p>
            <p className="text-sm text-muted-foreground">You don't have permission to access this page.</p>
          </div>
        </div>
      );
    }
    return <>{children}</>;
  }

  // Show loading while redirecting
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}

/**
 * Higher-order component version for easier usage
 */
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  options?: Omit<ProtectedRouteProps, "children">
) {
  return function AuthenticatedComponent(props: P) {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };
}
