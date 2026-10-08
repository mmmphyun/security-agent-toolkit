# Pattern: Micro-Interactions & Motion
<!-- Derived from emilkowalski/skills (MIT License) & pbakaus/impeccable (Apache 2.0) -->

Derived from `emilkowalski/skills` and `pbakaus/impeccable` motion engineering principles. Enforces hardware-accelerated animations, spring physics, and haptic feedback while strictly prohibiting layout thrashing.

## 1. Golden Rules of Interface Motion

1. **Transform & Opacity Only**: Never animate layout geometry properties (`width`, `height`, `top`, `left`, `margin`, `padding`). Animate ONLY `transform` and `opacity` to avoid sub-pixel layout thrashing and maintain 60/120fps.
2. **Spring Physics for Physical Reality**: Use non-linear springs for interactive surfaces. Avoid mechanical linear transitions on pressable components.
3. **Interruptibility & Timing Budget**:
   - Micro-interaction duration MUST NOT exceed 350ms (`maxMicroInteractionDuration`).
   - Exit transitions must be faster (~100-150ms) than enter transitions (~200-250ms).
   - Press feedback must execute within 100ms (`active:scale-[0.98]`).

## 2. Interactive Tactile Button (Tactile Press Feedback)

Implements `scale(0.98)` active press physics, high-contrast focus rings, and hardware acceleration hints.

```tsx
import React from "react";

export interface TactileButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md";
}

export function TactileButton({
  children,
  variant = "primary",
  size = "md",
  className = "",
  disabled,
  ...props
}: TactileButtonProps) {
  const variantStyles = {
    primary: "bg-primary text-primary-foreground shadow-elevation-1 hover:shadow-elevation-2 active:shadow-elevation-1 hover:brightness-105 active:brightness-95",
    secondary: "bg-surface text-foreground border border-border shadow-elevation-1 hover:bg-background active:bg-surface",
    danger: "bg-danger text-danger-foreground shadow-elevation-1 hover:brightness-105 active:brightness-95",
  }[variant];

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
  }[size];

  return (
    <button
      disabled={disabled}
      className={`inline-flex items-center justify-center font-sans font-medium rounded-btn select-none transition-all duration-fast ease-apple-snappy active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:pointer-events-none will-change-transform ${variantStyles} ${sizeStyles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
```

## 3. Drawer / Sheet Enter & Exit Physics

Emil Kowalski spring parameters mapped to CSS transitions: Enter utilizes spring deceleration, Exit utilizes snappy acceleration.

```tsx
import React, { useEffect } from "react";

export interface SheetProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Sheet({ isOpen, onClose, title, children }: SheetProps) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop: Opacity transition */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 transition-opacity duration-fast ease-out will-change-opacity animate-in fade-in"
        aria-hidden="true"
      />

      {/* Slide Surface: Transform X transition */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative w-full max-w-md h-full bg-surface border-l border-border shadow-elevation-4 z-10 flex flex-col transition-transform duration-normal ease-apple-spring will-change-transform animate-in slide-in-from-right"
      >
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h2 className="text-sm font-sans font-semibold text-foreground tracking-tight">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="text-xs font-mono text-muted hover:text-foreground p-1 rounded-btn focus-visible:ring-2 focus-visible:ring-primary"
            aria-label="Close dialog"
          >
            ESC
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {children}
        </div>
      </div>
    </div>
  );
}
```
