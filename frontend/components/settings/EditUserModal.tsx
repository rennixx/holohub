/**
 * Edit User Modal
 *
 * Modal for editing a user's role and status.
 */
"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Loader2 } from "lucide-react";
import { usersApi, type User, type UserUpdate } from "@/lib/api/users";
import { cn } from "@/lib/utils/cn";

interface EditUserModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: User | null;
  onSuccess?: () => void;
}

export function EditUserModal({ open, onOpenChange, user, onSuccess }: EditUserModalProps) {
  const [formData, setFormData] = useState<UserUpdate>({
    full_name: "",
    role: "viewer",
    is_active: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset form when user changes
  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name,
        role: user.role,
        is_active: user.is_active ?? true,
      });
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) return;

    setIsSubmitting(true);

    try {
      await usersApi.update(user.id, formData);
      toast.success("User updated successfully");
      onOpenChange(false);
      onSuccess?.();
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to update user";
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onOpenChange(false);
    }
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="glass-holo border-violet-500/30 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-white">Edit Team Member</DialogTitle>
          <DialogDescription className="text-violet-300/70">
            Manage {user.full_name || user.email}'s account
          </DialogDescription>
        </DialogHeader>

        {/* User Info */}
        <div className="flex items-center gap-4 py-4">
          <div className="h-12 w-12 rounded-full bg-gradient-to-br from-violet-600 to-cyan-500 flex items-center justify-center text-white font-semibold">
            {user.full_name?.split(" ").map((n) => n[0]).join("").toUpperCase() || user.email[0].toUpperCase()}
          </div>
          <div>
            <p className="font-medium text-white">{user.full_name}</p>
            <p className="text-sm text-violet-400">{user.email}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Full Name */}
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="John Doe"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                disabled={isSubmitting}
                className="bg-slate-950/50 border-violet-500/30 text-white"
              />
            </div>

            {/* Role */}
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Select
                value={formData.role}
                onValueChange={(value) => setFormData({ ...formData, role: value })}
                disabled={isSubmitting}
              >
                <SelectTrigger id="role" className="bg-slate-950/50 border-violet-500/30 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="glass-holo border-violet-500/30">
                  <SelectItem value="owner">Owner - Full access</SelectItem>
                  <SelectItem value="admin">Admin - Manage users & settings</SelectItem>
                  <SelectItem value="editor">Editor - Manage content</SelectItem>
                  <SelectItem value="viewer">Viewer - Read-only access</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Active Status */}
            <div className="flex items-center justify-between p-4 rounded-lg bg-violet-950/20 border border-violet-500/10">
              <div>
                <Label>Account Status</Label>
                <p className="text-sm text-violet-400">
                  {formData.is_active ? "User can access the platform" : "User account is deactivated"}
                </p>
              </div>
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                disabled={isSubmitting}
              />
            </div>

            {/* Warning for deactivation */}
            {!formData.is_active && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                <p className="text-sm text-amber-400">
                  ⚠️ Deactivating this user will prevent them from accessing the platform immediately.
                </p>
              </div>
            )}
          </div>

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={handleClose}
              disabled={isSubmitting}
              className="text-violet-300 hover:text-white hover:bg-violet-600/20"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="holo-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
