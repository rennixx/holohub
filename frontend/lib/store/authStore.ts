import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserMe, TokenPair } from "@/types";

// Helper to set/delete auth cookie (for server-side middleware)
const setAuthCookie = (tokens: TokenPair | null) => {
  if (typeof document === "undefined") return;

  if (tokens) {
    // Match the structure expected by middleware: accessToken.accessToken
    const cookieValue = JSON.stringify({ accessToken: { accessToken: tokens.access_token } });
    document.cookie = `holohub-auth=${encodeURIComponent(cookieValue)}; path=/; max-age=${tokens.expires_in || 3600}; SameSite=lax`;
  } else {
    document.cookie = "holohub-auth=; path=/; max-age=0";
  }
};

interface AuthState {
  // State
  user: UserMe | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setAuth: (user: UserMe, tokens: TokenPair) => void;
  clearAuth: () => void;
  updateTokens: (tokens: TokenPair) => void;
  setUser: (user: UserMe) => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      setAuth: (user, tokens) => {
        setAuthCookie(tokens);
        set({
          user,
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      clearAuth: () => {
        setAuthCookie(null);
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },

      updateTokens: (tokens) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
        }),

      setUser: (user) => set({ user }),

      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: "holohub-auth",
      // Only persist what we need to localStorage
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Selectors
export const selectUser = (state: AuthState) => state.user;
export const selectAccessToken = (state: AuthState) => state.accessToken;
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
export const selectOrganization = (state: AuthState) => state.user?.organization;
export const selectUserRole = (state: AuthState) => state.user?.role;
