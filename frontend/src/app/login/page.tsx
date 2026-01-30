"use client";

import React from "react";
import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";
import { motion } from "framer-motion";
import { Terminal, ShieldCheck, Zap } from "lucide-react";
import { useRouter } from "next/navigation";
import axios from "axios";

// --- REPLACE THIS WITH YOUR ACTUAL GOOGLE CLIENT ID ---
const GOOGLE_CLIENT_ID = "169790204914-3bf1tohqo7krth37dqof2mmre2dfgnv4.apps.googleusercontent.com"; 

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = React.useState("");

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      const googleToken = credentialResponse.credential;
      
      // Send Google Token to our Backend to verify and get User ID
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await axios.post(`${API_URL}/api/v1/auth/google`, {
        token: googleToken
      });

      // Save our internal session token
      localStorage.setItem("tm_token", res.data.access_token);
      localStorage.setItem("tm_user", JSON.stringify(res.data.user));

      // Redirect to Dashboard
      router.push("/dashboard");
      
    } catch (err) {
      console.error("Login Failed", err);
      setError("Authentication failed. Please try again.");
    }
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="min-h-screen flex bg-background text-text-main">
        
        {/* LEFT SIDE: Visuals */}
        <div className="hidden lg:flex w-1/2 bg-surface relative overflow-hidden flex-col justify-between p-12">
          <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
          <div className="z-10">
            <div className="flex items-center gap-2 text-primary font-bold text-2xl tracking-tighter mb-4">
              <div className="p-1.5 bg-primary/10 rounded-lg border border-primary/20">
                <Terminal className="w-6 h-6" />
              </div>
              TradeMatrix AI
            </div>
            <h1 className="text-5xl font-bold text-white leading-tight mb-6">
              Master the Markets <br /> with <span className="text-primary">Automation.</span>
            </h1>
            <p className="text-text-dim text-lg max-w-md">
              Deploy institutional-grade algorithms on your personal broker account. No code required.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 z-10">
             <div className="bg-black/40 backdrop-blur-md p-4 rounded-xl border border-border">
                <Zap className="text-yellow-400 mb-2" />
                <h3 className="font-bold text-white">Ultra Low Latency</h3>
                <p className="text-xs text-text-dim">Direct execution engine.</p>
             </div>
             <div className="bg-black/40 backdrop-blur-md p-4 rounded-xl border border-border">
                <ShieldCheck className="text-green-400 mb-2" />
                <h3 className="font-bold text-white">AES-256 Security</h3>
                <p className="text-xs text-text-dim">Your keys never leave the vault.</p>
             </div>
          </div>
        </div>

        {/* RIGHT SIDE: Login Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-md"
          >
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold text-white mb-2">Welcome Back</h2>
              <p className="text-text-dim">Sign in to access your trading console.</p>
            </div>

            <div className="flex justify-center">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => setError("Google Login Failed")}
                theme="filled_black"
                size="large"
                shape="pill"
                width="100%"
              />
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm text-center">
                {error}
              </div>
            )}

            <p className="mt-8 text-center text-xs text-text-dim">
              By continuing, you agree to our Terms of Service and Privacy Policy.
            </p>
          </motion.div>
        </div>

      </div>
    </GoogleOAuthProvider>
  );
}