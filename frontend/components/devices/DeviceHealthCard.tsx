import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Cpu, HardDrive, Activity, Thermometer } from "lucide-react";
import { DeviceHeartbeat } from "@/types";

interface DeviceHealthCardProps {
  health: DeviceHeartbeat;
}

export function DeviceHealthCard({ health }: DeviceHealthCardProps) {
  const getHealthColor = (percent: number) => {
    if (percent < 50) return "text-green-500";
    if (percent < 75) return "text-yellow-500";
    return "text-red-500";
  };

  const metrics = [
    {
      label: "CPU",
      value: health.cpu_percent,
      icon: Cpu,
      color: getHealthColor(health.cpu_percent),
    },
    {
      label: "Memory",
      value: health.memory_percent,
      icon: Activity,
      color: getHealthColor(health.memory_percent),
    },
    {
      label: "Disk",
      value: health.disk_percent,
      icon: HardDrive,
      color: getHealthColor(health.disk_percent),
    },
    {
      label: "Temperature",
      value: health.temperature_celsius ? (health.temperature_celsius / 100) * 100 : 0,
      icon: Thermometer,
      color: getHealthColor(health.temperature_celsius ? (health.temperature_celsius / 100) * 100 : 0),
      display: health.temperature_celsius ? `${health.temperature_celsius.toFixed(1)}°C` : undefined,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Device Health</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <div key={metric.label} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${metric.color}`} />
                  <span className="font-medium">{metric.label}</span>
                </div>
                <span className={metric.color}>
                  {metric.display || `${metric.value.toFixed(0)}%`}
                </span>
              </div>
              <Progress value={metric.value} className="h-2" />
            </div>
          );
        })}

        <div className="pt-2 border-t text-xs text-muted-foreground">
          Uptime: {Math.floor(health.uptime_seconds / 3600)}h {Math.floor((health.uptime_seconds % 3600) / 60)}m
        </div>
      </CardContent>
    </Card>
  );
}
