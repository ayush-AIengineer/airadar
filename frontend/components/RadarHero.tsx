"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * A live WebGL "radar" scene rendered with vanilla three.js (no react-three-fiber, to keep
 * peer deps clean on React 19). A wireframe core spins inside a particle field, ringed by a
 * flat radar grid with a sweeping wedge. The camera parallaxes toward the pointer.
 */
export function RadarHero() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const width = mount.clientWidth;
    const height = mount.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 1.6, 6);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const root = new THREE.Group();
    scene.add(root);

    // ── Wireframe core ──────────────────────────────────────────────
    const core = new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.35, 1),
      new THREE.MeshBasicMaterial({
        color: 0x3b82f6,
        wireframe: true,
        transparent: true,
        opacity: 0.6,
      })
    );
    const innerCore = new THREE.Mesh(
      new THREE.IcosahedronGeometry(0.85, 0),
      new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.35 })
    );
    root.add(core, innerCore);

    // ── Particle field (tools scattered in space) ───────────────────
    const COUNT = 900;
    const positions = new Float32Array(COUNT * 3);
    for (let i = 0; i < COUNT; i++) {
      const r = 2.6 + Math.random() * 2.4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.cos(phi) * 0.6;
      positions[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
    }
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const particles = new THREE.Points(
      pGeo,
      new THREE.PointsMaterial({
        color: 0xcfe0ff,
        size: 0.035,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
    );
    scene.add(particles);

    // ── Flat radar rings ────────────────────────────────────────────
    const ringGroup = new THREE.Group();
    ringGroup.rotation.x = -Math.PI / 2;
    [1.6, 2.4, 3.2].forEach((radius) => {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(radius - 0.006, radius, 96),
        new THREE.MeshBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.2, side: THREE.DoubleSide })
      );
      ringGroup.add(ring);
    });
    // sweeping wedge
    const sweep = new THREE.Mesh(
      new THREE.CircleGeometry(3.2, 48, 0, Math.PI / 5),
      new THREE.MeshBasicMaterial({
        color: 0x60a5fa,
        transparent: true,
        opacity: 0.18,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
    );
    ringGroup.add(sweep);
    scene.add(ringGroup);

    // ── Interaction + animation ─────────────────────────────────────
    const target = { x: 0, y: 0 };
    const onPointer = (e: PointerEvent) => {
      target.x = (e.clientX / window.innerWidth - 0.5) * 2;
      target.y = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener("pointermove", onPointer);

    const clock = new THREE.Clock();
    let raf = 0;
    const render = () => {
      const t = clock.getElapsedTime();
      core.rotation.y = t * 0.25;
      core.rotation.x = t * 0.12;
      innerCore.rotation.y = -t * 0.4;
      particles.rotation.y = t * 0.04;
      sweep.rotation.z = -t * 0.9;

      // parallax: ease camera toward pointer
      camera.position.x += (target.x * 1.2 - camera.position.x) * 0.04;
      camera.position.y += (1.6 - target.y * 0.8 - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
      if (!reduce) raf = requestAnimationFrame(render);
    };
    render();

    // ── Resize ──────────────────────────────────────────────────────
    const onResize = () => {
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onPointer);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      pGeo.dispose();
      core.geometry.dispose();
      innerCore.geometry.dispose();
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={mountRef} className="absolute inset-0" aria-hidden />;
}
