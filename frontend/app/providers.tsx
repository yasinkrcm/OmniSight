"use client";

import { I18nProvider, RouterProvider } from "@heroui/react";
import { useRouter } from "next/navigation";

export function Providers({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  return (
    <I18nProvider locale="tr-TR">
      <RouterProvider navigate={router.push}>
        {children}
      </RouterProvider>
    </I18nProvider>
  );
}
