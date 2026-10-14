# Pattern: Forms & Inputs
<!-- Derived from shadcn-ui/ui (MIT License) & addyosmani/web-quality-skills (MIT License) -->

Form controls designed for keyboard accessibility (WCAG 2.1 AA/AAA), deterministic validation states, and zero layout shifting.

## 1. Validated Form Field Group

Avoids ambient glow focus rings. Uses high-contrast 2px focus-visible rings with explicit error and hint slots.

```tsx
import React, { useId } from "react";

export interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
}

export function FormInput({
  label,
  hint,
  error,
  id: explicitId,
  disabled,
  className = "",
  ...props
}: FormInputProps) {
  const generatedId = useId();
  const inputId = explicitId || generatedId;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;

  return (
    <div className="flex flex-col space-y-1.5 w-full">
      <label
        htmlFor={inputId}
        className="text-xs font-sans font-medium text-foreground tracking-tight select-none"
      >
        {label}
      </label>

      <input
        id={inputId}
        disabled={disabled}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : hint ? hintId : undefined}
        className={`w-full px-3 py-2 text-sm font-sans bg-background border rounded-btn text-foreground placeholder:text-muted/60 transition-colors duration-fast outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 focus-visible:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed ${
          error ? "border-danger focus-visible:ring-danger" : "border-border hover:border-muted"
        } ${className}`}
        {...props}
      />

      {error ? (
        <span id={errorId} role="alert" className="text-xs font-sans text-danger mt-1">
          {error}
        </span>
      ) : hint ? (
        <span id={hintId} className="text-xs font-sans text-muted mt-1">
          {hint}
        </span>
      ) : null}
    </div>
  );
}
```

## 2. Accessible Filter Toolbar with Status Select

Standard compact action bar for data querying with explicit ARIA labels and keyboard focus contracts.

```tsx
import React from "react";

export interface FilterToolbarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  statusFilter: string;
  onStatusChange: (status: string) => void;
  statusOptions: { label: string; value: string }[];
}

export function FilterToolbar({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  statusOptions,
}: FilterToolbarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-surface border border-border rounded-card shadow-elevation-1">
      <div className="flex items-center gap-2 flex-1 min-w-[240px]">
        <input
          type="search"
          aria-label="Filter records"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Filter records by identifier or name..."
          className="w-full px-3 py-1.5 text-xs font-sans bg-background border border-border rounded-btn text-foreground placeholder:text-muted/60 outline-none focus-visible:ring-2 focus-visible:ring-primary"
        />
      </div>

      <div className="flex items-center gap-2">
        <select
          aria-label="Filter by status"
          value={statusFilter}
          onChange={(e) => onStatusChange(e.target.value)}
          className="px-2.5 py-1.5 text-xs font-sans bg-background border border-border rounded-btn text-foreground outline-none focus-visible:ring-2 focus-visible:ring-primary cursor-pointer"
        >
          <option value="all">All Statuses</option>
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
```
