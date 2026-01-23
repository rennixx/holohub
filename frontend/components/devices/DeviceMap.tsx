"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Device, DeviceStatus } from "@/types";
import { Badge } from "@/components/ui/badge";
import { MapPin, Wifi, WifiOff } from "lucide-react";

interface DeviceMapProps {
  devices: Device[];
  onDeviceClick?: (device: Device) => void;
}

/**
 * Simple Device Map Component
 * Displays devices as a list with location indicators
 * For a full map implementation, integrate with Leaflet
 */
export function DeviceMap({ devices, onDeviceClick }: DeviceMapProps) {
  const [hasLocation, setHasLocation] = useState(false);

  useEffect(() => {
    setHasLocation(devices.some((d) => d.location));
  }, [devices]);

  const isOnline = (device: Device) => {
    if (!device.last_heartbeat) return false;
    const lastSeen = new Date(device.last_heartbeat);
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return lastSeen > fiveMinutesAgo;
  };

  const getStatusColor = (status: DeviceStatus) => {
    switch (status) {
      case DeviceStatus.ACTIVE:
        return "bg-green-500";
      case DeviceStatus.OFFLINE:
        return "bg-red-500";
      case DeviceStatus.MAINTENANCE:
        return "bg-orange-500";
      case DeviceStatus.PENDING:
        return "bg-yellow-500";
      default:
        return "bg-gray-500";
    }
  };

  if (!hasLocation) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Device Map</CardTitle>
          <CardDescription>Geographic view of your devices</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <MapPin className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-sm text-muted-foreground">
              No devices with location data found
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Add location information to devices to see them on the map
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Device Map</CardTitle>
        <CardDescription>Geographic view of your devices</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {devices.filter((d) => d.location).map((device) => (
            <div
              key={device.id}
              onClick={() => onDeviceClick?.(device)}
              className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${getStatusColor(device.status)}`} />
                <div>
                  <p className="font-medium">{device.name}</p>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {device.location}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {isOnline(device) ? (
                  <Wifi className="h-4 w-4 text-green-500" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-500" />
                )}
                <Badge variant="outline">{device.status}</Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
