"use client";

import { Github, Mail } from "lucide-react";

export function ContactIcons() {
  return (
    <div className="fixed bottom-6 right-6 flex flex-col gap-3 z-50">
      <a
        href="mailto:boyangzhang25@gmail.com"
        className="bg-white dark:bg-gray-800 rounded-full p-3 shadow-lg text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:shadow-xl transition-all"
        aria-label="Email"
      >
        <Mail className="h-6 w-6" />
      </a>
      <a
        href="https://github.com/boyang-zhang1/RAGRace"
        target="_blank"
        rel="noopener noreferrer"
        className="bg-white dark:bg-gray-800 rounded-full p-3 shadow-lg text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 hover:shadow-xl transition-all"
        aria-label="GitHub Repository"
      >
        <Github className="h-6 w-6" />
      </a>
    </div>
  );
}
