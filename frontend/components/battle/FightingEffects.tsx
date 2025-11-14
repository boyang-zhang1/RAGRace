"use client";

import { motion } from "framer-motion";

export function FightingEffects() {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none" style={{ zIndex: 100 }}>
      {/* MASSIVE Lightning bolt */}
      <motion.div
        className="absolute"
        style={{ zIndex: 50 }}
        animate={{
          opacity: [1, 0.7, 1],
        }}
        transition={{
          repeat: Infinity,
          duration: 0.5,
        }}
      >
        <div className="text-9xl">⚡</div>
      </motion.div>

      {/* Impact sparks - SIMPLE AND VISIBLE */}
      {[...Array(6)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute text-4xl"
          style={{
            zIndex: 40,
          }}
          animate={{
            x: [0, Math.cos((i * Math.PI) / 3) * 60],
            y: [0, Math.sin((i * Math.PI) / 3) * 60],
            opacity: [1, 0],
            scale: [1, 0.3],
          }}
          transition={{
            repeat: Infinity,
            duration: 1,
            delay: i * 0.1,
            ease: "easeOut",
          }}
        >
          ✨
        </motion.div>
      ))}


      {/* Fire emojis */}
      {[...Array(8)].map((_, i) => (
        <motion.div
          key={`fire-${i}`}
          className="absolute text-5xl"
          style={{
            zIndex: 30,
          }}
          animate={{
            x: [0, (i % 2 === 0 ? 1 : -1) * 50],
            y: [0, -80],
            opacity: [1, 0],
            scale: [1, 0.3],
          }}
          transition={{
            repeat: Infinity,
            duration: 1.2,
            delay: i * 0.15,
            ease: "easeOut",
          }}
        >
          🔥
        </motion.div>
      ))}
    </div>
  );
}
