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
    <div className="flex min-h-screen w-full bg-slate-50">
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />
      <main className="flex-1 overflow-y-auto">
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
