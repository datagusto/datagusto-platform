"use client"

// Use sonner for toast notifications
import { toast as sonnerToast } from "sonner"

export interface Toast {
  title: string
  description?: string
  variant?: "default" | "destructive"
}

export function useToast() {
  const toast = ({ title, description, variant = "default" }: Toast) => {
    const message = description ? `${title}: ${description}` : title
    
    if (variant === "destructive") {
      sonnerToast.error(message)
    } else {
      sonnerToast.success(message)
    }
  }

  return {
    toast,
    dismiss: () => {}, // sonner handles dismissal automatically
    toasts: [], // not needed with sonner
  }
}