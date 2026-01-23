import { Badge } from "@/components/ui/badge";
import { DeviceStatus } from "@/types";
import { cn } from "@/lib/utils/cn";

interface DeviceStatusBadgeProps {
  status: DeviceStatus;
}

const statusConfig: Record<DeviceStatus, { label: string; className: string }> = {
  [DeviceStatus.PENDING]: { label: "Pending", className: "bg-yellow-500/10 text-yellow-500" },
  [DeviceStatus.ACTIVE]: { label: "Active", className: "bg-green-500/10 text-green-500" },
  [DeviceStatus.OFFLINE]: { label: "Offline", className: "bg-red-500/10 text-red-500" },
  [DeviceStatus.MAINTENANCE]: { label: "Maintenance", className: "bg-orange-500/10 text-orange-500" },
  [DeviceStatus.DECOMMISSIONED]: { label: "Decommissioned", className: "bg-gray-500/10 text-gray-500" },
};

export function DeviceStatusBadge({ status }: DeviceStatusBadgeProps) {
  const config = statusConfig[status];
  return <Badge className={cn("", config.className)}>{config.label}</Badge>;
}
