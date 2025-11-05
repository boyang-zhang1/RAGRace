"use client";

import { Clock } from "lucide-react";

interface ProcessingTimeDisplayProps {
  processingTime: number;
  providerName: string;
}

export function ProcessingTimeDisplay({ processingTime, providerName }: ProcessingTimeDisplayProps) {
  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-3">
        <Clock className="h-4 w-4 text-gray-500 dark:text-gray-400" />
        <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">Processing Time</span>
      </div>
      <div className="flex justify-center items-baseline">
        <span className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          {processingTime.toFixed(2)}
        </span>
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400 ml-1">seconds</span>
      </div>
    </div>
  );
}
