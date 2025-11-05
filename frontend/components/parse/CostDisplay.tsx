"use client";

import { DollarSign } from "lucide-react";

interface CostData {
  provider: string;
  credits: number;
  usd_per_credit: number;
  total_usd: number;
  details: Record<string, any>;
}

interface CostDisplayProps {
  cost: CostData;
  providerName: string;
}

export function CostDisplay({ cost, providerName }: CostDisplayProps) {
  // Use credits_per_page from details if available (calculated by backend)
  // Otherwise calculate it from total credits / num_pages
  const creditsPerPage = cost.details.credits_per_page !== undefined
    ? cost.details.credits_per_page.toFixed(1)
    : (cost.details.num_pages > 0
        ? (cost.credits / cost.details.num_pages).toFixed(1)
        : null);

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-3">
        <DollarSign className="h-4 w-4 text-gray-500 dark:text-gray-400" />
        <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">Cost</span>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Total credits:</span>
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {cost.credits.toFixed(2)}
          </span>
        </div>
        {creditsPerPage && (
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-600 dark:text-gray-400">Per page:</span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {creditsPerPage} credits
            </span>
          </div>
        )}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Rate:</span>
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
            ${cost.usd_per_credit.toFixed(4)}/credit
          </span>
        </div>
        <div className="pt-2 mt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">Total:</span>
            <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
              ${cost.total_usd.toFixed(4)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
