"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";
import { getProviderInfo, getProviderDisplayName } from "@/lib/providerMetadata";

interface ProviderLabelProps {
  provider: string;
  className?: string;
  nameClassName?: string;
  iconClassName?: string;
  size?: number;
  hideName?: boolean;
}

export function ProviderLabel({
  provider,
  className,
  nameClassName,
  iconClassName,
  size = 18,
  hideName = false,
}: ProviderLabelProps) {
  const info = getProviderInfo(provider);
  const displayName = getProviderDisplayName(provider);

  if (!info) {
    return (
      <span className={cn("inline-flex items-center", className)}>
        {displayName}
      </span>
    );
  }

  return (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      <Image
        src={info.logoSrc}
        alt={info.alt}
        width={size}
        height={size}
        style={{ width: size, height: size }}
        className={cn("object-contain", iconClassName)}
      />
      {!hideName && (
        <span className={cn(nameClassName)}>{displayName}</span>
      )}
    </span>
  );
}
