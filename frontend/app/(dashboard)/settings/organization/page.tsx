"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/store";
import { orgSettingsApi, type OrgSettingsUpdate } from "@/lib/api/settings";
import { useOrgSettings, useUpdateOrgSettings, useUploadOrgLogo, useDeleteOrgLogo } from "@/hooks/useSettings";
import { Loader2, Upload, X, Trash2 } from "lucide-react";

export default function OrganizationSettingsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const { data: orgSettings, isLoading } = useOrgSettings();
  const updateOrgSettings = useUpdateOrgSettings();
  const uploadLogo = useUploadOrgLogo();
  const deleteLogo = useDeleteOrgLogo();

  const [orgForm, setOrgForm] = useState<OrgSettingsUpdate>({
    name: orgSettings?.name || "",
    slug: orgSettings?.slug || "",
    branding: orgSettings?.branding || {},
    allowed_domains: orgSettings?.allowed_domains || [],
  });

  const [newDomain, setNewDomain] = useState("");

  // Update local form when data loads
  if (orgSettings && orgForm.name !== orgSettings.name) {
    setOrgForm({
      name: orgSettings.name,
      slug: orgSettings.slug || "",
      branding: orgSettings.branding || {},
      allowed_domains: orgSettings.allowed_domains || [],
    });
  }

  const handleSaveOrg = async () => {
    updateOrgSettings.mutate(orgForm);
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      toast.error("Please upload an image file");
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error("Logo must be less than 2MB");
      return;
    }

    uploadLogo.mutate(file, {
      onSuccess: (data) => {
        queryClient.setQueryData(["settings", "organization"], {
          ...orgSettings,
          branding: {
            ...orgSettings?.branding,
            logo_url: data.logo_url,
          },
        });
        toast.success("Logo uploaded successfully");
      },
    });
  };

  const handleDeleteLogo = async () => {
    if (!confirm("Are you sure you want to remove the logo?")) return;

    deleteLogo.mutate(undefined, {
      onSuccess: () => {
        queryClient.setQueryData(["settings", "organization"], {
          ...orgSettings,
          branding: {
            ...orgSettings?.branding,
            logo_url: undefined,
          },
        });
        toast.success("Logo removed successfully");
      },
    });
  };

  const handleAddDomain = () => {
    const trimmed = newDomain.trim().toLowerCase();
    if (!trimmed) return;

    // Basic domain validation
    if (!/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(trimmed)) {
      toast.error("Please enter a valid domain (e.g., example.com)");
      return;
    }

    if (orgForm.allowed_domains?.includes(trimmed)) {
      toast.error("Domain already added");
      return;
    }

    setOrgForm({
      ...orgForm,
      allowed_domains: [...(orgForm.allowed_domains || []), trimmed],
    });
    setNewDomain("");
  };

  const handleRemoveDomain = (domain: string) => {
    setOrgForm({
      ...orgForm,
      allowed_domains: orgForm.allowed_domains?.filter((d) => d !== domain) || [],
    });
  };

  const handleColorChange = (color: string) => {
    setOrgForm({
      ...orgForm,
      branding: {
        ...orgForm.branding,
        primary_color: color,
      },
    });
  };

  // Check if user has permission
  const canEdit = user?.role === "owner" || user?.role === "admin";

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
      </div>
    );
  }

  const logoUrl = orgSettings?.branding?.logo_url;
  const primaryColor = orgSettings?.branding?.primary_color || "#8b5cf6";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
            Organization Settings
          </span>
        </h1>
        <p className="text-violet-300/70 mt-1">
          Manage your organization's branding and settings
        </p>
      </div>

      {/* General Settings */}
      <Card className="glass-holo">
        <CardHeader>
          <CardTitle className="text-white">General Information</CardTitle>
          <CardDescription className="text-violet-300/70">
            Basic organization details
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Organization Name</Label>
            <Input
              value={orgForm.name}
              onChange={(e) => setOrgForm({ ...orgForm, name: e.target.value })}
              placeholder="Organization name"
              disabled={!canEdit}
              className="bg-slate-950/50 border-violet-500/30 text-white"
            />
          </div>

          <div className="space-y-2">
            <Label>Slug</Label>
            <Input
              value={orgForm.slug}
              disabled
              className="bg-violet-950/30 border-violet-500/30"
            />
            <p className="text-xs text-violet-400/50">Unique identifier for your organization (cannot be changed)</p>
          </div>

          {canEdit && (
            <Button
              onClick={handleSaveOrg}
              variant="holo-primary"
              disabled={updateOrgSettings.isPending}
            >
              {updateOrgSettings.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Branding */}
      {canEdit && (
        <Card className="glass-holo">
          <CardHeader>
            <CardTitle className="text-white">Branding</CardTitle>
            <CardDescription className="text-violet-300/70">
              Customize your organization's appearance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Logo Upload */}
            <div className="space-y-4">
              <Label>Organization Logo</Label>
              <div className="flex items-center gap-6">
                {logoUrl ? (
                  <div className="relative group">
                    <img
                      src={logoUrl}
                      alt="Organization logo"
                      className="h-20 w-20 rounded-lg object-cover ring-2 ring-violet-500/50"
                    />
                    <Button
                      size="sm"
                      variant="destructive"
                      className="absolute -top-2 -right-2 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={handleDeleteLogo}
                      disabled={deleteLogo.isPending}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <div className="h-20 w-20 rounded-lg bg-violet-950/30 border-2 border-dashed border-violet-500/30 flex items-center justify-center">
                    <span className="text-violet-500/50 text-xs">No logo</span>
                  </div>
                )}
                <div className="flex-1 space-y-3">
                  <div>
                    <label
                      htmlFor="logo-upload"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors cursor-pointer"
                    >
                      <Upload className="h-4 w-4" />
                      Upload Logo
                    </label>
                    <input
                      id="logo-upload"
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleLogoUpload}
                      disabled={uploadLogo.isPending}
                    />
                    <p className="text-xs text-violet-400/50 mt-1">
                      PNG, JPG, or GIF. Max 2MB. Recommended size: 200x200px.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Primary Color */}
            <div className="space-y-4">
              <Label>Primary Color</Label>
              <div className="flex items-center gap-4">
                <div
                  className="h-12 w-12 rounded-lg ring-2 ring-white/20"
                  style={{ backgroundColor: primaryColor }}
                />
                <div className="flex-1">
                  <Input
                    type="color"
                    value={primaryColor}
                    onChange={(e) => handleColorChange(e.target.value)}
                    className="h-12 w-20 cursor-pointer"
                    disabled={updateOrgSettings.isPending}
                  />
                  <p className="text-xs text-violet-400/50 mt-1">
                    This color will be used for accents and highlights across the interface
                  </p>
                </div>
                <div className="flex gap-2">
                  {["#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"].map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => handleColorChange(color)}
                      className="h-8 w-8 rounded-md ring-2 ring-white/20 hover:ring-white/40 transition-all"
                      style={{ backgroundColor: color }}
                      disabled={updateOrgSettings.isPending}
                    />
                  ))}
                </div>
              </div>
            </div>

            <Button
              onClick={handleSaveOrg}
              variant="holo-primary"
              disabled={updateOrgSettings.isPending}
            >
              {updateOrgSettings.isPending ? "Saving..." : "Save Branding"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Allowed Domains */}
      {canEdit && (
        <Card className="glass-holo">
          <CardHeader>
            <CardTitle className="text-white">Allowed Domains</CardTitle>
            <CardDescription className="text-violet-300/70">
              Restrict sign-ups to specific email domains
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="example.com"
                onKeyPress={(e) => e.key === "Enter" && handleAddDomain()}
                className="bg-slate-950/50 border-violet-500/30 text-white"
              />
              <Button onClick={handleAddDomain} variant="holo-secondary">
                Add
              </Button>
            </div>

            <div className="space-y-2">
              {orgForm.allowed_domains?.map((domain) => (
                <div
                  key={domain}
                  className="flex items-center justify-between p-3 rounded-lg bg-violet-950/20 border border-violet-500/10"
                >
                  <span className="text-white">{domain}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRemoveDomain(domain)}
                    disabled={updateOrgSettings.isPending}
                  >
                    <Trash2 className="h-4 w-4 text-red-400" />
                  </Button>
                </div>
              ))}
              {(!orgForm.allowed_domains || orgForm.allowed_domains.length === 0) && (
                <p className="text-sm text-violet-400/50 text-center py-4">
                  No domains configured. Users from any email domain can join.
                </p>
              )}
            </div>

            <Button
              onClick={handleSaveOrg}
              variant="holo-primary"
              disabled={updateOrgSettings.isPending}
            >
              {updateOrgSettings.isPending ? "Saving..." : "Save Domains"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Danger Zone */}
      {user?.role === "owner" && (
        <Card className="glass-holo border-red-500/30">
          <CardHeader>
            <CardTitle className="text-red-400">Danger Zone</CardTitle>
            <CardDescription className="text-red-300/70">
              Irreversible actions for your organization
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-white">Delete Organization</p>
                <p className="text-sm text-violet-400">
                  Permanently delete your organization and all associated data
                </p>
              </div>
              <Button
                variant="destructive"
                onClick={() => {
                  if (confirm("Are you sure? This action cannot be undone.")) {
                    toast.info("Organization deletion is not yet implemented");
                  }
                }}
              >
                Delete Organization
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
