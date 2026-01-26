/**
 * Settings Hooks
 *
 * React Query hooks for user and organization settings.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { settingsApi, orgSettingsApi } from "@/lib/api/settings";
import { useSettingsStore } from "@/lib/store/settingsStore";
import { DEFAULT_USER_SETTINGS } from "@/types/settings";

/**
 * Get current user's settings
 */
export function useSettings() {
  const setSettings = useSettingsStore((state) => state.setSettings);
  const setLoading = useSettingsStore((state) => state.setLoading);

  return useQuery({
    queryKey: ["settings"],
    queryFn: settingsApi.get,
    staleTime: 5 * 60 * 1000, // 5 minutes
    onSuccess: (data) => {
      setSettings(data);
      setLoading(false);
    },
    onError: () => {
      setLoading(false);
    },
  });
}

/**
 * Update user settings
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient();
  const setSettings = useSettingsStore((state) => state.setSettings);

  return useMutation({
    mutationFn: settingsApi.update,
    onSuccess: (data) => {
      queryClient.setQueryData(["settings"], data);
      setSettings(data);
      toast.success("Settings saved successfully");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to save settings";
      toast.error(message);
    },
  });
}

/**
 * Reset user settings to defaults
 */
export function useResetSettings() {
  const queryClient = useQueryClient();
  const setSettings = useSettingsStore((state) => state.setSettings);

  return useMutation({
    mutationFn: settingsApi.reset,
    onSuccess: (data) => {
      queryClient.setQueryData(["settings"], data);
      setSettings(data);
      toast.success("Settings reset to defaults");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to reset settings";
      toast.error(message);
    },
  });
}

/**
 * Get organization settings
 */
export function useOrgSettings() {
  return useQuery({
    queryKey: ["settings", "organization"],
    queryFn: orgSettingsApi.get,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Update organization settings
 */
export function useUpdateOrgSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: orgSettingsApi.update,
    onSuccess: (data) => {
      queryClient.setQueryData(["settings", "organization"], data);
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
      toast.success("Organization settings saved successfully");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to save organization settings";
      toast.error(message);
    },
  });
}

/**
 * Upload organization logo
 */
export function useUploadOrgLogo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: orgSettingsApi.uploadLogo,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["settings", "organization"] });
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
      toast.success("Logo uploaded successfully");
      return data;
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to upload logo";
      toast.error(message);
    },
  });
}

/**
 * Delete organization logo
 */
export function useDeleteOrgLogo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: orgSettingsApi.deleteLogo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", "organization"] });
      queryClient.invalidateQueries({ queryKey: ["organizations"] });
      toast.success("Logo removed successfully");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to remove logo";
      toast.error(message);
    },
  });
}
