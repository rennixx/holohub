import { create } from "zustand";
import type { Organization, OrganizationStats } from "@/types";

interface OrganizationState {
  // State
  organization: Organization | null;
  stats: OrganizationStats | null;

  // Actions
  setOrganization: (organization: Organization) => void;
  setStats: (stats: OrganizationStats) => void;
  clearOrganization: () => void;
}

export const useOrganizationStore = create<OrganizationState>((set) => ({
  // Initial state
  organization: null,
  stats: null,

  // Actions
  setOrganization: (organization) => set({ organization }),

  setStats: (stats) => set({ stats }),

  clearOrganization: () => set({ organization: null, stats: null }),
}));

// Selectors
export const selectCurrentOrganization = (state: OrganizationState) => state.organization;
export const selectOrganizationStats = (state: OrganizationState) => state.stats;
