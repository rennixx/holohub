"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DeviceStatusBadge, DeviceHealthCard, DeviceCommandPanel } from "@/components/devices";
import { devicesApi } from "@/api";
import { formatDistanceToNow } from "date-fns";
import { ArrowLeft, MapPin, Cpu } from "lucide-react";
import Link from "next/link";
import { Device } from "@/types";
import { toast } from "sonner";

export default function DeviceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const deviceId = params.id as string;

  const { data: device, isLoading } = useQuery({
    queryKey: ["device", deviceId],
    queryFn: () => devicesApi.get(deviceId),
    enabled: !!deviceId,
  });

  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ["device-health", deviceId],
    queryFn: async () => {
      const data = await devicesApi.getHealth(deviceId);
      return data[0]; // Get latest heartbeat
    },
    enabled: !!deviceId && device?.status === "active",
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const handleCommandSent = () => {
    refetchHealth();
  };

  const isOnline = (device: Device) => {
    if (!device.last_heartbeat) return false;
    const lastSeen = new Date(device.last_heartbeat);
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return lastSeen > fiveMinutesAgo;
  };

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
            Serial: {device.serial_number}
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
                  <dt className="text-sm text-muted-foreground">Serial Number</dt>
                  <dd className="font-mono text-sm">{device.serial_number}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Hardware ID</dt>
                  <dd className="font-mono text-sm">{device.hardware_id}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Location</dt>
                  <dd className="font-medium flex items-center gap-1">
                    {device.location ? (
                      <>
                        <MapPin className="h-4 w-4" />
                        {device.location}
                      </>
                    ) : (
                      "Not set"
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Resolution</dt>
                  <dd className="font-medium">{device.display_config.resolution}</dd>
                </div>
                <div>
                  <dt className="text-sm text-muted-foreground">Orientation</dt>
                  <dd className="font-medium capitalize">{device.display_config.orientation}</dd>
                </div>
                {device.network_info && (
                  <>
                    <div>
                      <dt className="text-sm text-muted-foreground">IP Address</dt>
                      <dd className="font-mono text-sm">{device.network_info.ip_address}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-muted-foreground">WiFi</dt>
                      <dd className="font-medium">{device.network_info.wifi_ssid || "N/A"}</dd>
                    </div>
                  </>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Health Metrics */}
          {health && <DeviceHealthCard health={health} />}
        </div>

        {/* Commands */}
        <div>
          <DeviceCommandPanel deviceId={device.id} onCommandSent={handleCommandSent} />
        </div>
      </div>
    </div>
  );
}
