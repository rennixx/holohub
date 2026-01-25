"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DeviceStatusBadge, DeviceCommandPanel } from "@/components/devices";
import { devicesApi, playlistsApi } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { ArrowLeft, MapPin, Cpu, ListVideo, Loader2, Key, RefreshCw, Copy, Check } from "lucide-react";
import Link from "next/link";
import { Device } from "@/types";
import { toast } from "sonner";
import { useState } from "react";

// Import Dialog components
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export default function DeviceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const deviceId = params.id as string;
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string | null>(null);

  const { data: device, isLoading } = useQuery({
    queryKey: ["device", deviceId],
    queryFn: () => devicesApi.get(deviceId),
    enabled: !!deviceId,
  });

  const { data: playlists } = useQuery({
    queryKey: ["playlists"],
    queryFn: async () => {
      const result = await playlistsApi.list({ page: 1, page_size: 100 });
      return result.items;
    },
  });

  const assignPlaylistMutation = useMutation({
    mutationFn: (playlistId: string) => devicesApi.assignPlaylist(deviceId, playlistId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device", deviceId] });
      toast.success("Playlist assigned to device");
      setSelectedPlaylistId(null);
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : "Failed to assign playlist");
    },
  });

  const handleAssignPlaylist = () => {
    if (selectedPlaylistId) {
      assignPlaylistMutation.mutate(selectedPlaylistId);
    }
  };

  const isOnline = (device: Device) => {
    if (!device.last_heartbeat) return false;
    const lastSeen = new Date(device.last_heartbeat);
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return lastSeen > fiveMinutesAgo;
  };

  const getLocation = (device: Device) => {
    const meta = device.location_metadata;
    if (!meta || typeof meta !== "object") return null;
    if (meta.building && meta.floor) return `${meta.building as string} - Floor ${meta.floor as string}`;
    if (meta.building) return meta.building as string;
    if (meta.room) return meta.room as string;
    return null;
  };

  const activePlaylists = playlists?.filter((p) => p.is_active && p.item_count > 0) || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
          <p className="mt-2 text-sm text-muted-foreground">Loading device...</p>
        </div>
      </div>
    );
  }

  if (!device) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-lg font-medium">Device not found</p>
          <Link href="/devices">
            <Button className="mt-4">Back to Devices</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/devices">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{device.name}</h1>
            <DeviceStatusBadge status={device.status} />
            {isOnline(device) && (
              <Badge variant="outline" className="text-green-500 border-green-500">
                Online
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground">
            Hardware ID: {device.hardware_id}
            {device.last_heartbeat &&
              ` • Last seen ${formatDistanceToNow(new Date(device.last_heartbeat), { addSuffix: true })}`}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Device Info */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Device Information</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-sm text-muted-foreground">Name</dt>
                  <dd className="font-medium">{device.name}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Hardware Type</dt>
                  <dd className="font-medium capitalize">{device.hardware_type.replace(/_/g, " ")}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Hardware ID</dt>
                  <dd className="font-mono text-sm">{device.hardware_id}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Location</dt>
                  <dd className="font-medium flex items-center gap-1">
                    {getLocation(device) ? (
                      <>
                        <MapPin className="h-4 w-4" />
                        {getLocation(device)}
                      </>
                    ) : (
                      "Not set"
                    )}
                  </dd>
                </div>
                {device.display_config && typeof device.display_config === "object" && (
                  <>
                    {"resolution" in device.display_config && (
                      <div>
                        <dt className="text-sm text-muted-foreground">Resolution</dt>
                        <dd className="font-medium">{String(device.display_config.resolution)}</dd>
                      </div>
                    )}
                    {"orientation" in device.display_config && (
                      <div>
                        <dt className="text-sm text-muted-foreground">Orientation</dt>
                        <dd className="font-medium capitalize">{String(device.display_config.orientation)}</dd>
                      </div>
                    )}
                  </>
                )}
                {device.network_info && typeof device.network_info === "object" && (
                  <>
                    {"ip_address" in device.network_info && (
                      <div>
                        <dt className="text-sm text-muted-foreground">IP Address</dt>
                        <dd className="font-mono text-sm">{String(device.network_info.ip_address)}</dd>
                      </div>
                    )}
                    {"wifi_ssid" in device.network_info && (
                      <div>
                        <dt className="text-sm text-muted-foreground">WiFi</dt>
                        <dd className="font-medium">{String(device.network_info.wifi_ssid || "N/A")}</dd>
                      </div>
                    )}
                  </>
                )}
                {device.firmware_version && (
                  <div>
                    <dt className="text-sm text-muted-foreground">Firmware</dt>
                    <dd className="font-medium">{device.firmware_version}</dd>
                  </div>
                )}
                {device.client_version && (
                  <div>
                    <dt className="text-sm text-muted-foreground">Client</dt>
                    <dd className="font-medium">{device.client_version}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Playlist Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ListVideo className="h-5 w-5" />
                Assigned Playlist
              </CardTitle>
              <CardDescription>
                Assign a playlist to this device for content playback
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {device.current_playlist_id ? (
                <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
                  <div>
                    <p className="font-medium">Playlist assigned</p>
                    <p className="text-sm text-muted-foreground">ID: {device.current_playlist_id}</p>
                  </div>
                  <Badge variant="secondary" className="bg-green-100 text-green-800">
                    Active
                  </Badge>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No playlist assigned to this device.</p>
              )}

              <div className="space-y-2">
                <Label htmlFor="playlist-select">Assign Playlist</Label>
                <div className="flex gap-2">
                  <Select
                    value={selectedPlaylistId || ""}
                    onValueChange={setSelectedPlaylistId}
                  >
                    <SelectTrigger id="playlist-select" className="flex-1">
                      <SelectValue placeholder="Select a playlist" />
                    </SelectTrigger>
                    <SelectContent>
                      {activePlaylists.length === 0 ? (
                        <div className="p-2 text-sm text-muted-foreground text-center">
                          No active playlists with items
                        </div>
                      ) : (
                        activePlaylists.map((playlist) => (
                          <SelectItem key={playlist.id} value={playlist.id}>
                            {playlist.name} ({playlist.item_count} items)
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  <Button
                    onClick={handleAssignPlaylist}
                    disabled={!selectedPlaylistId || assignPlaylistMutation.isPending}
                  >
                    {assignPlaylistMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Assigning
                      </>
                    ) : (
                      "Assign"
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Commands */}
        <div>
          <DeviceCommandPanel deviceId={device.id} />
        </div>
      </div>
    </div>
  );
}
