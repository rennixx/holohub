/**
 * Settings Store
 *
 * Zustand store for user settings with localStorage persistence.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserSettings } from "@/types/settings";

interface SettingsState {
  settings: UserSettings | null;
  isLoading: boolean;
  error: string | null;
  setSettings: (settings: UserSettings) => void;
  updateSetting: <K extends keyof UserSettings>(
    key: K,
    value: UserSettings[K]
  ) => void;
  updateMultipleSettings: (updates: Partial<UserSettings>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearSettings: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: null,
      isLoading: false,
      error: null,

      setSettings: (settings) => set({ settings, error: null }),

      updateSetting: <K extends keyof UserSettings>(
        key: K,
        value: UserSettings[K]
      ) =>
        set((state) => ({
          settings: state.settings
            ? { ...state.settings, [key]: value }
            : null,
        })),

      updateMultipleSettings: (updates) =>
        set((state) => ({
          settings: state.settings
            ? { ...state.settings, ...updates }
            : null,
        })),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      clearSettings: () => set({ settings: null, error: null }),
    }),
    {
      name: "user-settings-storage",
      version: 1,
    }
  )
);
