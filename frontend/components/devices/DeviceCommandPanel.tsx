"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RefreshCw, Trash2, Image, ListMusic } from "lucide-react";
import { toast } from "sonner";

interface DeviceCommandPanelProps {
  deviceId: string;
  onCommandSent?: () => void;
}

type Command = "restart" | "clear_cache" | "screenshot" | "update_playlist";

export function DeviceCommandPanel({ deviceId, onCommandSent }: DeviceCommandPanelProps) {
  const [command, setCommand] = useState<Command>("restart");
  const [playlistId, setPlaylistId] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSendCommand = async () => {
    setIsLoading(true);

    try {
      let params = {};
      if (command === "update_playlist") {
        if (!playlistId) {
          toast.error("Please enter a playlist ID");
          setIsLoading(false);
          return;
        }
        params = { playlist_id: playlistId };
      }

      const response = await fetch(`/api/devices/${deviceId}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command, params }),
      });

      if (!response.ok) throw new Error("Failed to send command");

      toast.success("Command sent successfully");
      onCommandSent?.();
    } catch (error) {
      toast.error("Failed to send command");
    } finally {
      setIsLoading(false);
    }
  };

  const commands = [
    { value: "restart", label: "Restart Device", icon: RefreshCw, description: "Restart the device" },
    { value: "clear_cache", label: "Clear Cache", icon: Trash2, description: "Clear local asset cache" },
    { value: "screenshot", label: "Take Screenshot", icon: Image, description: "Capture current display" },
    { value: "update_playlist", label: "Update Playlist", icon: ListMusic, description: "Assign a new playlist" },
  ];

  const selectedCommand = commands.find((c) => c.value === command);
  const Icon = selectedCommand?.icon || RefreshCw;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Device Commands</CardTitle>
        <CardDescription>Send remote commands to the device</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Command</Label>
          <Select value={command} onValueChange={(v) => setCommand(v as Command)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {commands.map((cmd) => (
                <SelectItem key={cmd.value} value={cmd.value}>
                  <div className="flex items-center gap-2">
                    <cmd.icon className="h-4 w-4" />
                    <span>{cmd.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedCommand && (
            <p className="text-xs text-muted-foreground">{selectedCommand.description}</p>
          )}
        </div>

        {command === "update_playlist" && (
          <div className="space-y-2">
            <Label>Playlist ID</Label>
            <Input
              value={playlistId}
              onChange={(e) => setPlaylistId(e.target.value)}
              placeholder="Enter playlist ID"
            />
          </div>
        )}

        <Button onClick={handleSendCommand} disabled={isLoading} className="w-full">
          {isLoading ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Sending...
            </>
          ) : (
            <>
              <Icon className="mr-2 h-4 w-4" />
              Send Command
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
