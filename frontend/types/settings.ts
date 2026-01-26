/**
 * Settings Types
 *
 * TypeScript interfaces and types for user and organization settings.
 */

export type ThemePreference = "dark" | "light" | "system";
export type ViewMode = "grid" | "list";

/**
 * User Settings Interface
 *
 * Contains all user preference settings.
 */
export interface UserSettings {
  // Notification Preferences
  email_notifications: boolean;
  push_notifications: boolean;
  device_alerts: boolean;
  playlist_updates: boolean;
  team_invites: boolean;

  // Display Preferences
  theme: ThemePreference;
  language: string;
  timezone: string;
  date_format: string;

  // Default Behaviors
  default_view_mode: ViewMode;
  items_per_page: number;
  auto_refresh_devices: boolean;
  auto_refresh_interval: number;

  // Privacy
  profile_visible: boolean;
  activity_visible: boolean;
}

/**
 * User Settings Update (all fields optional)
 */
export type UserSettingsUpdate = Partial<UserSettings>;

/**
 * Organization Settings Interface
 */
export interface OrgSettings {
  name: string;
  slug?: string;
  branding?: {
    logo_url?: string;
    primary_color?: string;
  };
  allowed_domains?: string[];
  default_device_settings?: Record<string, unknown>;
}

/**
 * Organization Settings Update (all fields optional)
 */
export type OrgSettingsUpdate = Partial<OrgSettings>;

/**
 * API Response Types
 */
export interface UserSettingsResponse extends UserSettings {
  id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface OrgSettingsResponse extends OrgSettings {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface LogoUploadResponse {
  logo_url: string;
  message: string;
}

/**
 * Default user settings values
 */
export const DEFAULT_USER_SETTINGS: UserSettings = {
  email_notifications: true,
  push_notifications: true,
  device_alerts: true,
  playlist_updates: true,
  team_invites: true,
  theme: "dark",
  language: "en",
  timezone: "UTC",
  date_format: "MM/DD/YYYY",
  default_view_mode: "grid",
  items_per_page: 20,
  auto_refresh_devices: true,
  auto_refresh_interval: 30,
  profile_visible: true,
  activity_visible: true,
} as const;
