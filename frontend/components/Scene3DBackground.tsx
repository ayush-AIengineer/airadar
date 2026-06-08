"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * A single persistent WebGL canvas behind the entire page, giving every section real depth.
 * A large parallax particle field drifts with time, leans toward the pointer, and travels as
 * you scroll — so the whole site reads as one 3D space, not a flat document. One renderer,
 * pointer-events none, DPR-capped, reduced-motion aware, fully disposed on unmount.
 */
export function Scene3DBackground() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x05060a, 0.05);
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 0, 12);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    mount.appendChild(renderer.domElement);

    // ── Layered particle field ──────────────────────────────────────
    const makeLayer = (count: number, spread: number, size: number, color: number, opacity: number) => {
      const pos = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        pos[i * 3] = (Math.random() - 0.5) * spread;
        pos[i * 3 + 1] = (Math.random() - 0.5) * spread;
        pos[i * 3 + 2] = (Math.random() - 0.5) * spread * 0.6;
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      const points = new THREE.Points(
        geo,
        new THREE.PointsMaterial({
          color,
          size,
          transparent: true,
          opacity,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
          sizeAttenuation: true,
        })
      );
      scene.add(points);
      return { points, geo };
    };

    // Lighter particle load on phones (smaller GPUs, battery).
    const f = window.innerWidth < 768 ? 0.4 : 1;
    const layers = [
      makeLayer(Math.round(700 * f), 36, 0.05, 0x2563eb, 0.5), // far deep blue
      makeLayer(Math.round(500 * f), 28, 0.06, 0x3b82f6, 0.6), // mid blue
      makeLayer(Math.round(220 * f), 20, 0.09, 0xffffff, 0.55), // near white
    ];

    // faint slow wireframe torus for parallax depth
    const torus = new THREE.Mesh(
      new THREE.TorusGeometry(7, 0.04, 8, 120),
      new THREE.MeshBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.08 })
    );
    torus.rotation.x = Math.PI / 3;
    scene.add(torus);

    // ── Interaction state ───────────────────────────────────────────
    const pointer = { x: 0, y: 0 };
    let scrollN = 0;
    const onPointer = (e: PointerEvent) => {
      pointer.x = (e.clientX / window.innerWidth - 0.5) * 2;
      pointer.y = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    const onScroll = () => {
      const max = document.body.scrollHeight - window.innerHeight;
      scrollN = max > 0 ? window.scrollY / max : 0;
    };
    window.addEventListener("pointermove", onPointer, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    const clock = new THREE.Clock();
    let raf = 0;
    const render = () => {
      const t = clock.getElapsedTime();
      layers.forEach((l, i) => {
        l.points.rotation.y = t * (0.02 + i * 0.012) + scrollN * 0.6;
        l.points.rotation.x = scrollN * (0.3 + i * 0.1);
      });
      torus.rotation.z = t * 0.05;

      // camera parallax to pointer + travel with scroll
      camera.position.x += (pointer.x * 1.6 - camera.position.x) * 0.03;
      camera.position.y += (-pointer.y * 1.2 - scrollN * 3 - camera.position.y) * 0.03;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
      if (!reduce) raf = requestAnimationFrame(render);
    };
    render();

    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onPointer);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      layers.forEach((l) => {
        l.geo.dispose();
        (l.points.material as THREE.Material).dispose();
      });
      torus.geometry.dispose();
      (torus.material as THREE.Material).dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={mountRef} className="pointer-events-none fixed inset-0 -z-10" aria-hidden />;
}
