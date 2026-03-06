import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, Shield, ArrowRight, X, Key, CheckCircle } from 'lucide-react';
import { setAuth } from "../utils/auth";
import api from '../services/api';

const TEST_ACCOUNTS = [
  { role: 'System Administrator', username: 'admin', password: 'admin123', color: 'bg-indigo-600', initial: 'A' },
  { role: 'HR Operations', username: 'hr', password: '1234', color: 'bg-sky-600', initial: 'H' },
  { role: 'Department Manager', username: 'manager', password: '12345', color: 'bg-teal-700', initial: 'M' },
  { role: 'Associate Staff', username: 'employee', password: '123456', color: 'bg-slate-600', initial: 'E' },
];

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showDemoModal, setShowDemoModal] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (!username.trim() || !password.trim()) return;
    setError('');
    setLoading(true);

    try {
      const params = new URLSearchParams();
      params.append('username', username.trim());
      params.append('password', password);

      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      setAuth(response.data.access_token, response.data.user);
      
      if (response.data.user.role === 'admin') {
        navigate('/dashboard');
      } else {
        navigate('/chat');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (account) => {
    setUsername(account.username);
    setPassword(account.password);
    setShowDemoModal(false);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex font-['Outfit',sans-serif]">

      {/* ── LEFT BRAND PANEL ── */}
      <div className="hidden lg:flex lg:w-[480px] xl:w-[540px] bg-slate-900 flex-col relative overflow-hidden shrink-0">
        <div className="absolute inset-0">
          <div className="absolute top-[-20%] left-[-20%] w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
          <div className="absolute bottom-[-10%] right-[-10%] w-80 h-80 bg-blue-600/15 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 flex flex-col h-full p-12">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Shield size={18} className="text-white" />
            </div>
            <span className="text-white font-bold text-sm tracking-tight">Enterprise RAG</span>
          </div>

          <div className="flex-1">
            <h1 className="text-4xl xl:text-5xl font-black text-white leading-[1.1] mb-6">
              Your company's knowledge,<br />
              <span className="text-indigo-400">on demand.</span>
            </h1>
            <p className="text-slate-400 text-base leading-relaxed mb-12 max-w-sm">
              Ask questions, retrieve policies, find documents — all powered by AI. Instant answers from your verified knowledge base.
            </p>

            <div className="space-y-4">
              {[
                'Role-based access — see only what you need',
                'Real-time AI responses via streaming',
                'Semantic search across all documents',
                'Full session history & audit trail',
              ].map((feat, i) => (
                <div key={i} className="flex items-center gap-3">
                  <CheckCircle size={16} className="text-emerald-500 shrink-0" />
                  <span className="text-slate-300 text-sm font-medium">{feat}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-auto">
            <div className="h-px bg-white/10 mb-6" />
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-slate-500 text-xs font-medium">All systems operational</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── RIGHT LOGIN PANEL ── */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="lg:hidden flex items-center gap-2.5 mb-10">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Shield size={15} className="text-white" />
          </div>
          <span className="font-bold text-slate-900 text-sm">Enterprise RAG</span>
        </div>

        <div className="w-full max-w-md">
          <div className="mb-10">
            <h2 className="text-3xl font-bold text-slate-900 mb-2">Welcome back</h2>
            <p className="text-slate-500 text-sm">Sign in with your corporate credentials to continue.</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <X size={16} className="text-red-500 shrink-0 mt-0.5" />
              <span className="text-sm text-red-700 font-medium">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                autoComplete="username"
                className="w-full px-4 py-3 bg-white border border-gray-200 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50 rounded-xl outline-none text-slate-800 text-sm font-medium placeholder:text-slate-300 transition-all"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="w-full px-4 py-3 pr-12 bg-white border border-gray-200 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50 rounded-xl outline-none text-slate-800 text-sm font-medium placeholder:text-slate-300 transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-600 transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !username.trim() || !password.trim()}
              className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 group shadow-sm"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Sign In
                  <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="flex items-center gap-4 my-6">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-slate-400 font-medium">or</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          <button
            onClick={() => setShowDemoModal(true)}
            className="w-full py-3.5 bg-white border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/50 text-slate-600 font-semibold rounded-xl transition-all flex items-center justify-center gap-2 text-sm"
          >
            <Key size={16} className="text-indigo-500" />
            Try Demo Accounts
          </button>

          <p className="text-center text-xs text-slate-400 mt-8">
            Enterprise RAG Platform · Secured with JWT Authentication
          </p>
        </div>
      </div>

      {showDemoModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
            <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-800">Demo Accounts</h3>
                <p className="text-xs text-slate-400 mt-0.5">Click any account to auto-fill credentials</p>
              </div>
              <button
                onClick={() => setShowDemoModal(false)}
                className="p-2 text-slate-300 hover:text-slate-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-4 space-y-2">
              {TEST_ACCOUNTS.map((account, i) => (
                <button
                  key={i}
                  onClick={() => fillCredentials(account)}
                  className="w-full flex items-center gap-4 p-4 bg-gray-50 hover:bg-indigo-50 border border-transparent hover:border-indigo-200 rounded-xl transition-all text-left group"
                >
                  <div className={`w-10 h-10 ${account.color} rounded-xl flex items-center justify-center text-white font-bold text-sm shrink-0`}>
                    {account.initial}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-slate-800 text-sm">{account.role}</div>
                    <div className="text-xs text-slate-400 mt-0.5 font-mono">
                      {account.username} / {account.password}
                    </div>
                  </div>
                  <ArrowRight size={15} className="text-gray-300 group-hover:text-indigo-500 transition-colors shrink-0" />
                </button>
              ))}
            </div>

            <div className="px-6 py-4 border-t border-gray-50 bg-gray-50">
              <p className="text-xs text-slate-400 text-center">
                Each role has different access permissions and AI capabilities
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LoginPage;