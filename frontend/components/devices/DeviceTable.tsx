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
  onCommand?: (id: string, command: string) => void;
}

export function DeviceTable({ devices, onCommand }: DeviceTableProps) {
  const isOnline = (device: Device) => {
    if (!device.last_heartbeat) return false;
    const lastSeen = new Date(device.last_heartbeat);
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return lastSeen > fiveMinutesAgo;
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Serial Number</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Location</TableHead>
            <TableHead>Last Seen</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {devices.length === 0 ? (
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
                <TableCell className="font-mono text-sm">{device.serial_number}</TableCell>
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
                <TableCell>{device.location || "-"}</TableCell>
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
                        onClick={() => onCommand?.(device.id, "restart")}
                      >
                        Restart
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
