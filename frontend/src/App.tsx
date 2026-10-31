import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AuthPage } from "./modules/auth/AuthPages";
import { Sidebar } from "./components/Sidebar";
import { CustomersPage } from "./modules/customers/CustomersPage";
import { CataloguePage } from "./modules/catalogue/CataloguePage";
import { PlansPage } from "./modules/catalogue/PlansPage";
import { QuotationsPage } from "./modules/quotations/QuotationsPage";
import { SubscriptionsPage } from "./modules/subscriptions/SubscriptionsPage";
import { StaffPage } from "./modules/staff/StaffPage";
import { CustomerPortalPage } from "./modules/portal/CustomerPortalPage";

const DashboardLayout: React.FC = () => {
  const { user } = useAuth();
  const isCustomer = user?.role === "customer";
  const [currentTab, setCurrentTab] = useState<string>(isCustomer ? "portal" : "customers");

  return (
    <div className="flex min-h-screen w-full bg-slate-50">
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />
      <main className="flex-1 overflow-y-auto">
        {currentTab === "customers" && <CustomersPage />}
        {currentTab === "catalogue" && <CataloguePage />}
        {currentTab === "plans" && <PlansPage />}
        {currentTab === "quotations" && <QuotationsPage />}
        {currentTab === "subscriptions" && <SubscriptionsPage />}
        {currentTab === "staff" && <StaffPage />}
        {currentTab === "portal" && <CustomerPortalPage />}
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
