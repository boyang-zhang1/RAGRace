"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PageNavigatorProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function PageNavigator({
  currentPage,
  totalPages,
  onPageChange,
}: PageNavigatorProps) {
  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  const handlePageInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const page = parseInt(e.target.value);
    if (!isNaN(page) && page >= 1 && page <= totalPages) {
      onPageChange(page);
    }
  };

  return (
    <div className="flex items-center justify-center gap-6 py-6">
      <Button
        variant="outline"
        size="lg"
        onClick={handlePrevious}
        disabled={currentPage === 1}
        className="px-6"
      >
        <ChevronLeft className="h-5 w-5 mr-2" />
        Previous
      </Button>

      <div className="flex items-center gap-3">
        <span className="text-base font-medium text-gray-600 dark:text-gray-400">Page</span>
        <input
          type="number"
          min={1}
          max={totalPages}
          value={currentPage}
          onChange={handlePageInput}
          className="w-20 text-center border rounded px-3 py-2 text-base font-medium"
        />
        <span className="text-base font-medium text-gray-600 dark:text-gray-400">
          of {totalPages}
        </span>
      </div>

      <Button
        variant="outline"
        size="lg"
        onClick={handleNext}
        disabled={currentPage === totalPages}
        className="px-6"
      >
        Next
        <ChevronRight className="h-5 w-5 ml-2" />
      </Button>
    </div>
  );
}
