import React from "react";
import {
  LayoutDashboard,
  Users,
  Package,
  Calendar,
  FileText,
  Repeat,
  ShieldCheck,
  UserCheck,
  LogOut
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const { user, logout } = useAuth();
  const role = user?.role || "customer";

  const adminNavItems = [
    { id: "dashboard", label: "Admin Overview", icon: LayoutDashboard },
    { id: "customers", label: "Customers", icon: Users },
    { id: "catalogue", label: "Products & Variants", icon: Package },
    { id: "plans", label: "Subscription Plans", icon: Calendar },
    { id: "quotations", label: "Quotations", icon: FileText },
    { id: "subscriptions", label: "Subscriptions", icon: Repeat },
    { id: "staff", label: "Staff Management", icon: ShieldCheck },
  ];

  const staffNavItems = [
    { id: "staff-dashboard", label: "Staff Workspace", icon: LayoutDashboard },
    { id: "customers", label: "Customers", icon: Users },
    { id: "catalogue", label: "Products & Variants", icon: Package },
    { id: "plans", label: "Subscription Plans", icon: Calendar },
    { id: "quotations", label: "Quotations", icon: FileText },
    { id: "subscriptions", label: "Subscriptions", icon: Repeat },
  ];

  const customerNavItems = [
    { id: "portal", label: "Customer Portal", icon: UserCheck },
  ];

  const items =
    role === "admin"
      ? adminNavItems
      : role === "staff"
      ? staffNavItems
      : customerNavItems;

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col justify-between min-h-screen shrink-0 border-r border-slate-800">
      <div>
        <div className="p-6 flex items-center gap-3 border-b border-slate-800">
          <div className="w-10 h-10 rounded-lg bg-emerald-500 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-emerald-500/20">
            S
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">SubscriptIQ</h1>
            <p className="text-xs text-slate-400 font-medium capitalize">
              {role} Workspace
            </p>
          </div>
        </div>

        <nav className="p-4 space-y-1">
          {items.map((item) => {
            const Icon = item.icon;
            const active = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-800">
        <div className="mb-3 px-2">
          <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider block">Logged in as</span>
          <p className="text-xs text-slate-300 font-medium truncate">{user?.email}</p>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 rounded-lg transition-colors"
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
