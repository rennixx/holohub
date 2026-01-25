"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { playlistsApi, assetsApi } from "@/lib/api";
import { ArrowLeft, Plus, Trash2, Loader2, Clock, GripVertical } from "lucide-react";
import Link from "next/link";
import { Playlist, PlaylistItem, Asset } from "@/types";
import { toast } from "sonner";
import { useState } from "react";

export default function EditPlaylistPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const playlistId = params.id as string;
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [itemDuration, setItemDuration] = useState("10");

  const { data: playlist, isLoading } = useQuery({
    queryKey: ["playlist", playlistId],
    queryFn: () => playlistsApi.get(playlistId),
    enabled: !!playlistId,
  });

  const { data: assets } = useQuery({
    queryKey: ["assets"],
    queryFn: async () => {
      const result = await assetsApi.list({ page: 1, page_size: 100 });
      return result.items;
    },
  });

  const addItemMutation = useMutation({
    mutationFn: (data: { asset_id: string; duration: number }) =>
      playlistsApi.addItem(playlistId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["playlist", playlistId] });
      toast.success("Item added to playlist");
      setSelectedAssetId(null);
      setItemDuration("10");
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to add item");
    },
  });

  const removeItemMutation = useMutation({
    mutationFn: (itemId: string) => playlistsApi.removeItem(playlistId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["playlist", playlistId] });
      toast.success("Item removed from playlist");
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to remove item");
    },
  });

  const handleAddItem = () => {
    if (selectedAssetId) {
      addItemMutation.mutate({
        asset_id: selectedAssetId,
        duration: parseInt(itemDuration) || 10,
      });
    }
  };

  const handleRemoveItem = (itemId: string) => {
    removeItemMutation.mutate(itemId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
          <p className="mt-2 text-sm text-muted-foreground">Loading playlist...</p>
        </div>
      </div>
    );
  }

  if (!playlist) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-lg font-medium">Playlist not found</p>
          <Link href="/playlists">
            <Button className="mt-4">Back to Playlists</Button>
          </Link>
        </div>
      </div>
    );
  }

  const readyAssets = assets?.filter((a) => a.processing_status === "completed") || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/playlists/${playlistId}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">Edit Playlist</h1>
          <p className="text-muted-foreground">{playlist.name}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Playlist Items */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Playlist Items</CardTitle>
              <CardDescription>
                {playlist.item_count} item{playlist.item_count !== 1 ? "s" : ""} in this playlist
              </CardDescription>
            </CardHeader>
            <CardContent>
              {playlist.items && playlist.items.length > 0 ? (
                <div className="space-y-2">
                  {playlist.items.map((item, index) => (
                    <div
                      key={item.id}
                      className="flex items-center gap-3 p-3 rounded-lg border bg-card group"
                    >
                      <GripVertical className="h-4 w-4 text-muted-foreground cursor-move" />
                      <span className="text-xs text-muted-foreground w-6 text-center">
                        #{index + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{item.asset?.title || "Unknown Asset"}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{item.duration}s</span>
                          {item.asset?.category && (
                            <>
                              <span>•</span>
                              <span className="capitalize">{item.asset.category}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemoveItem(item.id)}
                        className="opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <p>No items in this playlist</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Add Item */}
          <Card>
            <CardHeader>
              <CardTitle>Add Item</CardTitle>
              <CardDescription>Add an asset to this playlist</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="asset-select">Asset</Label>
                <Select
                  value={selectedAssetId || ""}
                  onValueChange={setSelectedAssetId}
                >
                  <SelectTrigger id="asset-select">
                    <SelectValue placeholder="Select an asset" />
                  </SelectTrigger>
                  <SelectContent>
                    {readyAssets.length === 0 ? (
                      <div className="p-2 text-sm text-muted-foreground text-center">
                        No ready assets available
                      </div>
                    ) : (
                      readyAssets.map((asset) => (
                        <SelectItem key={asset.id} value={asset.id}>
                          {asset.title}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="duration">Duration (seconds)</Label>
                <Input
                  id="duration"
                  type="number"
                  min="1"
                  value={itemDuration}
                  onChange={(e) => setItemDuration(e.target.value)}
                  placeholder="10"
                />
              </div>

              <Button
                onClick={handleAddItem}
                disabled={!selectedAssetId || addItemMutation.isPending}
                className="w-full"
              >
                {addItemMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Adding...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    Add to Playlist
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Playlist Settings */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Settings</CardTitle>
              <CardDescription>Configure playlist behavior</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="loop-mode">Loop Mode</Label>
                <Switch
                  id="loop-mode"
                  checked={playlist.loop_mode}
                  disabled
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="shuffle-mode">Shuffle Mode</Label>
                <Switch
                  id="shuffle-mode"
                  checked={playlist.shuffle_mode}
                  disabled
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="transition">Transition Type</Label>
                <Select value={playlist.transition_type} disabled>
                  <SelectTrigger id="transition">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cut">Cut</SelectItem>
                    <SelectItem value="fade">Fade</SelectItem>
                    <SelectItem value="slide_left">Slide Left</SelectItem>
                    <SelectItem value="slide_right">Slide Right</SelectItem>
                    <SelectItem value="zoom">Zoom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="transition-duration">Transition Duration (ms)</Label>
                <Input
                  id="transition-duration"
                  type="number"
                  value={playlist.transition_duration_ms}
                  disabled
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
