"use client";

import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { ProviderLabel } from "@/components/providers/ProviderLabel";

type RobotState = "fighting" | "idle" | "celebrating" | "defeated";

interface RobotProps {
  position: "left" | "right";
  state: RobotState;
  isRevealed?: boolean;
  provider?: string;
  color?: string;
}

export function Robot({
  position,
  state,
  isRevealed = false,
  provider,
  color = position === "left" ? "#3b82f6" : "#f97316", // blue or orange
}: RobotProps) {
  const shouldReduceMotion = useReducedMotion();

  // Animation variants for the entire robot
  const robotVariants = {
    fighting: {
      // Slight forward/backward motion during fight
      x: shouldReduceMotion
        ? 0
        : position === "left"
        ? [0, 5, 0, 5, 0]
        : [0, -5, 0, -5, 0],
      y: shouldReduceMotion ? 0 : [0, -3, 0, -3, 0],
      transition: shouldReduceMotion
        ? { duration: 0 }
        : {
            repeat: Infinity,
            duration: 0.8,
            ease: "easeInOut" as const,
          },
    },
    idle: {
      y: shouldReduceMotion ? 0 : [0, -5, 0],
      transition: shouldReduceMotion
        ? { duration: 0 }
        : {
            repeat: Infinity,
            duration: 2,
            ease: "easeInOut" as const,
          },
    },
    celebrating: {
      y: shouldReduceMotion ? 0 : [-30, 0, -20, 0],
      rotate: shouldReduceMotion ? 0 : [0, -10, 10, -5, 5, 0],
      transition: {
        duration: shouldReduceMotion ? 0 : 1.2,
        ease: "easeOut" as const,
        // repeat: Infinity, // LOOP celebrating animation
      },
    },
    defeated: {
      rotate: position === "left" ? -90 : 90,
      y: 30,
      opacity: 0.5,
      transition: {
        duration: shouldReduceMotion ? 0 : 0.8,
        ease: "easeIn" as const,
      },
    },
  };

  // Arm animation variants - LEFT ARM PUNCHES
  const leftArmVariants = {
    fighting: {
      // Extend arm forward for punch
      rotate: shouldReduceMotion
        ? position === "left"
          ? -20
          : 20
        : position === "left"
        ? [-20, -90, -20] // Left robot: arm extends forward (punching)
        : [20, 80, 20], // Right robot: arm extends forward
      x: shouldReduceMotion
        ? 0
        : position === "left"
        ? [0, 15, 0] // Punch extends outward
        : [0, -15, 0],
      transition: shouldReduceMotion
        ? { duration: 0 }
        : {
            repeat: Infinity,
            duration: 0.8,
            ease: "easeInOut" as const,
            times: [0, 0.5, 1], // Sync with right arm (opposite)
          },
    },
    idle: {
      rotate: position === "left" ? -20 : 20,
      x: 0,
    },
    celebrating: {
      rotate: position === "left" ? -80 : 80,
      y: -5,
      x: 0,
    },
    defeated: {
      rotate: position === "left" ? -10 : 10,
      x: 0,
    },
  };

  // RIGHT ARM PUNCHES (alternates with left arm)
  const rightArmVariants = {
    fighting: {
      // Extend arm forward for punch (opposite of left arm)
      rotate: shouldReduceMotion
        ? position === "left"
          ? 20
          : -20
        : position === "left"
        ? [20, 90, 20] // Left robot: right arm punches
        : [-20, -80, -20], // Right robot: left arm punches
      x: shouldReduceMotion
        ? 0
        : position === "left"
        ? [0, 15, 0] // Punch extends outward
        : [0, -15, 0],
      transition: shouldReduceMotion
        ? { duration: 0 }
        : {
            repeat: Infinity,
            duration: 0.8,
            ease: "easeInOut" as const,
            times: [0, 0.5, 1],
            delay: 0.4, // Offset from left arm for alternating punches
          },
    },
    idle: {
      rotate: position === "left" ? 20 : -20,
      x: 0,
    },
    celebrating: {
      rotate: position === "left" ? 80 : -80,
      y: -5,
      x: 0,
    },
    defeated: {
      rotate: position === "left" ? 10 : -10,
      x: 0,
    },
  };


  return (
    <motion.div
      className="relative flex items-center justify-center"
      key={state} // Force re-render on state change
      initial={{ y: 0, rotate: 0, opacity: 1 }} // RESET position first
      variants={robotVariants}
      animate={state}
      style={{ width: 120, height: 140 }}
    >
      <svg
        width="120"
        height="140"
        viewBox="0 0 120 140"
        className="overflow-visible"
      >
        {/* Head - always show frame, swap face/logo inside */}
        <g className="robot-head">
          {/* Head rectangle frame - Medium-sized head */}
          <rect
            x="35"
            y="18"
            width="50"
            height="42"
            rx="9"
            fill="none"
            stroke={color}
            strokeWidth="1.5"
          />
          {/* Head background fill */}
          <rect
            x="36"
            y="19"
            width="48"
            height="40"
            rx="8"
            fill={color}
            opacity="0.9"
          />

          {/* Face or Logo content */}
          <AnimatePresence mode="wait">
            {!isRevealed ? (
              <motion.g
                key="robot-face"
                initial={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.5 }}
                transition={{ duration: 0.3 }}
              >
                {/* Eyes - adjusted for medium head */}
                <circle cx="50" cy="32" r="4.5" fill="white" />
                <circle cx="70" cy="32" r="4.5" fill="white" />
                {/* Eye pupils */}
                <circle cx="50" cy="32" r="2.2" fill="#1f2937" />
                <circle cx="70" cy="32" r="2.2" fill="#1f2937" />
                {/* Mouth line */}
                <line
                  x1="47"
                  y1="48"
                  x2="73"
                  y2="48"
                  stroke="white"
                  strokeWidth="2.3"
                  strokeLinecap="round"
                />
              </motion.g>
            ) : provider ? (
              <motion.g
                key="provider-logo"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: 0.2 }}
              >
                {/* Logo inside medium-sized head frame */}
                <foreignObject x="38" y="21" width="44" height="36">
                  <div className="flex items-center justify-center h-full bg-white/95 dark:bg-gray-900/95 rounded">
                    <ProviderLabel provider={provider} size={38} hideName={true} />
                  </div>
                </foreignObject>
              </motion.g>
            ) : null}
          </AnimatePresence>
        </g>

        {/* Body */}
        <rect
          x="45"
          y="63"
          width="30"
          height="40"
          rx="4"
          fill={color}
          opacity="0.9"
        />
        {/* Chest panel */}
        <rect
          x="52"
          y="71"
          width="16"
          height="12"
          rx="2"
          fill="white"
          opacity="0.3"
        />
        {/* Chest indicator lights */}
        <circle cx="56" cy="91" r="2" fill="#10b981" opacity="0.8" />
        <circle cx="64" cy="91" r="2" fill="#3b82f6" opacity="0.8" />

        {/* Left Arm - rotates from LEFT shoulder at (45, 70) */}
        <g transform="translate(45, 70)">
          <motion.g
            key={`left-${state}`} // Force reset on state change
            initial={{ rotate: 0 }} // RESET rotation first
            variants={leftArmVariants}
            animate={state}
            style={{ transformOrigin: "0 0" }}
          >
            {/* Arm extends down-left from shoulder (origin) */}
            <rect
              x="-12"
              y="0"
              width="12"
              height="24"
              rx="2"
              fill={color}
              opacity="0.85"
            />
          </motion.g>
        </g>

        {/* Right Arm - rotates from RIGHT shoulder at (75, 70) */}
        <g transform="translate(75, 70)">
          <motion.g
            key={`right-${state}`} // Force reset on state change
            initial={{ rotate: 0 }} // RESET rotation first
            variants={rightArmVariants}
            animate={state}
            style={{ transformOrigin: "0 0" }}
          >
            {/* Arm extends down-right from shoulder (origin) */}
            <rect
              x="0"
              y="0"
              width="12"
              height="24"
              rx="2"
              fill={color}
              opacity="0.85"
            />
          </motion.g>
        </g>

        {/* Legs */}
        <g>
          <rect
            x="48"
            y="105"
            width="10"
            height="22"
            rx="2"
            fill={color}
            opacity="0.85"
          />
          <rect
            x="62"
            y="105"
            width="10"
            height="22"
            rx="2"
            fill={color}
            opacity="0.85"
          />
          {/* Feet */}
          <rect
            x="46"
            y="127"
            width="14"
            height="6"
            rx="2"
            fill={color}
          />
          <rect
            x="60"
            y="127"
            width="14"
            height="6"
            rx="2"
            fill={color}
          />
        </g>
      </svg>

      {/* Glow effect for celebrating state */}
      {state === "celebrating" && (
        <motion.div
          className="absolute inset-0 rounded-full blur-xl"
          style={{ backgroundColor: color }}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: [0.15, 0.25, 0.15], scale: [1.2, 1.4, 1.2] }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        />
      )}

      {/* Confetti particles for celebrating - simple colored dots */}
      {state === "celebrating" && !shouldReduceMotion && (
        <>
          {[...Array(12)].map((_, i) => {
            const angle = (i * 30 * Math.PI) / 180; // 12 directions
            const distance = 50 + Math.random() * 30;
            const colors = ["#fbbf24", "#10b981", "#3b82f6", "#ec4899", "#8b5cf6"];
            const particleColor = colors[i % colors.length];
            return (
              <motion.div
                key={i}
                className="absolute rounded-full pointer-events-none"
                style={{
                  left: "50%",
                  top: "50%",
                  width: 8,
                  height: 8,
                  backgroundColor: particleColor,
                }}
                initial={{ opacity: 0, x: 0, y: 0, scale: 0 }}
                animate={{
                  opacity: [0, 1, 1, 0],
                  x: Math.cos(angle) * distance,
                  y: Math.sin(angle) * distance - 20, // Add upward drift
                  scale: [0, 1.5, 1, 0.5],
                }}
                transition={{
                  duration: 1.2,
                  delay: i * 0.03,
                  ease: "easeOut",
                  repeat: Infinity, // LOOP confetti forever
                  repeatDelay: 0.5,
                }}
              />
            );
          })}
        </>
      )}
    </motion.div>
  );
}
