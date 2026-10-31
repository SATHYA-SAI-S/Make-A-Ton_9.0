import React, { createContext, useContext, useState, useEffect } from "react";
import { apiRequest } from "../api/client";

export interface User {
  id: string;
  email: string;
  role: "admin" | "staff" | "customer";
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  role: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: any) => Promise<void>;
  initiateRegistration: (payload: any) => Promise<any>;
  resendRegistrationOtp: (email: string) => Promise<any>;
  verifyRegistration: (email: string, otp: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<any>;
  resendForgotPasswordOtp: (email: string) => Promise<any>;
  verifyForgotPasswordOtp: (email: string, otp: string) => Promise<any>;
  confirmResetPassword: (email: string, resetToken: string, newPassword: string) => Promise<any>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("subscriptiq_access_token"));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const storedUser = localStorage.getItem("subscriptiq_user");
    if (storedUser && token) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.clear();
      }
    }
    setIsLoading(false);
  }, [token]);

  const login = async (email: string, password: string) => {
    const data: any = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("subscriptiq_access_token", data.access_token);
    localStorage.setItem("subscriptiq_refresh_token", data.refresh_token);
    localStorage.setItem("subscriptiq_user", JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  };

  const register = async (payload: any) => {
    const data: any = await apiRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    localStorage.setItem("subscriptiq_access_token", data.access_token);
    localStorage.setItem("subscriptiq_refresh_token", data.refresh_token);
    localStorage.setItem("subscriptiq_user", JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  };

  const initiateRegistration = async (payload: any) => {
    return await apiRequest("/auth/register/initiate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  };

  const resendRegistrationOtp = async (email: string) => {
    return await apiRequest("/auth/register/resend", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  };

  const verifyRegistration = async (email: string, otp: string) => {
    const data: any = await apiRequest("/auth/register/verify", {
      method: "POST",
      body: JSON.stringify({ email, otp }),
    });
    localStorage.setItem("subscriptiq_access_token", data.access_token);
    localStorage.setItem("subscriptiq_refresh_token", data.refresh_token);
    localStorage.setItem("subscriptiq_user", JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
  };

  const forgotPassword = async (email: string) => {
    return await apiRequest("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  };

  const resendForgotPasswordOtp = async (email: string) => {
    return await apiRequest("/auth/forgot-password/resend", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  };

  const verifyForgotPasswordOtp = async (email: string, otp: string) => {
    return await apiRequest("/auth/forgot-password/verify-otp", {
      method: "POST",
      body: JSON.stringify({ email, otp }),
    });
  };

  const confirmResetPassword = async (email: string, resetToken: string, newPassword: string) => {
    return await apiRequest("/auth/forgot-password/confirm", {
      method: "POST",
      body: JSON.stringify({ email, reset_token: resetToken, new_password: newPassword }),
    });
  };

  const logout = () => {
    localStorage.removeItem("subscriptiq_access_token");
    localStorage.removeItem("subscriptiq_refresh_token");
    localStorage.removeItem("subscriptiq_user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role || null,
        login,
        register,
        initiateRegistration,
        resendRegistrationOtp,
        verifyRegistration,
        forgotPassword,
        resendForgotPasswordOtp,
        verifyForgotPasswordOtp,
        confirmResetPassword,
        logout,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
