"use client";

import { Upload } from "lucide-react";
import { useState } from "react";

interface FileUploadZoneProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export function FileUploadZone({ onUpload, disabled = false }: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      onUpload(file);
    } else {
      alert("Please upload a PDF file");
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;

    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-lg p-12 text-center
        transition-colors
        ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
        ${
          isDragging && !disabled
            ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
            : "border-gray-300 hover:border-gray-400 dark:border-gray-700"
        }
      `}
      onClick={() => !disabled && document.getElementById("file-input")?.click()}
    >
      <Upload className="mx-auto mb-4 text-gray-400" size={48} />
      <p className="text-lg mb-2 font-medium">
        Drag & drop your PDF here
      </p>
      <p className="text-sm text-gray-500">
        or click to browse files
      </p>
      <input
        id="file-input"
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileSelect}
        disabled={disabled}
        className="hidden"
      />
    </div>
  );
}
