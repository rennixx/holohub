"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, Environment, Grid, useGLTF, useProgress, Html } from "@react-three/drei";
import * as THREE from "three";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface ThreeDPreviewProps {
  src: string;
  autoRotate?: boolean;
  showGrid?: boolean;
  className?: string;
  onLoaded?: () => void;
  onError?: (error: Error) => void;
}

/**
 * 3D Model Component
 * Loads and renders a GLB/GLTF model
 */
function Model({ src, onLoaded, onError }: { src: string; onLoaded?: () => void; onError?: (error: Error) => void }) {
  const groupRef = useRef<THREE.Group>(null);
  const { scene } = useGLTF(src, true, undefined, (error) => {
    onError?.(error);
  });

  useEffect(() => {
    if (scene) {
      onLoaded?.();
    }
  }, [scene, onLoaded]);

  return <primitive ref={groupRef} object={scene} />;
}

/**
 * Loading Progress Component
 */
function LoadingProgress() {
  const { progress } = useProgress();

  return (
    <Html center>
      <div className="flex flex-col items-center gap-2">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm font-medium">Loading 3D model...</p>
        <p className="text-xs text-muted-foreground">{progress.toFixed(0)}%</p>
      </div>
    </Html>
  );
}

/**
 * Error Display Component
 */
interface ErrorDisplayProps {
  error: string;
  onRetry?: () => void;
}

function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  return (
    <Html center>
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center max-w-xs">
        <p className="text-sm font-medium text-destructive">Failed to load model</p>
        <p className="text-xs text-muted-foreground mt-1">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 px-3 py-1 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        )}
      </div>
    </Html>
  );
}

/**
 * Main ThreeDPreview Component
 * Provides a 3D viewer for GLB/GLTF files
 */
export function ThreeDPreview({ src, autoRotate = false, showGrid = true, className, onLoaded, onError }: ThreeDPreviewProps) {
  const [error, setError] = useState<string | null>(null);
  const [key, setKey] = useState(0);

  const handleError = (err: Error) => {
    setError(err.message);
    onError?.(err);
  };

  const handleRetry = () => {
    setError(null);
    setKey((prev) => prev + 1);
  };

  return (
    <div className={cn("relative w-full h-full bg-muted rounded-lg overflow-hidden", className)}>
      <Canvas
        key={key}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        className="three-canvas"
      >
        <Suspense fallback={<LoadingProgress />}>
          {error ? (
            <ErrorDisplay error={error} onRetry={handleRetry} />
          ) : (
            <>
              {/* Lighting */}
              <ambientLight intensity={0.5} />
              <directionalLight position={[10, 10, 5]} intensity={1} />
              <pointLight position={[-10, -10, -5]} intensity={0.5} />

              {/* Environment for reflections */}
              <Environment preset="sunset" />

              {/* Camera */}
              <PerspectiveCamera makeDefault position={[0, 2, 5]} fov={50} />

              {/* Controls */}
              <OrbitControls
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                autoRotate={autoRotate}
                autoRotateSpeed={1}
                minDistance={2}
                maxDistance={10}
              />

              {/* Grid */}
              {showGrid && (
                <Grid
                  args={[10, 10]}
                  cellSize={1}
                  cellThickness={0.5}
                  cellColor="#6366f1"
                  sectionSize={5}
                  sectionThickness={1}
                  sectionColor="#6366f1"
                  fadeDistance={25}
                  fadeStrength={1}
                  followCamera={false}
                  infiniteGrid
                />
              )}

              {/* Model */}
              <Model src={src} onLoaded={onLoaded} onError={handleError} />
            </>
          )}
        </Suspense>
      </Canvas>

      {/* Info overlay */}
      <div className="absolute bottom-2 left-2 text-xs text-muted-foreground pointer-events-none">
        Left-click + drag to rotate • Scroll to zoom • Right-click + drag to pan
      </div>
    </div>
  );
}

/**
 * Lightweight version for asset cards (no grid, minimal controls)
 */
export function ThreeDPreviewMini({ src, className }: { src: string; className?: string }) {
  return (
    <div className={cn("relative w-full h-full bg-muted rounded-lg overflow-hidden", className)}>
      <Canvas dpr={[1, 2]} gl={{ antialias: true }}>
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          <Environment preset="sunset" />
          <PerspectiveCamera makeDefault position={[0, 2, 5]} fov={50} />
          <OrbitControls enablePan={false} enableZoom={false} enableRotate={false} />
          <Model src={src} />
        </Suspense>
      </Canvas>
    </div>
  );
}
