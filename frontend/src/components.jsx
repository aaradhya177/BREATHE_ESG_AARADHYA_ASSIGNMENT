import { NavLink } from "react-router-dom";

const statusClass = {
  COMPLETED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  PENDING: "bg-amber-50 text-amber-700 ring-amber-200",
  PROCESSING: "bg-blue-50 text-blue-700 ring-blue-200",
  FAILED: "bg-red-50 text-red-700 ring-red-200",
  PENDING_REVIEW: "bg-amber-50 text-amber-700 ring-amber-200",
  FLAGGED: "bg-orange-50 text-orange-700 ring-orange-200",
  APPROVED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  REJECTED: "bg-red-50 text-red-700 ring-red-200",
};

const scopeLabel = {
  SCOPE_1: "S1",
  SCOPE_2: "S2",
  SCOPE_3: "S3",
};

export function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-950">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <NavLink to="/" className="text-lg font-semibold">
            Breathe ESG
          </NavLink>
          <nav className="flex gap-2 text-sm">
            <NavItem to="/upload">Upload</NavItem>
            <NavItem to="/review">Review</NavItem>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">{children}</main>
    </div>
  );
}

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "rounded-md px-3 py-2 font-medium",
          isActive ? "bg-zinc-900 text-white" : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950",
        ].join(" ")
      }
    >
      {children}
    </NavLink>
  );
}

export function Button({ children, variant = "primary", className = "", ...props }) {
  const styles = {
    primary: "bg-zinc-900 text-white hover:bg-zinc-700 disabled:bg-zinc-300",
    secondary: "bg-white text-zinc-800 ring-1 ring-inset ring-zinc-300 hover:bg-zinc-50 disabled:text-zinc-400",
    approve: "bg-emerald-600 text-white hover:bg-emerald-700 disabled:bg-zinc-300",
    reject: "bg-red-600 text-white hover:bg-red-700 disabled:bg-zinc-300",
    flag: "bg-orange-500 text-white hover:bg-orange-600 disabled:bg-zinc-300",
  };

  return (
    <button
      className={`inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium transition ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function StatusBadge({ value }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ring-inset ${statusClass[value] ?? "bg-zinc-100 text-zinc-700 ring-zinc-200"}`}>
      {value}
    </span>
  );
}

export function ScopeBadge({ value }) {
  return (
    <span className="inline-flex rounded-full bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-200">
      {scopeLabel[value] ?? value}
    </span>
  );
}

export function EmptyState({ children }) {
  return <div className="rounded-md border border-dashed border-zinc-300 bg-white p-8 text-center text-sm text-zinc-500">{children}</div>;
}

export function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleDateString();
}

export function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
}
