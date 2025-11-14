"use client";

import { useState } from "react";
import { BattleCharacters } from "@/components/battle/BattleCharacters";
import { Button } from "@/components/ui/button";
import { Swords } from "lucide-react";
import { ContactIcons } from "@/components/ui/ContactIcons";

type VerdictState = "fighting" | "idle" | "left_better" | "right_better" | "both_good" | "both_bad";

export default function AnimationDemoPage() {
  const [currentState, setCurrentState] = useState<VerdictState>("idle");
  const [isRevealed, setIsRevealed] = useState(false);

  const states: { state: VerdictState; label: string; description: string }[] = [
    {
      state: "fighting",
      label: "Fighting",
      description: "Robots are battling (during parsing)",
    },
    {
      state: "idle",
      label: "Idle",
      description: "Waiting for user feedback",
    },
    {
      state: "left_better",
      label: "Left is better",
      description: "Left wins (celebrates), Right loses (defeated)",
    },
    {
      state: "right_better",
      label: "Right is better",
      description: "Right wins (celebrates), Left loses (defeated)",
    },
    {
      state: "both_good",
      label: "Both are good",
      description: "Both robots celebrate together",
    },
    {
      state: "both_bad",
      label: "Both are bad",
      description: "Both robots defeated/sad",
    },
  ];

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Swords className="h-8 w-8 text-purple-500" />
          <h1 className="text-3xl font-bold">Robot Animation Demo</h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Test all the battle robot animations and states
        </p>
      </div>

      {/* Animation Preview */}
      <div className="mb-8 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-8 overflow-visible">
        <BattleCharacters
          isParsing={currentState === "fighting"}
          isRevealed={isRevealed}
          feedbackChoice={
            currentState === "left_better" ? "A" :
            currentState === "right_better" ? "B" :
            currentState === "both_good" ? "BOTH_GOOD" :
            currentState === "both_bad" ? "BOTH_BAD" :
            null
          }
          assignments={[
            { label: "A", provider: "llamaindex" },
            { label: "B", provider: "reducto" },
          ]}
          preferredLabels={
            currentState === "left_better" ? ["A"] :
            currentState === "right_better" ? ["B"] :
            currentState === "both_good" ? ["A", "B"] :
            currentState === "both_bad" ? [] :
            null
          }
        />

        {/* Current State Info */}
        <div className="mt-8 text-center">
          <div className="inline-block rounded-lg bg-purple-100 dark:bg-purple-900/30 px-4 py-2">
            <span className="text-sm font-semibold text-purple-700 dark:text-purple-300">
              Current State: {currentState.toUpperCase()}
            </span>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            {states.find((s) => s.state === currentState)?.description}
          </p>
        </div>
      </div>

      {/* State Controls */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Animation States</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {states.map(({ state, label, description }) => (
            <Button
              key={state}
              onClick={() => setCurrentState(state)}
              variant={currentState === state ? "default" : "outline"}
              className="h-auto flex-col items-start p-4"
            >
              <span className="font-semibold">{label}</span>
              <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {description}
              </span>
            </Button>
          ))}
        </div>
      </div>

      {/* Reveal Toggle */}
      <div className="mb-6">
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-6">
          <h2 className="text-xl font-semibold mb-4">Provider Reveal</h2>
          <div className="flex items-center gap-4">
            <Button
              onClick={() => setIsRevealed(!isRevealed)}
              variant={isRevealed ? "default" : "outline"}
            >
              {isRevealed ? "Hide Providers" : "Show Providers"}
            </Button>
            <p className="text-sm text-gray-500">
              {isRevealed
                ? "Robot heads show provider logos"
                : "Robot heads show default faces"}
            </p>
          </div>
        </div>
      </div>

      {/* Testing Scenarios */}
      <div className="mt-8 rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/30 p-6">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-3">
          Testing Scenarios
        </h3>
        <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
          <li>
            <strong>1. Battle Start:</strong> Click "Fighting" to see robots
            battle
          </li>
          <li>
            <strong>2. Results Ready:</strong> Click "Idle" to see waiting state
          </li>
          <li>
            <strong>3. Winner:</strong> Click "Celebrating" (one robot wins)
          </li>
          <li>
            <strong>4. Loser:</strong> Click "Defeated" (one robot loses)
          </li>
          <li>
            <strong>5. Tie:</strong> Click "Handshake" (both good/bad)
          </li>
          <li>
            <strong>6. Reveal:</strong> Toggle "Show Providers" to see logo swap
          </li>
        </ul>
      </div>

      {/* Navigation */}
      <div className="mt-8 text-center">
        <a
          href="/battle"
          className="text-purple-600 dark:text-purple-400 hover:underline"
        >
          ← Back to Battle Page
        </a>
      </div>

      <ContactIcons />
    </div>
  );
}
