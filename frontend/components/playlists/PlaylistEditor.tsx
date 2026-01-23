"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PlaylistItem as PlaylistItemType, Asset, TransitionType } from "@/types";
import { GripVertical, Clock, Trash2, Plus } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils/cn";

interface PlaylistEditorProps {
  name?: string;
  items?: PlaylistItemType[];
  loopMode?: boolean;
  shuffleMode?: boolean;
  transitionType?: TransitionType;
  transitionDurationMs?: number;
  onSave?: (data: PlaylistEditorData) => void;
  onAddItem?: () => void;
  onRemoveItem?: (itemId: string) => void;
  onReorderItems?: (items: Array<{ id: string; order: number }>) => void;
  availableAssets?: Asset[];
}

export interface PlaylistEditorData {
  name: string;
  is_active: boolean;
  loop_mode: boolean;
  shuffle_mode: boolean;
  transition_type: TransitionType;
  transition_duration_ms: number;
  items: Array<{ asset_id: string; duration: number }>;
}

export function PlaylistEditor({
  name = "",
  items = [],
  loopMode = true,
  shuffleMode = false,
  transitionType = TransitionType.FADE,
  transitionDurationMs = 1000,
  onSave,
  onAddItem,
  onRemoveItem,
  onReorderItems,
  availableAssets = [],
}: PlaylistEditorProps) {
  const [formData, setFormData] = useState({
    name,
    is_active: true,
    loop_mode: loopMode,
    shuffle_mode: shuffleMode,
    transition_type: transitionType,
    transition_duration_ms: transitionDurationMs,
  });

  const handleSave = () => {
    onSave?.({
      ...formData,
      items: items.map((item) => ({
        asset_id: item.asset_id,
        duration: item.duration,
      })),
    });
  };

  const handleUpdateItemDuration = (itemId: string, duration: number) => {
    // This would update the item duration
    // In a real implementation, this would be handled by the parent component
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Playlist Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Playlist Settings</CardTitle>
          <CardDescription>Configure your playlist options</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Playlist Name</Label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="My Playlist"
            />
          </div>

          <div className="flex items-center justify-between">
            <Label>Active</Label>
            <Switch
              checked={formData.is_active}
              onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label>Loop Mode</Label>
            <Switch
              checked={formData.loop_mode}
              onCheckedChange={(checked) => setFormData({ ...formData, loop_mode: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label>Shuffle Mode</Label>
            <Switch
              checked={formData.shuffle_mode}
              onCheckedChange={(checked) => setFormData({ ...formData, shuffle_mode: checked })}
            />
          </div>

          <div className="space-y-2">
            <Label>Transition Type</Label>
            <Select
              value={formData.transition_type}
              onValueChange={(value) => setFormData({ ...formData, transition_type: value as TransitionType })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TransitionType.CUT}>Cut</SelectItem>
                <SelectItem value={TransitionType.FADE}>Fade</SelectItem>
                <SelectItem value={TransitionType.DISSOLVE}>Dissolve</SelectItem>
                <SelectItem value={TransitionType.WIPE}>Wipe</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Transition Duration (ms)</Label>
            <Input
              type="number"
              value={formData.transition_duration_ms}
              onChange={(e) => setFormData({ ...formData, transition_duration_ms: parseInt(e.target.value) })}
              min={0}
              max={10000}
              step={100}
            />
          </div>

          {onSave && (
            <Button onClick={handleSave} className="w-full">
              Save Playlist
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Playlist Items */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Playlist Items</CardTitle>
              <CardDescription>
                {items.length} item{items.length !== 1 ? "s" : ""}
              </CardDescription>
            </div>
            {onAddItem && (
              <Button size="sm" onClick={onAddItem}>
                <Plus className="mr-2 h-4 w-4" />
                Add Item
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No items in this playlist</p>
              {onAddItem && (
                <Button variant="outline" className="mt-4" onClick={onAddItem}>
                  Add First Item
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {items.map((item, index) => (
                <div
                  key={item.id}
                  className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent transition-colors"
                >
                  <div className="cursor-grab text-muted-foreground hover:text-foreground">
                    <GripVertical className="h-5 w-5" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{item.asset?.title || "Unknown Asset"}</p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{item.duration}s</span>
                      {item.asset?.file_size && (
                        <span>• {(item.asset.file_size / 1024 / 1024).toFixed(1)} MB</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground w-6 text-center">
                      #{index + 1}
                    </span>
                    {onRemoveItem && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onRemoveItem(item.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
