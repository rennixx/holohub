/**
 * Billing API
 *
 * Endpoints for billing, subscription, and invoice management.
 */
import apiClient from "./client";

// =============================================================================
// Types
// =============================================================================

export interface PlanFeatures {
  devices: number;
  playlists: number;
  storage_gb: number;
}

export interface PlanDetails {
  id: string;
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  limits: PlanFeatures;
  is_current?: boolean;
}

export interface UsageStats {
  devices: number;
  device_limit: number;
  playlists: number;
  playlist_limit: number;
  storage_gb: number;
  storage_limit_gb: number;
  storage_percentage: number;
}

export interface InvoiceItem {
  id: string;
  date: string;
  amount: number;
  currency: string;
  status: string;
  description: string;
  invoice_pdf?: string;
}

export interface SubscriptionInfo {
  tier: string;
  status?: string;
  subscription_end_date?: string;
  is_active: boolean;
  plan: PlanDetails;
}

export interface UpgradeRequest {
  tier: string;
}

// =============================================================================
// API
// =============================================================================

export const billingApi = {
  /**
   * Get current subscription information
   */
  getSubscription: async (): Promise<SubscriptionInfo> => {
    return await apiClient.get("/billing/subscription");
  },

  /**
   * Get current usage statistics
   */
  getUsage: async (): Promise<UsageStats> => {
    return await apiClient.get("/billing/usage");
  },

  /**
   * Get invoice history
   */
  getInvoices: async (limit: number = 12): Promise<InvoiceItem[]> => {
    return await apiClient.get(`/billing/invoices?limit=${limit}`);
  },

  /**
   * Get available plans
   */
  getPlans: async (): Promise<PlanDetails[]> => {
    return await apiClient.get("/billing/plans");
  },

  /**
   * Upgrade to a new plan
   */
  upgradePlan: async (tier: string): Promise<{ message: string; tier: string }> => {
    return await apiClient.post("/billing/upgrade", { tier });
  },
};
