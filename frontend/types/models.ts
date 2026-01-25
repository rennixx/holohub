/**
 * Domain Models
 * These types mirror the backend Pydantic schemas
 */

// ============================================================================
// Common Types
// ============================================================================

export interface UUIDModel {
  id: string;
}

export interface TimestampModel {
  created_at: string;
  updated_at: string;
}

export interface SoftDeleteModel {
  deleted_at: string | null;
}

// ============================================================================
// Organization
// ============================================================================

export enum OrganizationTier {
  FREE = "free",
  PRO = "pro",
  ENTERPRISE = "enterprise",
}

export interface Organization extends UUIDModel, TimestampModel {
  name: string;
  slug: string;
  tier: OrganizationTier;
  storage_quota_bytes: number;
  device_limit: number;
  stripe_customer_id?: string;
  subscription_status?: string;
  branding?: Record<string, unknown>;
}

export interface OrganizationStats {
  total_devices: number;
  total_assets: number;
  total_playlists: number;
  storage_used_bytes: number;
  storage_usage_percent: number;
  is_storage_full: boolean;
  can_add_device: boolean;
}

// ============================================================================
// User
// ============================================================================

export enum UserRole {
  OWNER = "owner",
  ADMIN = "admin",
  EDITOR = "editor",
  VIEWER = "viewer",
}

export interface User extends UUIDModel, TimestampModel {
  email: string;
  full_name: string;
  organization_id: string;
  role: UserRole;
  is_active: boolean;
  mfa_enabled: boolean;
  last_login_at?: string;
}

export interface UserMe extends User {
  organization: Organization;
}

// ============================================================================
// Device
// ============================================================================

export enum DeviceStatus {
  PENDING = "pending",
  ACTIVE = "active",
  OFFLINE = "offline",
  MAINTENANCE = "maintenance",
  DECOMMISSIONED = "decommissioned",
}

export interface DisplayConfig {
  resolution: string;
  orientation: "landscape" | "portrait";
  quilt_format?: string;
}

export interface NetworkInfo {
  ip_address: string;
  mac_address: string;
  wifi_ssid?: string;
  signal_strength?: number;
}

export interface Device extends UUIDModel, TimestampModel {
  name: string;
  hardware_type: string;
  hardware_id: string;
  organization_id: string;
  status: DeviceStatus;
  location_metadata: Record<string, unknown>;
  tags: string[];
  display_config: Record<string, unknown>;
  network_info: Record<string, unknown>;
  firmware_version?: string;
  client_version?: string;
  current_playlist_id?: string;
  last_heartbeat?: string;
}

export interface DeviceHeartbeat {
  time: string;
  device_id: string;
  cpu_usage_percent?: number;
  memory_usage_percent?: number;
  storage_used_gb?: number;
  temperature_celsius?: number;
  bandwidth_mbps?: number;
  latency_ms?: number;
  packet_loss_percent?: number;
  current_playlist_id?: string;
  current_asset_id?: string;
  playback_position_sec?: number;
  error_count: number;
  last_error?: string;
}

// ============================================================================
// Asset
// ============================================================================

export enum AssetCategory {
  SCENE = "scene",
  PRODUCT = "product",
  CHARACTER = "character",
  PROP = "prop",
}

export enum ProcessingStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface GeometryStats {
  polygon_count: number;
  vertex_count: number;
  texture_count: number;
  material_count: number;
  animation_count?: number;
}

export interface QuiltOutput {
  resolution: string;
  format: string;
  file_path: string;
  file_size: number;
}

export interface AssetOutputs {
  optimized_glb?: {
    file_path: string;
    file_size: number;
  };
  draco_compressed?: {
    file_path: string;
    file_size: number;
  };
  quilts?: QuiltOutput[];
  video?: {
    file_path: string;
    file_size: number;
    duration: number;
  };
  thumbnail?: {
    file_path: string;
  };
  cdn_urls?: Record<string, string>;
}

export interface Asset extends UUIDModel, TimestampModel {
  title: string;
  description?: string;
  category: AssetCategory;
  file_path: string;
  file_size: number;
  mime_type: string;
  duration?: number;
  organization_id: string;
  uploaded_by: string;
  processing_status: ProcessingStatus;
  processing_error?: string;
  geometry_stats?: GeometryStats;
  outputs?: AssetOutputs;
  metadata?: Record<string, unknown>;
  sha256_hash: string;
}

// ============================================================================
// Playlist
// ============================================================================

export enum TransitionType {
  CUT = "cut",
  FADE = "fade",
  DISSOLVE = "dissolve",
  WIPE = "wipe",
}

export interface RecurrenceConfig {
  frequency: "daily" | "weekly" | "monthly";
  days_of_week?: number[];
  end_date?: string;
}

export interface ScheduleConfig {
  start_date: string;
  end_date?: string;
  start_time?: string;
  end_time?: string;
  timezone?: string;
  recurrence?: RecurrenceConfig;
}

export interface Playlist extends UUIDModel, TimestampModel {
  name: string;
  organization_id: string;
  created_by: string;
  is_active: boolean;
  loop_mode: boolean;
  shuffle_mode: boolean;
  shuffle: boolean;
  transition_type: TransitionType;
  transition_duration_ms: number;
  schedule_config?: ScheduleConfig;
  items?: PlaylistItem[];
  item_count: number;
  total_duration_sec?: number;
  description?: string;
}

export interface PlaylistItem {
  id: string;
  playlist_id: string;
  asset_id: string;
  order: number;
  duration: number;
  asset?: Asset;
}

export interface DevicePlaylist {
  device_id: string;
  playlist_id: string;
  priority: number;
  device?: Device;
  playlist?: Playlist;
}

// ============================================================================
// Auth
// ============================================================================

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
  mfa_code?: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  organization_name: string;
}

export interface AuthResponse extends TokenPair {
  user: UserMe;
}

// ============================================================================
// API Responses
// ============================================================================

export interface APIResponse<T = unknown> {
  success: boolean;
  message?: string;
  data?: T;
}

export interface ErrorResponse {
  detail: string;
  error_code?: string;
  field?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PaginatedData<T> {
  items: T[];
  meta: PaginationMeta;
}
