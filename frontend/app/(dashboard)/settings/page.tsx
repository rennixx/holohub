"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuthStore } from "@/lib/store";
import { organizationsApi } from "@/lib/api";
import { useSettings, useUpdateSettings, useOrgSettings, useUpdateOrgSettings } from "@/hooks/useSettings";
import { Loader2, User as UserIcon, Lock, Bell, Palette } from "lucide-react";
import { cn } from "@/lib/utils/cn";

// Common timezones
const TIMEZONES = [
  { value: "UTC", label: "UTC (Universal Coordinated Time)" },
  { value: "America/New_York", label: "Eastern Time (ET)" },
  { value: "America/Chicago", label: "Central Time (CT)" },
  { value: "America/Denver", label: "Mountain Time (MT)" },
  { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
  { value: "Europe/London", label: "London (GMT/BST)" },
  { value: "Europe/Paris", label: "Paris (CET/CEST)" },
  { value: "Europe/Berlin", label: "Berlin (CET/CEST)" },
  { value: "Asia/Tokyo", label: "Tokyo (JST)" },
  { value: "Asia/Shanghai", label: "Shanghai (CST)" },
  { value: "Asia/Dubai", label: "Dubai (GST)" },
  { value: "Australia/Sydney", label: "Sydney (AEST/AEDT)" },
];

// Languages
const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "zh", label: "Chinese" },
  { value: "ja", label: "Japanese" },
  { value: "ko", label: "Korean" },
];

