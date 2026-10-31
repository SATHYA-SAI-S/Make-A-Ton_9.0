import React, { useState, Suspense, lazy } from "react";
import { FintechSphere3D } from "./FintechSphere3D";
import { Sparkles, Loader2 } from "lucide-react";

// Lazy load Spline to ensure client-only mounting and avoid SSR WebGL crashes
const SplineComponent = lazy(() => import("@splinetool/react-spline"));

interface SplineSceneProps {
  sceneUrl?: string;
  className?: string;
  accentColor?: "emerald" | "cyan" | "indigo";
}

export const SplineScene: React.FC<SplineSceneProps> = ({
  sceneUrl = "https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode", // interactive futuristic glass torus
  className = "w-full h-full min-h-[380px]",
  accentColor = "emerald",
}) => {
  const [hasError, setHasError] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  // If remote spline fails or has WebGL error, seamlessly fall back to FintechSphere3D
  if (hasError) {
    return (
      <div className={`relative ${className}`}>
        <FintechSphere3D className="w-full h-full" accentColor={accentColor} />
      </div>
    );
  }

  return (
    <div className={`relative w-full h-full overflow-hidden ${className}`}>
      {/* Loading Skeleton */}
      {!isLoaded && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/60 backdrop-blur-sm z-10">
          <div className="relative flex items-center justify-center">
            <div className="w-16 h-16 rounded-full border-2 border-emerald-500/20 border-t-emerald-500 animate-spin" />
            <Sparkles className="absolute text-emerald-400 animate-pulse" size={20} />
          </div>
          <p className="mt-3 text-xs font-mono text-emerald-400/80 flex items-center gap-1.5">
            <Loader2 size={12} className="animate-spin" />
            Initializing 3D Visualizer...
          </p>
        </div>
      )}

      {/* Interactive Spline Scene */}
      <Suspense fallback={<FintechSphere3D className="w-full h-full" accentColor={accentColor} />}>
        <div className="w-full h-full transition-opacity duration-700 ease-in-out" style={{ opacity: isLoaded ? 1 : 0 }}>
          <SplineComponent
            scene={sceneUrl}
            onLoad={() => setIsLoaded(true)}
            onError={() => {
              setHasError(true);
            }}
          />
        </div>
      </Suspense>
    </div>
  );
};
