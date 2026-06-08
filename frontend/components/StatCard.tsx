"use client";

import { animate, motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { Tilt3D } from "@/components/Tilt3D";

interface StatCardProps {
  label: string;
  value: number;
  suffix?: string;
  delay?: number;
}

export function StatCard({ label, value, suffix = "", delay = 0 }: StatCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const controls = animate(0, value, {
      duration: 1.2,
      delay,
      ease: "easeOut",
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
    return () => controls.stop();
  }, [inView, value, delay]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay }}
    >
      <Tilt3D max={10} className="h-full">
        <div className="glass glass-hover h-full rounded-2xl p-5">
          <div
            className="font-mono text-3xl font-bold tracking-tight text-gradient"
            style={{ transform: "translateZ(34px)" }}
          >
            {display.toLocaleString()}
            {suffix}
          </div>
          <div className="mt-1 text-sm text-slate-400" style={{ transform: "translateZ(20px)" }}>
            {label}
          </div>
        </div>
      </Tilt3D>
    </motion.div>
  );
}
