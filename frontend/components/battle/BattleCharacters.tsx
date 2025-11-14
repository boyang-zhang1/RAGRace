"use client";

import { motion } from "framer-motion";
import { Robot } from "./Robot";
import { FightingEffects } from "./FightingEffects";
import { Swords } from "lucide-react";
import type { BattleMetadata } from "@/types/api";

type RobotState = "fighting" | "idle" | "celebrating" | "defeated";

interface BattleCharactersProps {
  isParsing: boolean;
  isRevealed: boolean;
  feedbackChoice: string | null;
  assignments: BattleMetadata["assignments"];
  preferredLabels: string[] | null;
}

export function BattleCharacters({
  isParsing,
  isRevealed,
  feedbackChoice,
  assignments,
  preferredLabels,
}: BattleCharactersProps) {
  // Create placeholder assignments if none provided (during initial parsing)
  const hasAssignments = assignments.length > 0;
  const leftAssignment = hasAssignments
    ? assignments[0]
    : { label: "A", provider: "" };
  const rightAssignment = hasAssignments
    ? assignments[1] || assignments[0]
    : { label: "B", provider: "" };

  // Determine the state for each robot
  const getLeftRobotState = (): RobotState => {
    if (isParsing) return "fighting";

    // If feedbackChoice is set (but not submitted yet), show verdict animation
    if (preferredLabels === null && feedbackChoice) {
      // User picked a verdict, show animation immediately
      if (feedbackChoice === "BOTH_GOOD") return "celebrating";
      if (feedbackChoice === "BOTH_BAD") return "defeated";
      // Left is better
      if (feedbackChoice === leftAssignment.label) return "celebrating";
      // Right is better (left lost)
      return "defeated";
    }

    // If preferredLabels is set, show animation (AFTER submission and reveal)
    if (preferredLabels !== null) {
      const isLeftPreferred = preferredLabels.includes(leftAssignment.label);

      // Both good = both celebrate
      if (preferredLabels.length === 2) {
        return "celebrating";
      }

      // Both bad = both defeated
      if (preferredLabels.length === 0) {
        return "defeated";
      }

      // Left won
      if (isLeftPreferred) return "celebrating";

      // Left lost
      return "defeated";
    }

    // Default: idle (waiting for user feedback)
    return "idle";
  };

  const getRightRobotState = (): RobotState => {
    if (isParsing) return "fighting";

    // If feedbackChoice is set (but not submitted yet), show verdict animation
    if (preferredLabels === null && feedbackChoice) {
      // User picked a verdict, show animation immediately
      if (feedbackChoice === "BOTH_GOOD") return "celebrating";
      if (feedbackChoice === "BOTH_BAD") return "defeated";
      // Right is better
      if (feedbackChoice === rightAssignment.label) return "celebrating";
      // Left is better (right lost)
      return "defeated";
    }

    // If preferredLabels is set, show animation (AFTER submission and reveal)
    if (preferredLabels !== null) {
      const isRightPreferred = preferredLabels.includes(rightAssignment.label);

      // Both good = both celebrate
      if (preferredLabels.length === 2) {
        return "celebrating";
      }

      // Both bad = both defeated
      if (preferredLabels.length === 0) {
        return "defeated";
      }

      // Right won
      if (isRightPreferred) return "celebrating";

      // Right lost
      return "defeated";
    }

    // Default: idle (waiting for user feedback)
    return "idle";
  };

  const leftState = getLeftRobotState();
  const rightState = getRightRobotState();

  // Show VS badge during fighting
  const showVsBadge = isParsing;

  return (
    <motion.div
      className="flex items-center justify-center py-1 mb-2 overflow-visible"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="relative flex flex-col sm:flex-row items-center gap-4 sm:gap-6 md:gap-8 overflow-visible">
        {/* Left Robot */}
        <Robot
          position="left"
          state={leftState}
          isRevealed={isRevealed}
          provider={isRevealed ? leftAssignment.provider : undefined}
          color="#3b82f6" // Blue
        />

        {/* VS Badge / Fighting Effects */}
        <div className="relative flex items-center justify-center min-w-[160px] min-h-[160px] overflow-visible">
          {showVsBadge && (
            <>
              {/* Fighting effects (lightning, fire, boom) */}
              <FightingEffects />

              {/* VS Badge */}
              <motion.div
                className="flex flex-col items-center gap-2 relative z-10"
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: "spring", stiffness: 200, damping: 15 }}
              >
                <Swords className="h-8 w-8 text-purple-500 dark:text-purple-400" />
                <motion.span
                  className="text-2xl font-bold text-purple-600 dark:text-purple-400"
                  animate={{
                    scale: [1, 1.1, 1],
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 1.5,
                    ease: "easeInOut",
                  }}
                >
                  VS
                </motion.span>
              </motion.div>
            </>
          )}
        </div>

        {/* Right Robot */}
        <Robot
          position="right"
          state={rightState}
          isRevealed={isRevealed}
          provider={isRevealed ? rightAssignment.provider : undefined}
          color="#f97316" // Orange
        />
      </div>

      {/* Status text below robots */}
      {isParsing && (
        <motion.div
          className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 text-sm font-medium text-purple-600 dark:text-purple-400"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          Battle in progress...
        </motion.div>
      )}
    </motion.div>
  );
}
