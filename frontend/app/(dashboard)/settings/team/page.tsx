"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { usersApi } from "@/lib/api";
import { InviteUserModal } from "@/components/settings/InviteUserModal";
import { EditUserModal } from "@/components/settings/EditUserModal";
import { DeleteConfirmDialog } from "@/components/settings/DeleteConfirmDialog";
import { Plus, Edit, Trash2 } from "lucide-react";
import { UserRole } from "@/types";
import { useAuthStore } from "@/lib/store";

export default function TeamSettingsPage() {
  const { user: currentUser } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      return await usersApi.list();
    },
  });

  // Modal states
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<typeof users.items[0] | null>(null);

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => usersApi.delete(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast.success("User removed successfully");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to remove user";
      toast.error(message);
    },
  });

  const handleDeleteUser = async () => {
    if (selectedUser) {
      await deleteUserMutation.mutateAsync(selectedUser.id);
    }
  };

  const canManageUsers = currentUser?.role === "owner" || currentUser?.role === "admin";

  const getRoleBadgeColor = (role: UserRole) => {
    switch (role) {
      case UserRole.OWNER:
        return "bg-purple-500";
      case UserRole.ADMIN:
        return "bg-blue-500";
      case UserRole.EDITOR:
        return "bg-green-500";
      case UserRole.VIEWER:
        return "bg-gray-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Team</h1>
          <p className="text-muted-foreground">
            Manage users and permissions
          </p>
        </div>
        {canManageUsers && (
          <Button onClick={() => setInviteModalOpen(true)} variant="holo-primary">
            <Plus className="mr-2 h-4 w-4" />
            Invite User
          </Button>
        )}
      </div>

      <Card className="glass-holo">
        <CardHeader>
          <CardTitle className="text-white">Team Members</CardTitle>
          <CardDescription className="text-violet-300/70">
            {users?.meta.total || 0} member{users?.meta.total !== 1 ? "s" : ""}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users?.items.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium text-white">{user.full_name}</TableCell>
                    <TableCell className="text-violet-300">{user.email}</TableCell>
                    <TableCell>
                      <Badge className={getRoleBadgeColor(user.role)}>
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.is_active ? (
                        <Badge variant="outline" className="text-green-500 border-green-500">
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-red-500 border-red-500">
                          Inactive
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {canManageUsers && (
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedUser(user);
                              setEditModalOpen(true);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedUser(user);
                              setDeleteModalOpen(true);
                            }}
                            disabled={user.id === currentUser?.id}
                          >
                            <Trash2 className="h-4 w-4 text-red-400" />
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      <InviteUserModal
        open={inviteModalOpen}
        onOpenChange={setInviteModalOpen}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ["users"] })}
      />

      <EditUserModal
        open={editModalOpen}
        onOpenChange={setEditModalOpen}
        user={selectedUser}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ["users"] })}
      />

      <DeleteConfirmDialog
        open={deleteModalOpen}
        onOpenChange={setDeleteModalOpen}
        title="Remove Team Member"
        message={`Are you sure you want to remove ${selectedUser?.full_name || selectedUser?.email} from your organization? They will lose access to all resources.`}
        confirmText="Remove User"
        requiresConfirmation={selectedUser?.role === "owner"}
        confirmationText={selectedUser?.full_name || ""}
        onConfirm={handleDeleteUser}
      />
    </div>
  );
}
