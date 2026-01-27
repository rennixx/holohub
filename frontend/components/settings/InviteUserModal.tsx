/**
 * Invite User Modal
 *
 * Modal for inviting a new user to the organization.
 */
"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { usersApi, type UserInvite } from "@/lib/api/users";

interface InviteUserModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function InviteUserModal({ open, onOpenChange, onSuccess }: InviteUserModalProps) {
  const [formData, setFormData] = useState<UserInvite>({
    email: "",
    full_name: "",
    role: "viewer",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.email || !formData.email.includes("@")) {
      toast.error("Please enter a valid email address");
      return;
    }

    if (!formData.full_name || formData.full_name.trim().length < 2) {
      toast.error("Please enter the user's full name");
      return;
    }

    setIsSubmitting(true);

    try {
      await usersApi.invite(formData);
      toast.success("User invited successfully");
      setFormData({ email: "", full_name: "", role: "viewer" });
      onOpenChange(false);
      onSuccess?.();
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Failed to invite user";
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFormData({ email: "", full_name: "", role: "viewer" });
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="glass-holo border-violet-500/30 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-white">Invite Team Member</DialogTitle>
          <DialogDescription className="text-violet-300/70">
            Send an invitation to join your organization
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="colleague@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                disabled={isSubmitting}
                className="bg-slate-950/50 border-violet-500/30 text-white"
              />
            </div>

            {/* Full Name */}
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="John Doe"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
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
              <p className="text-xs text-violet-400/50 mt-1">
                {formData.role === "owner" && "Has full control over the organization"}
                {formData.role === "admin" && "Can manage users, devices, and playlists"}
                {formData.role === "editor" && "Can manage devices and playlists"}
                {formData.role === "viewer" && "Can only view content"}
              </p>
            </div>
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
                  Sending...
                </>
              ) : (
                "Send Invitation"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

