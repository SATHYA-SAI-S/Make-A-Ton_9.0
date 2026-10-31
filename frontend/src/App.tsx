import React, { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AuthPage } from "./modules/auth/AuthPages";
import { Sidebar } from "./components/Sidebar";
import { AdminDashboard } from "./modules/dashboard/AdminDashboard";
import { StaffDashboard } from "./modules/dashboard/StaffDashboard";
import { CustomersPage } from "./modules/customers/CustomersPage";
import { CataloguePage } from "./modules/catalogue/CataloguePage";
import { PlansPage } from "./modules/catalogue/PlansPage";
import { QuotationsPage } from "./modules/quotations/QuotationsPage";
import { SubscriptionsPage } from "./modules/subscriptions/SubscriptionsPage";
import { StaffPage } from "./modules/staff/StaffPage";
import { CustomerPortalPage } from "./modules/portal/CustomerPortalPage";

const getDefaultTabForRole = (role?: string) => {
  if (role === "admin") return "dashboard";
  if (role === "staff") return "staff-dashboard";
  return "portal";
};

const DashboardLayout: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role || "customer";
  const [currentTab, setCurrentTab] = useState<string>(() => getDefaultTabForRole(role));

  useEffect(() => {
    setCurrentTab(getDefaultTabForRole(role));
  }, [role]);

  return (
    <div className="flex min-h-screen w-full bg-[#070b12] text-slate-100">
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">{role}</span>
            <span className="text-slate-600">/</span>
            <span className="text-xs font-semibold text-white capitalize">{currentTab.replace("-", " ")}</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-950/80 border border-slate-800 text-[11px] font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-400">Core API:</span>
              <span className="text-emerald-400">8000</span>
            </div>
            <a
              href="http://127.0.0.1:8025"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950/80 border border-slate-800 hover:border-cyan-500/40 text-[11px] font-mono text-slate-300 hover:text-white transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              <span>Mailpit</span>
              <span className="text-cyan-400">:8025 ↗</span>
            </a>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-gradient-to-b from-[#070b12] to-[#0a0f1d]">
          {/* Customer View */}
          {role === "customer" && <CustomerPortalPage />}

          {/* Staff Views */}
          {role === "staff" && (
            <>
              {currentTab === "staff-dashboard" && <StaffDashboard onNavigate={setCurrentTab} />}
              {currentTab === "customers" && <CustomersPage />}
              {currentTab === "catalogue" && <CataloguePage />}
              {currentTab === "plans" && <PlansPage />}
              {currentTab === "quotations" && <QuotationsPage />}
              {currentTab === "subscriptions" && <SubscriptionsPage />}
              {/* If tab not allowed for staff, fallback to staff-dashboard */}
              {["dashboard", "staff", "portal"].includes(currentTab) && (
                <StaffDashboard onNavigate={setCurrentTab} />
              )}
            </>
          )}

          {/* Admin Views */}
          {role === "admin" && (
            <>
              {currentTab === "dashboard" && <AdminDashboard onNavigate={setCurrentTab} />}
              {currentTab === "customers" && <CustomersPage />}
              {currentTab === "catalogue" && <CataloguePage />}
              {currentTab === "plans" && <PlansPage />}
              {currentTab === "quotations" && <QuotationsPage />}
              {currentTab === "subscriptions" && <SubscriptionsPage />}
              {currentTab === "staff" && <StaffPage />}
              {/* If admin navigates to non-admin tab */}
              {["staff-dashboard", "portal"].includes(currentTab) && (
                <AdminDashboard onNavigate={setCurrentTab} />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

const MainApp: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-slate-950 text-white text-sm">
        Loading SubscriptIQ workspace...
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return <DashboardLayout />;
};

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
