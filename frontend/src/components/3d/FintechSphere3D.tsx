import React, { useEffect, useRef } from "react";

interface FintechSphere3DProps {
  className?: string;
  accentColor?: string; // emerald, cyan, indigo
  interactive?: boolean;
}

export const FintechSphere3D: React.FC<FintechSphere3DProps> = ({
  className = "w-full h-full",
  accentColor = "emerald",
  interactive = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = (canvas.width = canvas.parentElement?.clientWidth || 400);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 400);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };
    window.addEventListener("resize", handleResize);

    // 3D Nodes generation on a sphere
    const nodeCount = 42;
    const radius = Math.min(width, height) * 0.32;
    interface Node3D {
      x: number;
      y: number;
      z: number;
      origX: number;
      origY: number;
      origZ: number;
      size: number;
      color: string;
      pulse: number;
      label?: string;
    }

    const nodes: Node3D[] = [];
    const phi = Math.PI * (3 - Math.sqrt(5)); // Golden angle

    const colors =
      accentColor === "cyan"
        ? ["#06b6d4", "#38bdf8", "#0284c7", "#67e8f9"]
        : accentColor === "indigo"
        ? ["#6366f1", "#818cf8", "#4f46e5", "#c7d2fe"]
        : ["#10b981", "#34d399", "#059669", "#6ee7b7"];

    const labels = ["MRR", "ARR", "ACTIVE", "BILLING", "AUTH", "SECURE", "QUOTA", "INVOICE"];

    for (let i = 0; i < nodeCount; i++) {
      const y = 1 - (i / (nodeCount - 1)) * 2;
      const radiusAtY = Math.sqrt(1 - y * y);
      const theta = phi * i;

      const x = Math.cos(theta) * radiusAtY;
      const z = Math.sin(theta) * radiusAtY;

      nodes.push({
        x: x * radius,
        y: y * radius,
        z: z * radius,
        origX: x * radius,
        origY: y * radius,
        origZ: z * radius,
        size: Math.random() * 2.5 + 2,
        color: colors[i % colors.length],
        pulse: Math.random() * Math.PI * 2,
        label: i < labels.length ? labels[i] : undefined,
      });
    }

    // Rings on the sphere
    const ringSegments = 36;
    const ring1: { x: number; y: number; z: number }[] = [];
    const ring2: { x: number; y: number; z: number }[] = [];
    for (let i = 0; i <= ringSegments; i++) {
      const theta = (i / ringSegments) * Math.PI * 2;
      // Equatorial ring
      ring1.push({
        x: Math.cos(theta) * radius * 1.05,
        y: Math.sin(theta) * radius * 1.05 * 0.25,
        z: Math.sin(theta) * radius * 1.05 * 0.95,
      });
      // Polar tilted ring
      ring2.push({
        x: Math.cos(theta) * radius * 1.15 * 0.7,
        y: Math.sin(theta) * radius * 1.15,
        z: Math.cos(theta) * radius * 1.15 * 0.7,
      });
    }

    // Dynamic rotation angles
    let angleX = 0.2;
    let angleY = 0.0;
    let targetAngleX = 0.2;
    let targetAngleY = 0.0;
    let mouseX = 0;
    let mouseY = 0;

    const onMouseMove = (e: MouseEvent) => {
      if (!interactive || !canvas) return;
      const rect = canvas.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      mouseX = (e.clientX - cx) / (rect.width / 2);
      mouseY = (e.clientY - cy) / (rect.height / 2);

      targetAngleY = mouseX * 0.8;
      targetAngleX = -mouseY * 0.6;
    };

    window.addEventListener("mousemove", onMouseMove);

    let lastTime = performance.now();

    const render = (now: number) => {
      const dt = (now - lastTime) / 1000;
      lastTime = now;

      ctx.clearRect(0, 0, width, height);

      // Smooth camera interpolation
      angleX += (targetAngleX - angleX) * 0.05;
      angleY += (targetAngleY - angleY) * 0.05 + 0.005; // continuous idle spin

      const cosX = Math.cos(angleX);
      const sinX = Math.sin(angleX);
      const cosY = Math.cos(angleY);
      const sinY = Math.sin(angleY);

      const cx = width / 2;
      const cy = height / 2;
      const fov = 400;

      // Project function
      const project = (x: number, y: number, z: number) => {
        // Rotate around Y
        const x1 = x * cosY - z * sinY;
        const z1 = z * cosY + x * sinY;

        // Rotate around X
        const y2 = y * cosX - z1 * sinX;
        const z2 = z1 * cosX + y * sinX;

        const distance = fov + z2;
        const scale = distance > 0 ? fov / distance : 0;
        return {
          px: cx + x1 * scale,
          py: cy + y2 * scale,
          scale,
          z: z2,
        };
      };

      // Draw background ambient glow
      const glowGrad = ctx.createRadialGradient(cx, cy, 20, cx, cy, radius * 1.3);
      glowGrad.addColorStop(0, accentColor === "cyan" ? "rgba(6, 182, 212, 0.12)" : "rgba(16, 185, 129, 0.12)");
      glowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = glowGrad;
      ctx.fillRect(0, 0, width, height);

      // Draw Rings
      const drawRing = (ringPoints: typeof ring1, strokeColor: string) => {
        ctx.beginPath();
        for (let i = 0; i < ringPoints.length; i++) {
          const pt = project(ringPoints[i].x, ringPoints[i].y, ringPoints[i].z);
          if (i === 0) ctx.moveTo(pt.px, pt.py);
          else ctx.lineTo(pt.px, pt.py);
        }
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 1;
        ctx.stroke();
      };

      drawRing(ring1, "rgba(52, 211, 153, 0.2)");
      drawRing(ring2, "rgba(56, 189, 248, 0.15)");

      // Project & sort nodes by Z (back to front)
      interface ProjectedNode {
        px: number;
        py: number;
        scale: number;
        z: number;
        size: number;
        color: string;
        label?: string;
      }

      const projected: ProjectedNode[] = nodes.map((node) => {
        node.pulse += dt * 2.5;
        const p = project(node.x, node.y, node.z);
        return {
          ...p,
          size: node.size * (1 + Math.sin(node.pulse) * 0.2),
          color: node.color,
          label: node.label,
        };
      });

      projected.sort((a, b) => a.z - b.z);

      // Draw connection lines between nearby nodes
      ctx.lineWidth = 0.75;
      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const dx = projected[i].px - projected[j].px;
          const dy = projected[i].py - projected[j].py;
          const dist = Math.sqrt(dx * dx + dy * dy);

          // Connect if close in 2D and similar in 3D depth
          if (dist < 65 && Math.abs(projected[i].z - projected[j].z) < 120) {
            const alpha = Math.max(0, (1 - dist / 65) * 0.3);
            ctx.strokeStyle = `rgba(52, 211, 153, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(projected[i].px, projected[i].py);
            ctx.lineTo(projected[j].px, projected[j].py);
            ctx.stroke();
          }
        }
      }

      // Draw nodes
      for (const p of projected) {
        if (p.scale <= 0) continue;

        const alpha = Math.min(1, Math.max(0.15, (p.z + radius) / (radius * 2)));

        ctx.beginPath();
        ctx.arc(p.px, p.py, Math.max(1, p.size * p.scale), 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = alpha;
        ctx.fill();

        // Glow halo for prominent front nodes
        if (p.z > 20) {
          ctx.beginPath();
          ctx.arc(p.px, p.py, p.size * p.scale * 2.2, 0, Math.PI * 2);
          ctx.fillStyle = p.color;
          ctx.globalAlpha = alpha * 0.25;
          ctx.fill();
        }

        // Draw micro labels on select front nodes
        if (p.label && p.z > 30) {
          ctx.globalAlpha = alpha * 0.9;
          ctx.font = "9px 'JetBrains Mono', monospace";
          ctx.fillStyle = "#ffffff";
          ctx.fillText(p.label, p.px + 7, p.py + 3);
        }

        ctx.globalAlpha = 1.0;
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", onMouseMove);
    };
  }, [accentColor, interactive]);

  return (
    <div className={`relative overflow-hidden pointer-events-auto ${className}`}>
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
};
