"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { PlaylistEditor, type PlaylistEditorData } from "@/components/playlists";
import { playlistsApi, assetsApi } from "@/api";
import { toast } from "sonner";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NewPlaylistPage() {
  const router = useRouter();
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);

  const { data: assets } = useQuery({
    queryKey: ["assets"],
    queryFn: async () => {
      return await assetsApi.list({ page_size: 100 });
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: PlaylistEditorData) => {
      return await playlistsApi.create(data);
    },
    onSuccess: (playlist) => {
      toast.success("Playlist created successfully!");
      router.push(`/playlists/${playlist.id}`);
    },
    onError: () => {
      toast.error("Failed to create playlist");
    },
  });

  const handleAddItems = () => {
    // Open asset selection dialog
    // For now, just add all assets
    if (assets) {
      setSelectedAssetIds(assets.items.slice(0, 3).map((a) => a.id));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/playlists">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">New Playlist</h1>
          <p className="text-muted-foreground">
            Create a new content playlist
          </p>
        </div>
      </div>

      <PlaylistEditor
        onSave={(data) => createMutation.mutate(data)}
        onAddItem={handleAddItems}
        availableAssets={assets?.items || []}
      />
    </div>
  );
}
