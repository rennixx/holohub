"use client";

import Link from "next/link";
import { Device } from "@/types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DeviceStatusBadge } from "./DeviceStatusBadge";
import { formatDistanceToNow } from "date-fns";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { MoreHorizontal } from "lucide-react";

interface DeviceTableProps {
  devices: Device[];
  isLoading?: boolean;
  onCommand?: (id: string, command: string) => void;
}

// Loading skeleton
function TableSkeleton() {
  return (
    <>
      {[...Array(5)].map((_, i) => (
        <TableRow key={i}>
          <TableCell><div className="h-4 w-24 animate-pulse bg-muted rounded" /></TableCell>
          <TableCell><div className="h-4 w-32 animate-pulse bg-muted rounded" /></TableCell>
          <TableCell><div className="h-6 w-16 animate-pulse bg-muted rounded" /></TableCell>
          <TableCell><div className="h-4 w-20 animate-pulse bg-muted rounded" /></TableCell>
          <TableCell><div className="h-4 w-24 animate-pulse bg-muted rounded" /></TableCell>
          <TableCell><div className="h-8 w-8 animate-pulse bg-muted rounded" /></TableCell>
        </TableRow>
      ))}
    </>
  );
}

interface DeviceTableProps {
  devices: Device[];
  isLoading?: boolean;
  onCommand?: (id: string, command: string) => void;
}

export function DeviceTable({ devices, isLoading, onCommand }: DeviceTableProps) {
  const isOnline = (device: Device) => {
    if (!device.last_heartbeat) return false;
    const lastSeen = new Date(device.last_heartbeat);
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return lastSeen > fiveMinutesAgo;
  };

  const getLocation = (device: Device) => {
    const meta = device.location_metadata;
    if (!meta || typeof meta !== "object") return "-";
    if (meta.building && meta.floor) return `${meta.building} - Floor ${meta.floor}`;
    if (meta.building) return meta.building as string;
    if (meta.room) return meta.room as string;
    return "-";
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Hardware ID</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Location</TableHead>
            <TableHead>Last Seen</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableSkeleton />
          ) : devices.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                No devices found
              </TableCell>
            </TableRow>
          ) : (
            devices.map((device) => (
              <TableRow key={device.id}>
                <TableCell className="font-medium">
                  <Link href={`/devices/${device.id}`} className="hover:underline">
                    {device.name}
                  </Link>
                </TableCell>
                <TableCell className="font-mono text-sm">{device.hardware_id}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <DeviceStatusBadge status={device.status} />
                    {isOnline(device) && (
                      <Badge variant="outline" className="text-green-500 border-green-500">
                        Online
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>{getLocation(device)}</TableCell>
                <TableCell>
                  {device.last_heartbeat
                    ? formatDistanceToNow(new Date(device.last_heartbeat), { addSuffix: true })
                    : "Never"}
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                        <span className="sr-only">Actions</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem asChild>
                        <Link href={`/devices/${device.id}`}>View Details</Link>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onCommand?.(device.id, "refresh")}
                      >
                        Refresh Content
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onCommand?.(device.id, "reboot")}
                      >
                        Reboot
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onCommand?.(device.id, "clear_cache")}
                      >
                        Clear Cache
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onCommand?.(device.id, "screenshot")}
                      >
                        Take Screenshot
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