export default function SettingsPage() {
  const { user } = useAuthStore();
  const { data: organization } = useQuery({
    queryKey: ["organization"],
    queryFn: () => organizationsApi.get(),
  });

  // Settings hooks
  const { data: settings, isLoading: settingsLoading } = useSettings();
  const updateSettings = useUpdateSettings();
  const { data: orgSettings } = useOrgSettings();
  const updateOrgSettings = useUpdateOrgSettings();

  // Local form state
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || "",
  });

  const [prefsForm, setPrefsForm] = useState({
    theme: settings?.theme || "dark",
    language: settings?.language || "en",
    timezone: settings?.timezone || "UTC",
    date_format: settings?.date_format || "MM/DD/YYYY",
    default_view_mode: settings?.default_view_mode || "grid",
    items_per_page: settings?.items_per_page || 20,
    auto_refresh_devices: settings?.auto_refresh_devices ?? true,
  });

  const [notifForm, setNotifForm] = useState({
    email_notifications: settings?.email_notifications ?? true,
    push_notifications: settings?.push_notifications ?? true,
    device_alerts: settings?.device_alerts ?? true,
    playlist_updates: settings?.playlist_updates ?? true,
    team_invites: settings?.team_invites ?? true,
  });

  const [privacyForm, setPrivacyForm] = useState({
    profile_visible: settings?.profile_visible ?? true,
    activity_visible: settings?.activity_visible ?? true,
  });

  // Handlers
  const handleSaveProfile = async () => {
    // TODO: Implement profile update API
    console.log("Saving profile:", profileForm);
  };

  const handleSavePreferences = async () => {
    updateSettings.mutate({
      theme: prefsForm.theme as any,
      language: prefsForm.language,
      timezone: prefsForm.timezone,
      date_format: prefsForm.date_format,
      default_view_mode: prefsForm.default_view_mode as any,
      items_per_page: prefsForm.items_per_page,
      auto_refresh_devices: prefsForm.auto_refresh_devices,
    });
  };

  const handleSaveNotifications = async () => {
    updateSettings.mutate(notifForm);
  };

  const handleSavePrivacy = async () => {
    updateSettings.mutate(privacyForm);
  };

  const handleSaveOrg = async () => {
    updateOrgSettings.mutate({
      name: orgForm.name,
    });
  };

  const [orgForm, setOrgForm] = useState({
    name: organization?.name || "",
  });

  if (settingsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
      </div>
    );
  }

  const userInitials = user?.full_name
    ? user.full_name.split(" ").map((n: string) => n[0]).join("").toUpperCase()
    : user?.email?.[0].toUpperCase() || "U";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            Settings
          </span>
        </h1>
        <p className="text-violet-300/70 mt-1">
          Manage your account and application preferences
        </p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="glass-holo p-1">
          <TabsTrigger value="profile" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-violet-600 data-[state=active]:to-cyan-500">
            <UserIcon className="h-4 w-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="security" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-violet-600 data-[state=active]:to-cyan-500">
            <Lock className="h-4 w-4 mr-2" />
            Security
          </TabsTrigger>
          <TabsTrigger value="preferences" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-violet-600 data-[state=active]:to-cyan-500">
            <Palette className="h-4 w-4 mr-2" />
            Preferences
          </TabsTrigger>
          <TabsTrigger value="notifications" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-violet-600 data-[state=active]:to-cyan-500">
            <Bell className="h-4 w-4 mr-2" />
            Notifications
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card className="glass-holo">
            <CardHeader>
              <CardTitle className="text-white">Profile Information</CardTitle>
              <CardDescription className="text-violet-300/70">
                Update your personal information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-6">
                <Avatar className="h-20 w-20 ring-2 ring-violet-500/50">
                  <AvatarImage src="" alt={user?.full_name} />
                  <AvatarFallback className="bg-gradient-to-br from-violet-600 to-cyan-500 text-white text-lg">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <p className="font-medium text-white">{user?.full_name || "User"}</p>
                  <p className="text-sm text-violet-400">{user?.email}</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input
                    value={profileForm.full_name}
                    onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                    placeholder="Your full name"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Email Address</Label>
                  <Input value={user?.email} disabled className="bg-violet-950/30" />
                  <p className="text-xs text-violet-400/50">Contact support to change your email</p>
                </div>

                <div className="space-y-2">
                  <Label>Role</Label>
                  <Input
                    value={user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
                    disabled
                    className="bg-violet-950/30 capitalize"
                  />
                </div>

                <Button onClick={handleSaveProfile} variant="holo-primary" disabled={updateSettings.isPending}>
                  {updateSettings.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <Card className="glass-holo">
            <CardHeader>
              <CardTitle className="text-white">Security Settings</CardTitle>
              <CardDescription className="text-violet-300/70">
                Manage your password and authentication
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between p-4 rounded-lg bg-violet-950/30 border border-violet-500/20">
                <div>
                  <p className="font-medium text-white">Two-Factor Authentication</p>
                  <p className="text-sm text-violet-400">
                    {user?.mfa_enabled ? "2FA is enabled on your account" : "Add an extra layer of security"}
                  </p>
                </div>
                <Switch
                  checked={user?.mfa_enabled ?? false}
                  disabled
                />
              </div>

              <div className="space-y-4 pt-4 border-t border-violet-500/20">
                <h3 className="text-sm font-medium text-white">Change Password</h3>
                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label>Current Password</Label>
                    <Input type="password" placeholder="Enter current password" />
                  </div>
                  <div className="space-y-2">
                    <Label>New Password</Label>
                    <Input type="password" placeholder="Enter new password" />
                  </div>
                  <div className="space-y-2">
                    <Label>Confirm New Password</Label>
                    <Input type="password" placeholder="Confirm new password" />
                  </div>
                  <Button variant="holo-secondary">Update Password</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-6">
          <Card className="glass-holo">
            <CardHeader>
              <CardTitle className="text-white">Preferences</CardTitle>
              <CardDescription className="text-violet-300/70">
                Customize your experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Appearance */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-white">Appearance</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Theme</Label>
                      <p className="text-sm text-violet-400">Choose your preferred theme</p>
                    </div>
                    <Select
                      value={prefsForm.theme}
                      onValueChange={(value) => setPrefsForm({ ...prefsForm, theme: value as any })}
                    >
                      <SelectTrigger className="w-[180px] bg-slate-950/50 border-violet-500/30 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="glass-holo border-violet-500/30">
                        <SelectItem value="dark">Dark</SelectItem>
                        <SelectItem value="light">Light</SelectItem>
                        <SelectItem value="system">System</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Language</Label>
                      <p className="text-sm text-violet-400">Interface language</p>
                    </div>
                    <Select
                      value={prefsForm.language}
                      onValueChange={(value) => setPrefsForm({ ...prefsForm, language: value })}
                    >
                      <SelectTrigger className="w-[180px] bg-slate-950/50 border-violet-500/30 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="glass-holo border-violet-500/30">
                        {LANGUAGES.map((lang) => (
                          <SelectItem key={lang.value} value={lang.value}>
                            {lang.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Timezone</Label>
                      <p className="text-sm text-violet-400">Your local timezone</p>
                    </div>
                    <Select
                      value={prefsForm.timezone}
                      onValueChange={(value) => setPrefsForm({ ...prefsForm, timezone: value })}
                    >
                      <SelectTrigger className="w-[240px] bg-slate-950/50 border-violet-500/30 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="glass-holo border-violet-500/30 max-h-60">
                        {TIMEZONES.map((tz) => (
                          <SelectItem key={tz.value} value={tz.value}>
                            {tz.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Display */}
              <div className="space-y-4 pt-4 border-t border-violet-500/20">
                <h3 className="text-sm font-medium text-white">Display</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Default View</Label>
                      <p className="text-sm text-violet-400">Grid or list view</p>
                    </div>
                    <Select
                      value={prefsForm.default_view_mode}
                      onValueChange={(value) => setPrefsForm({ ...prefsForm, default_view_mode: value as any })}
                    >
                      <SelectTrigger className="w-[140px] bg-slate-950/50 border-violet-500/30 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="glass-holo border-violet-500/30">
                        <SelectItem value="grid">Grid</SelectItem>
                        <SelectItem value="list">List</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Items Per Page</Label>
                      <p className="text-sm text-violet-400">Default pagination size</p>
                    </div>
                    <Select
                      value={prefsForm.items_per_page.toString()}
                      onValueChange={(value) => setPrefsForm({ ...prefsForm, items_per_page: parseInt(value) })}
                    >
                      <SelectTrigger className="w-[100px] bg-slate-950/50 border-violet-500/30 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="glass-holo border-violet-500/30">
                        <SelectItem value="10">10</SelectItem>
                        <SelectItem value="20">20</SelectItem>
                        <SelectItem value="50">50</SelectItem>
                        <SelectItem value="100">100</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Auto-Refresh Devices</Label>
                      <p className="text-sm text-violet-400">Auto-refresh device status</p>
                    </div>
                    <Switch
                      checked={prefsForm.auto_refresh_devices}
                      onCheckedChange={(checked) => setPrefsForm({ ...prefsForm, auto_refresh_devices: checked })}
                    />
                  </div>
                </div>
              </div>

              <Button
                onClick={handleSavePreferences}
                variant="holo-primary"
                className="mt-4"
                disabled={updateSettings.isPending}
              >
                {updateSettings.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Preferences"
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card className="glass-holo">
            <CardHeader>
              <CardTitle className="text-white">Notification Preferences</CardTitle>
              <CardDescription className="text-violet-300/70">
                Manage how you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10">
                  <div>
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-violet-400">Receive notifications via email</p>
                  </div>
                  <Switch
                    checked={notifForm.email_notifications}
                    onCheckedChange={(checked) => setNotifForm({ ...notifForm, email_notifications: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10">
                  <div>
                    <Label>Push Notifications</Label>
                    <p className="text-sm text-violet-400">Browser push notifications</p>
                  </div>
                  <Switch
                    checked={notifForm.push_notifications}
                    onCheckedChange={(checked) => setNotifForm({ ...notifForm, push_notifications: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10">
                  <div>
                    <Label>Device Alerts</Label>
                    <p className="text-sm text-violet-400">Device offline/error notifications</p>
                  </div>
                  <Switch
                    checked={notifForm.device_alerts}
                    onCheckedChange={(checked) => setNotifForm({ ...notifForm, device_alerts: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10">
                  <div>
                    <Label>Playlist Updates</Label>
                    <p className="text-sm text-violet-400">Changes to your playlists</p>
                  </div>
                  <Switch
                    checked={notifForm.playlist_updates}
                    onCheckedChange={(checked) => setNotifForm({ ...notifForm, playlist_updates: checked })}
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10">
                  <div>
                    <Label>Team Invites</Label>
                    <p className="text-sm text-violet-400">New team member invitations</p>
                  </div>
                  <Switch
                    checked={notifForm.team_invites}
                    onCheckedChange={(checked) => setNotifForm({ ...notifForm, team_invites: checked })}
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-violet-500/20">
                <h3 className="text-sm font-medium text-white mb-4">Privacy</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10">
                    <div>
                      <Label>Profile Visible</Label>
                      <p className="text-sm text-violet-400">Show profile to team members</p>
                    </div>
                    <Switch
                      checked={privacyForm.profile_visible}
                      onCheckedChange={(checked) => setPrivacyForm({ ...privacyForm, profile_visible: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10">
                    <div>
                      <Label>Activity Visible</Label>
                      <p className="text-sm text-violet-400">Show activity to team members</p>
                    </div>
                    <Switch
                      checked={privacyForm.activity_visible}
                      onCheckedChange={(checked) => setPrivacyForm({ ...privacyForm, activity_visible: checked })}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-violet-500/20 flex gap-3">
                <Button
                  onClick={handleSaveNotifications}
                  variant="holo-primary"
                  disabled={updateSettings.isPending}
                >
                  {updateSettings.isPending ? "Saving..." : "Save Notifications"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Organization Card (for admins/owners only) */}
          {(user?.role === "owner" || user?.role === "admin") && (
            <Card className="glass-holo">
              <CardHeader>
                <CardTitle className="text-white">Organization</CardTitle>
                <CardDescription className="text-violet-300/70">
                  Organization settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Organization Name</Label>
                  <Input
                    value={orgForm.name}
                    onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
                    placeholder="Organization name"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Slug</Label>
                  <Input
                    value={organization?.slug}
                    disabled
                    className="bg-violet-950/30"
                  />
                  <p className="text-xs text-violet-400/50">Cannot be changed</p>
                </div>

                <Button
                  onClick={handleSaveOrg}
                  variant="holo-secondary"
                  disabled={updateOrgSettings.isPending}
                >
                  {updateOrgSettings.isPending ? "Saving..." : "Save Organization"}
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
