import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import {
  Check,
  X,
  Lock,
  Mail,
  Building,
  Phone,
  Eye,
  EyeOff,
  Key,
  ArrowLeft,
  RefreshCw,
  Clock,
  ShieldCheck
} from "lucide-react";

type AuthMode =
  | "login"
  | "register"
  | "verify-reg"
  | "forgot"
  | "verify-reset"
  | "reset-new-password";

export const AuthPage: React.FC = () => {
  const {
    login,
    initiateRegistration,
    resendRegistrationOtp,
    verifyRegistration,
    forgotPassword,
    resendForgotPasswordOtp,
    verifyForgotPasswordOtp,
    confirmResetPassword,
  } = useAuth();

  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState<string>("");
  const [maskedEmail, setMaskedEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [name, setName] = useState<string>("");
  const [phone, setPhone] = useState<string>("");

  // OTP inputs
  const [regOtp, setRegOtp] = useState<string>("");
  const [resetOtp, setResetOtp] = useState<string>("");

  // Reset password states
  const [resetToken, setResetToken] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  const [showNewPassword, setShowNewPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);

  // Status banners
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Timers: 10-minute expiry countdown (600 seconds) & 60-second resend cooldown
  const [expirySeconds, setExpirySeconds] = useState<number>(600);
  const [cooldownSeconds, setCooldownSeconds] = useState<number>(0);

  useEffect(() => {
    let interval: any = null;
    if (mode === "verify-reg" || mode === "verify-reset") {
      interval = setInterval(() => {
        setExpirySeconds((prev) => (prev > 0 ? prev - 1 : 0));
        setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [mode]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Password Policy Checkers
  const hasMinLen = password.length > 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>_\-+=[\]\\/`~]/.test(password);
  const isPasswordValid = hasMinLen && hasUpper && hasLower && hasSpecial;

  const isNewPasswordValid =
    newPassword.length > 8 &&
    /[A-Z]/.test(newPassword) &&
    /[a-z]/.test(newPassword) &&
    /[!@#$%^&*(),.?":{}|<>_\-+=[\]\\/`~]/.test(newPassword);

  const resetMessages = () => {
    setError(null);
    setSuccessMsg(null);
  };

  // 1. Login Handler
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  // 2. Register (Step 1) Handler
  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();

    if (!isPasswordValid) {
      setError("Please ensure your password satisfies all policy requirements.");
      return;
    }

    setLoading(true);
    try {
      const resp = await initiateRegistration({
        email,
        password,
        name,
        phone,
        country: "India",
        timezone: "Asia/Kolkata",
      });
      setMaskedEmail(resp.masked_email || email);
      setSuccessMsg(resp.message || `Verification code sent to ${resp.masked_email || email}.`);
      setExpirySeconds(600);
      setCooldownSeconds(60);
      setRegOtp("");
      setMode("verify-reg");
    } catch (err: any) {
      setError(err.message || "Failed to initiate registration.");
    } finally {
      setLoading(false);
    }
  };

  // 2b. Resend Registration OTP
  const handleResendRegistrationOtp = async () => {
    if (cooldownSeconds > 0) return;
    resetMessages();
    setLoading(true);
    try {
      const resp = await resendRegistrationOtp(email);
      setSuccessMsg(resp.message || "A fresh verification code has been dispatched.");
      setExpirySeconds(600);
      setCooldownSeconds(60);
      setRegOtp("");
    } catch (err: any) {
      setError(err.message || "Failed to resend verification code.");
    } finally {
      setLoading(false);
    }
  };

  // 3. Register (Step 2 - Verify OTP) Handler
  const handleVerifyRegistrationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();

    if (regOtp.trim().length !== 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    setLoading(true);
    try {
      await verifyRegistration(email, regOtp.trim());
    } catch (err: any) {
      setError(err.message || "Invalid or expired verification code.");
    } finally {
      setLoading(false);
    }
  };

  // 4. Forgot Password Request Handler
  const handleForgotPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    setLoading(true);
    try {
      const resp = await forgotPassword(email);
      setMaskedEmail(resp.masked_email || email);
      setSuccessMsg(resp.message || "If registered, a verification code has been dispatched.");
      setExpirySeconds(600);
      setCooldownSeconds(60);
      setResetOtp("");
      setMode("verify-reset");
    } catch (err: any) {
      setError(err.message || "Failed to submit request.");
    } finally {
      setLoading(false);
    }
  };

  // 4b. Resend Forgot Password OTP
  const handleResendForgotPasswordOtp = async () => {
    if (cooldownSeconds > 0) return;
    resetMessages();
    setLoading(true);
    try {
      const resp = await resendForgotPasswordOtp(email);
      setSuccessMsg(resp.message || "A fresh verification code has been dispatched.");
      setExpirySeconds(600);
      setCooldownSeconds(60);
      setResetOtp("");
    } catch (err: any) {
      setError(err.message || "Failed to resend verification code.");
    } finally {
      setLoading(false);
    }
  };

  // 5. Verify Forgot Password OTP Handler
  const handleVerifyResetOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();

    if (resetOtp.trim().length !== 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    setLoading(true);
    try {
      const resp = await verifyForgotPasswordOtp(email, resetOtp.trim());
      setResetToken(resp.reset_token);
      setSuccessMsg("Verification code confirmed! Please set your new password.");
      setMode("reset-new-password");
    } catch (err: any) {
      setError(err.message || "Invalid or expired verification code.");
    } finally {
      setLoading(false);
    }
  };

  // 6. Confirm Reset Password Handler
  const handleConfirmResetPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation password do not match.");
      return;
    }

    if (!isNewPasswordValid) {
      setError("Password must satisfy all policy requirements (min 9 chars, uppercase, lowercase, special character).");
      return;
    }

    setLoading(true);
    try {
      await confirmResetPassword(email, resetToken, newPassword);
      setSuccessMsg("Password updated successfully! Please sign in with your new password.");
      setPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMode("login");
    } catch (err: any) {
      setError(err.message || "Failed to update password. Session may have expired.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (demoEmail: string, demoPass: string) => {
    resetMessages();
    setEmail(demoEmail);
    setPassword(demoPass);
    setMode("login");
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-emerald-500 text-white font-bold text-2xl flex items-center justify-center mx-auto mb-3 shadow-lg shadow-emerald-500/20">
            S
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">SubscriptIQ</h2>
          <p className="text-sm text-slate-400 mt-1">
            {mode === "login" && "Sign in to manage your subscriptions"}
            {mode === "register" && "Create your customer account"}
            {mode === "verify-reg" && "Email Verification"}
            {mode === "forgot" && "Recover your password"}
            {mode === "verify-reset" && "Verify Password Reset Code"}
            {mode === "reset-new-password" && "Set a New Password"}
          </p>
        </div>

        {/* Feedback alerts */}
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            {error}
          </div>
        )}
        {successMsg && (
          <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
            {successMsg}
          </div>
        )}

        {/* 1. LOGIN MODE */}
        {mode === "login" && (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => {
                    resetMessages();
                    setMode("forgot");
                  }}
                  className="text-xs text-emerald-400 hover:text-emerald-300 hover:underline transition-colors font-medium"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-9 pr-10 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
                <button
                  type="button"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg text-sm transition-colors shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>
        )}

        {/* 2. REGISTER MODE (Step 1) */}
        {mode === "register" && (
          <form onSubmit={handleRegisterSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Full Name / Organization
              </label>
              <div className="relative">
                <Building className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Acme Global Inc"
                  className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-9 pr-10 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
                <button
                  type="button"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {/* Password Requirements live checklist */}
              <div className="mt-3 p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-xs space-y-1.5">
                <p className="font-semibold text-slate-400 mb-1">Password Requirements:</p>
                <div className={`flex items-center gap-1.5 ${hasMinLen ? "text-emerald-400" : "text-slate-500"}`}>
                  {hasMinLen ? <Check size={14} /> : <X size={14} />} More than 8 characters (min 9)
                </div>
                <div className={`flex items-center gap-1.5 ${hasUpper ? "text-emerald-400" : "text-slate-500"}`}>
                  {hasUpper ? <Check size={14} /> : <X size={14} />} At least one uppercase letter
                </div>
                <div className={`flex items-center gap-1.5 ${hasLower ? "text-emerald-400" : "text-slate-500"}`}>
                  {hasLower ? <Check size={14} /> : <X size={14} />} At least one lowercase letter
                </div>
                <div className={`flex items-center gap-1.5 ${hasSpecial ? "text-emerald-400" : "text-slate-500"}`}>
                  {hasSpecial ? <Check size={14} /> : <X size={14} />} At least one special character
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Phone Number (Optional)
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg text-sm transition-colors shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              {loading ? "Sending Verification Code..." : "Continue to Verification"}
            </button>
          </form>
        )}

        {/* 3. VERIFY REGISTRATION MODE (Step 2) */}
        {mode === "verify-reg" && (
          <form onSubmit={handleVerifyRegistrationSubmit} className="space-y-4">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-300 space-y-1">
              <div className="flex items-center gap-2 font-semibold text-emerald-400">
                <ShieldCheck size={16} />
                Email Verification Code Required
              </div>
              <p>
                Enter the six-digit verification code sent to your email address:
              </p>
              <p className="font-mono font-bold text-white tracking-wide">{maskedEmail}</p>
              <div className="flex items-center gap-1.5 pt-1 text-slate-400 font-mono text-[11px]">
                <Clock size={13} className="text-amber-400" />
                <span>Code expires in: <strong className="text-amber-400">{formatTimer(expirySeconds)}</strong></span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Six-Digit Verification Code
              </label>
              <div className="relative">
                <Key className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={regOtp}
                  onChange={(e) => setRegOtp(e.target.value.replace(/\D/g, ""))}
                  placeholder="000000"
                  className="w-full pl-9 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white text-xl tracking-widest font-mono text-center focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || regOtp.length !== 6 || expirySeconds === 0}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg text-sm transition-colors shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              {loading ? "Activating Account..." : "Verify Email"}
            </button>

            <div className="flex items-center justify-between pt-2 text-xs">
              <button
                type="button"
                onClick={() => {
                  resetMessages();
                  setMode("register");
                }}
                className="text-slate-400 hover:text-white flex items-center gap-1"
              >
                <ArrowLeft size={14} /> Back to details
              </button>
              <button
                type="button"
                onClick={handleResendRegistrationOtp}
                disabled={loading || cooldownSeconds > 0}
                className="text-emerald-400 hover:underline flex items-center gap-1 disabled:opacity-40 disabled:no-underline"
              >
                <RefreshCw size={14} />
                {cooldownSeconds > 0 ? `Resend Code (${cooldownSeconds}s)` : "Resend Code"}
              </button>
            </div>
          </form>
        )}

        {/* 4. FORGOT PASSWORD MODE (Step 1) */}
        {mode === "forgot" && (
          <form onSubmit={handleForgotPasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Enter your registered email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email address"
                  className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg text-sm transition-colors shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              {loading ? "Sending Verification Code..." : "Send Reset Code"}
            </button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  resetMessages();
                  setMode("login");
                }}
                className="text-xs text-slate-400 hover:text-white flex items-center gap-1 mx-auto"
              >
                <ArrowLeft size={14} /> Back to Sign In
              </button>
            </div>
          </form>
        )}

        {/* 5. VERIFY FORGOT PASSWORD OTP (Step 2) */}
        {mode === "verify-reset" && (
          <form onSubmit={handleVerifyResetOtpSubmit} className="space-y-4">
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-300 space-y-1">
              <div className="flex items-center gap-2 font-semibold text-blue-400">
                <ShieldCheck size={16} />
                Password Reset Verification Code
              </div>
              <p>
                Enter the six-digit verification code sent to:
              </p>
              <p className="font-mono font-bold text-white tracking-wide">{maskedEmail}</p>
              <div className="flex items-center gap-1.5 pt-1 text-slate-400 font-mono text-[11px]">
                <Clock size={13} className="text-amber-400" />
                <span>Code expires in: <strong className="text-amber-400">{formatTimer(expirySeconds)}</strong></span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Six-Digit Verification Code
              </label>
              <div className="relative">
                <Key className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={resetOtp}
                  onChange={(e) => setResetOtp(e.target.value.replace(/\D/g, ""))}
                  placeholder="000000"
                  className="w-full pl-9 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white text-xl tracking-widest font-mono text-center focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || resetOtp.length !== 6 || expirySeconds === 0}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg text-sm transition-colors shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              {loading ? "Verifying..." : "Verify Code"}
            </button>

            <div className="flex items-center justify-between pt-2 text-xs">
              <button
                type="button"
                onClick={() => {
                  resetMessages();
                  setMode("forgot");
                }}
                className="text-slate-400 hover:text-white flex items-center gap-1"
              >
                <ArrowLeft size={14} /> Back
              </button>
              <button
                type="button"
                onClick={handleResendForgotPasswordOtp}
                disabled={loading || cooldownSeconds > 0}
                className="text-emerald-400 hover:underline flex items-center gap-1 disabled:opacity-40 disabled:no-underline"
              >
                <RefreshCw size={14} />
                {cooldownSeconds > 0 ? `Resend Code (${cooldownSeconds}s)` : "Resend Code"}
              </button>
            </div>
          </form>
        )}

        {/* 6. SET NEW PASSWORD MODE (Step 3) */}
        {mode === "reset-new-password" && (
          <form onSubmit={handleConfirmResetPasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type={showNewPassword ? "text" : "password"}
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-9 pr-10 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
                <button
                  type="button"
                  aria-label={showNewPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showNewPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {/* Password checklist */}
              <div className="mt-3 p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-xs space-y-1">
                <p className="font-semibold text-slate-400 mb-1">Password Requirements:</p>
                <div className={`flex items-center gap-1.5 ${newPassword.length > 8 ? "text-emerald-400" : "text-slate-500"}`}>
                  {newPassword.length > 8 ? <Check size={14} /> : <X size={14} />} More than 8 characters (min 9)
                </div>
                <div className={`flex items-center gap-1.5 ${/[A-Z]/.test(newPassword) ? "text-emerald-400" : "text-slate-500"}`}>
                  {/[A-Z]/.test(newPassword) ? <Check size={14} /> : <X size={14} />} At least one uppercase letter
                </div>
                <div className={`flex items-center gap-1.5 ${/[a-z]/.test(newPassword) ? "text-emerald-400" : "text-slate-500"}`}>
                  {/[a-z]/.test(newPassword) ? <Check size={14} /> : <X size={14} />} At least one lowercase letter
                </div>
                <div className={`flex items-center gap-1.5 ${/[!@#$%^&*(),.?":{}|<>_\-+=[\]\\/`~]/.test(newPassword) ? "text-emerald-400" : "text-slate-500"}`}>
                  {/[!@#$%^&*(),.?":{}|<>_\-+=[\]\\/`~]/.test(newPassword) ? <Check size={14} /> : <X size={14} />} At least one special character
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Confirm New Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-9 pr-10 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                />
                <button
                  type="button"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !isNewPasswordValid || newPassword !== confirmPassword}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg text-sm transition-colors shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              {loading ? "Updating Password..." : "Update Password"}
            </button>
          </form>
        )}

        {/* Bottom Mode Switcher */}
        {mode === "login" && (
          <div className="mt-6 text-center text-sm text-slate-400">
            Don't have an account?{" "}
            <button
              onClick={() => {
                resetMessages();
                setMode("register");
              }}
              className="text-emerald-400 hover:underline font-medium"
            >
              Sign Up
            </button>
          </div>
        )}

        {mode === "register" && (
          <div className="mt-6 text-center text-sm text-slate-400">
            Already registered?{" "}
            <button
              onClick={() => {
                resetMessages();
                setMode("login");
              }}
              className="text-emerald-400 hover:underline font-medium"
            >
              Sign In
            </button>
          </div>
        )}

        {/* Demo Fast Login Buttons */}
        <div className="mt-8 pt-6 border-t border-slate-800">
          <p className="text-xs text-center text-slate-500 font-semibold uppercase tracking-wider mb-3">
            Demo Instant Sign In (Pre-seeded Accounts)
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin("admin@example.com", "Admin@Secure123!")}
              className="py-1.5 px-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg font-medium transition-colors border border-slate-700 text-center"
            >
              Admin
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("staff@example.com", "Staff@Secure123!")}
              className="py-1.5 px-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg font-medium transition-colors border border-slate-700 text-center"
            >
              Staff
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("acme@example.com", "Customer@Secure123!")}
              className="py-1.5 px-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg font-medium transition-colors border border-slate-700 text-center"
            >
              Customer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
