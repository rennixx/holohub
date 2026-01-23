"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DeviceTable, DeviceMap } from "@/components/devices";
import { devicesApi } from "@/api";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { Device } from "@/types";
import { toast } from "sonner";

export default function DevicesPage() {
  const router = useRouter();
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["devices"],
    queryFn: async () => {
      return await devicesApi.list();
    },
  });

  const handleCommand = async (id: string, command: string) => {
    try {
      await devicesApi.sendCommand(id, { command: command as any });
      toast.success("Command sent successfully");
    } catch (error) {
      toast.error("Failed to send command");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Devices</h1>
          <p className="text-muted-foreground">
            Manage your holographic display fleet
          </p>
        </div>
        <Button onClick={() => router.push("/devices/register")}>
          <Plus className="mr-2 h-4 w-4" />
          Register Device
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>All Devices</CardTitle>
              <CardDescription>
                {data?.meta.total || 0} device{data?.meta.total !== 1 ? "s" : ""} registered
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DeviceTable
                devices={data?.items || []}
                isLoading={isLoading}
                onCommand={handleCommand}
              />
            </CardContent>
          </Card>
        </div>

        <div>
          <DeviceMap
            devices={data?.items || []}
            onDeviceClick={(device) => router.push(`/devices/${device.id}`)}
          />
        </div>
      </div>
    </div>
  );
}
