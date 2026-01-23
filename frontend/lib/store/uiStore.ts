import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "light" | "dark" | "system";

interface UIState {
  // Theme
  theme: Theme;

  // Sidebar
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;

  // View mode
  assetsViewMode: "grid" | "list";

  // Actions
  setTheme: (theme: Theme) => void;
  setSidebarOpen: (open: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  setAssetsViewMode: (mode: "grid" | "list") => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Initial state
      theme: "system",
      sidebarOpen: true,
      sidebarCollapsed: false,
      assetsViewMode: "grid",

      // Actions
      setTheme: (theme) => set({ theme }),

      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),

      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      setAssetsViewMode: (assetsViewMode) => set({ assetsViewMode }),
    }),
    {
      name: "holohub-ui",
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        assetsViewMode: state.assetsViewMode,
      }),
    }
  )
);

// Selectors
export const selectTheme = (state: UIState) => state.theme;
export const selectSidebarOpen = (state: UIState) => state.sidebarOpen;
export const selectSidebarCollapsed = (state: UIState) => state.sidebarCollapsed;
export const selectAssetsViewMode = (state: UIState) => state.assetsViewMode;
