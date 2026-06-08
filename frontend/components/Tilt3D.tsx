"use client";

import {
  motion,
  useMotionTemplate,
  useMotionValue,
  useSpring,
  useTransform,
} from "framer-motion";
import type { PointerEvent, ReactNode } from "react";

/**
 * Reusable cursor-tracking 3D tilt. Wraps any content in a perspective container and
 * rotates it toward the pointer (spring-eased), with an optional glare highlight. Children
 * can use `translateZ(...)` to float at different depths. Used by stat + tool cards.
 */
export function Tilt3D({
  children,
  className,
  max = 9,
  glare = true,
}: {
  children: ReactNode;
  className?: string;
  max?: number;
  glare?: boolean;
}) {
  const px = useMotionValue(0);
  const py = useMotionValue(0);
  const rotateX = useSpring(useTransform(py, [-0.5, 0.5], [max, -max]), {
    stiffness: 220,
    damping: 18,
  });
  const rotateY = useSpring(useTransform(px, [-0.5, 0.5], [-max, max]), {
    stiffness: 220,
    damping: 18,
  });
  const gx = useTransform(px, [-0.5, 0.5], ["0%", "100%"]);
  const gy = useTransform(py, [-0.5, 0.5], ["0%", "100%"]);
  const glareBg = useMotionTemplate`radial-gradient(220px circle at ${gx} ${gy}, rgba(34,211,238,0.16), transparent 70%)`;

  function onMove(e: PointerEvent<HTMLDivElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    px.set((e.clientX - r.left) / r.width - 0.5);
    py.set((e.clientY - r.top) / r.height - 0.5);
  }
  function onLeave() {
    px.set(0);
    py.set(0);
  }

  return (
    <div style={{ perspective: 1000 }} className={className}>
      <motion.div
        onPointerMove={onMove}
        onPointerLeave={onLeave}
        style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
        className="group relative h-full"
      >
        {glare && (
          <motion.div
            style={{ background: glareBg }}
            className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          />
        )}
        {children}
      </motion.div>
    </div>
  );
}
