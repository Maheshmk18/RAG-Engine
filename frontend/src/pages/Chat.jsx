import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Send, Plus, MessageSquare, Trash2, LogOut, FileText,
  User, Shield, Bot, Sparkles,
  Menu, X, LayoutDashboard,
  Calendar, Gift, UserCheck, BarChart2,
  DollarSign, Users, Package, TrendingUp,
  FileSearch, BookOpen, FolderOpen,
  Home, Receipt, Star, ArrowRight,
  Database, AlertTriangle, RefreshCw, WifiOff,
  ChevronRight, ExternalLink, Info, Search
} from 'lucide-react';
import api from '../services/api';
import { getUser, isAdmin } from '../utils/auth';
import ProfileModal from '../components/ProfileModal';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ROLE_CONFIG = {
  admin: {
    title: 'Admin Intelligence',
    subtitle: 'Full System Access',
    description: 'Query documents, manage knowledge base, and extract strategic insights from all enterprise data.',
    placeholder: 'Ask anything about your documents or system...',
    accentColor: '#6366f1',
    gradientFrom: '#4f46e5',
    gradientTo: '#7c3aed',
    suggestions: [
      { Icon: FileSearch, label: 'Summarize all uploaded documents', desc: 'Get a full knowledge base overview' },
      { Icon: BookOpen, label: 'What policies are in the knowledge base?', desc: 'Explore policies and guidelines' },
      { Icon: Database, label: 'Show system overview', desc: 'View indexed data and metrics' },
      { Icon: FolderOpen, label: 'List all document categories', desc: 'Browse by category' },
    ]
  },
  hr: {
    title: 'HR Intelligence',
    subtitle: 'HR & Compliance Specialist',
    description: 'Specialized in HR policies, compliance, benefits, and talent management across the organization.',
    placeholder: 'Ask about HR policies, benefits, or compliance...',
    accentColor: '#0284c7',
    gradientFrom: '#0369a1',
    gradientTo: '#0891b2',
    suggestions: [
      { Icon: Calendar, label: 'What is the annual leave policy?', desc: 'Leave entitlements & procedures' },
      { Icon: Gift, label: 'Explain maternity benefits', desc: 'Benefits & parental leave details' },
      { Icon: UserCheck, label: 'How does the onboarding process work?', desc: 'Employee onboarding steps' },
      { Icon: BarChart2, label: 'What are the performance review guidelines?', desc: 'Review cycles & criteria' },
    ]
  },
  manager: {
    title: 'Manager Intelligence',
    subtitle: 'Decision Support System',
    description: 'Decision support for operational strategy, team management, performance tracking, and budgeting.',
    placeholder: 'Ask about operations or team management...',
    accentColor: '#0f766e',
    gradientFrom: '#0f766e',
    gradientTo: '#0369a1',
    suggestions: [
      { Icon: DollarSign, label: 'What are the budget approval procedures?', desc: 'Budget workflow & approvals' },
      { Icon: Users, label: 'How do I handle conflict resolution?', desc: 'Team management guidelines' },
      { Icon: Package, label: 'Explain resource allocation guidelines', desc: 'Resource planning & allocation' },
      { Icon: TrendingUp, label: 'What are managerial KPIs?', desc: 'Key performance indicators' },
    ]
  },
  employee: {
    title: 'Employee Assistant',
    subtitle: 'Your Personal AI Guide',
    description: 'Your personal guide to company policies, benefits, procedures, and everything you need to know.',
    placeholder: 'Ask about company policies or procedures...',
    accentColor: '#2563eb',
    gradientFrom: '#1d4ed8',
    gradientTo: '#4f46e5',
    suggestions: [
      { Icon: Calendar, label: 'What is the holiday schedule?', desc: 'Upcoming holidays & time off' },
      { Icon: Receipt, label: 'How do I submit an expense report?', desc: 'Expense claim process' },
      { Icon: Home, label: 'Explain the remote work policy', desc: 'Work-from-home guidelines' },
      { Icon: Star, label: 'What are the company values?', desc: 'Culture & core principles' },
    ]
  }
};


const ROLE_LABELS = {
  admin: 'System Administrator',
  hr: 'HR Operations',
  manager: 'Department Manager',
  employee: 'Associate Staff',
};

function TypingIndicator({ color }) {
  return (
    <div className="chat-typing" style={{ '--dot-color': color || '#6366f1' }}>
      <span /><span /><span />
    </div>
  );
}

export default function Chat() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [user, setUser] = useState(getUser());
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true); // Managed by window size or toggle
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [sidebarVisible, setSidebarVisible] = useState(!isMobile);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const userRole = user?.role || 'employee';
  const roleInfo = ROLE_CONFIG[userRole] || ROLE_CONFIG.employee;
  const roleLabel = ROLE_LABELS[userRole] || 'Staff';

  useEffect(() => {
    if (!getUser()) { navigate('/login'); return; }
    fetchSessions();

    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) setSidebarVisible(true);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px';
    }
  }, [input]);

  const fetchSessions = async () => {
    try {
      const r = await api.get('/chat/sessions');
      setSessions(r.data || []);
    } catch (e) { console.error(e); }
  };

  const loadSession = async (sid) => {
    try {
      if (isMobile) setSidebarVisible(false);
      const r = await api.get(`/chat/sessions/${sid}`);
      setCurrentSession(sid);
      setMessages(r.data.messages || []);
    } catch (e) { console.error(e); }
  };

  const handleNewChat = () => {
    if (isMobile) setSidebarVisible(false);
    setCurrentSession(null);
    setMessages([]);
    textareaRef.current?.focus();
  };

  const handleSubmit = async (e, directText) => {
    e?.preventDefault();
    const trimmed = (directText ?? input).trim();
    if (!trimmed || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: trimmed }]);
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ message: trimmed, session_id: currentSession }),
      });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `Error ${res.status}`); }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let text = '', buf = '';
      setMessages(prev => [...prev, { role: 'assistant', content: '', thinking: true }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split('\n\n');
        buf = lines.pop() || '';
        for (const line of lines) {
          const t = line.trim();
          if (!t.startsWith('data: ')) continue;
          const ds = t.slice(6);
          if (ds === '[DONE]') continue;
          try {
            const d = JSON.parse(ds);

            if (d.error === true) {
              const errorPayload = {
                role: 'error',
                errorType: d.error_type || 'general',
                errorMsg: d.error_message || 'Something went wrong. Please try again.',
              };
              setMessages(prev => {
                const u = [...prev];
                const last = u[u.length - 1];
                if (last?.role === 'assistant') { u[u.length - 1] = errorPayload; }
                else { u.push(errorPayload); }
                return u;
              });
              return;
            }
            if (d.content) {
              text += d.content;
              setMessages(prev => {
                const u = [...prev];
                u[u.length - 1] = { role: 'assistant', content: text, thinking: false };
                return u;
              });
            }
            if (d.done && d.session_id) {
              if (!currentSession) setCurrentSession(d.session_id);
            }
          } catch (_) { }
        }
      }
    } catch (err) {
      const isQuota = err.message?.includes('429') || err.message?.includes('quota') || err.message?.includes('billing');
      const isNetwork = err.message?.includes('fetch') || err.message?.includes('network') || err.message?.includes('Failed to fetch');
      const errorPayload = {
        role: 'error',
        errorType: isQuota ? 'quota' : isNetwork ? 'network' : 'general',
        errorMsg: isQuota
          ? 'AI service quota exceeded. Please check your OpenAI billing or contact your administrator.'
          : isNetwork
            ? 'Network connection failed. Please check if the backend server is running.'
            : 'Something went wrong while generating a response. Please try again.'
      };
      setMessages(prev => {
        const u = [...prev];
        const last = u[u.length - 1];
        if (last?.role === 'assistant') { u[u.length - 1] = errorPayload; }
        else { u.push(errorPayload); }
        return u;
      });
    } finally {
      setLoading(false);
      fetchSessions();
    }
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    try {
      await api.delete(`/chat/sessions/${sid}`);
      setSessions(prev => prev.filter(s => s.id !== sid));
      if (currentSession === sid) handleNewChat();
    } catch (e) { console.error(e); }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        :root {
          --chat-bg: #f8fafc;
          --sidebar-bg: #0f172a;
          --accent-primary: #6366f1;
          --accent-secondary: #8b5cf6;
          --text-primary: #1e293b;
          --text-muted: #64748b;
          --border-color: #e2e8f0;
          --radius-common: 20px;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Plus Jakarta Sans', sans-serif; background: var(--chat-bg); }

        .app-container { display: flex; height: 100vh; overflow: hidden; }

        /* ── SIDEBAR ── */
        .sidebar {
          width: 300px; min-width: 300px;
          background: var(--sidebar-bg);
          display: flex; flex-direction: column;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          z-index: 50;
        }
        @media (max-width: 768px) {
          .sidebar { position: fixed; left: -300px; height: 100%; box-shadow: 20px 0 50px rgba(0,0,0,0.5); }
          .sidebar.visible { left: 0; }
        }

        .sidebar-header {
          padding: 24px; border-bottom: 1px solid rgba(255,255,255,0.05);
          display: flex; align-items: center; gap: 12px;
        }
        .logo-box {
          width: 40px; height: 40px; border-radius: 12px;
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          display: flex; align-items: center; justify-content: center;
          box-shadow: 0 8px 16px rgba(99, 102, 241, 0.3);
        }
        .logo-text h2 { color: #fff; font-size: 14px; font-weight: 800; tracking: -0.01em; }
        .logo-text p { color: rgba(255,255,255,0.4); font-size: 10px; font-bold tracking-widest uppercase; margin-top: 2px; }

        .new-chat-btn {
          margin: 20px; padding: 12px;
          background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
          border-radius: 14px; color: #fff; font-size: 13px; font-weight: 600;
          display: flex; align-items: center; justify-content: center; gap: 8px;
          cursor: pointer; transition: all 0.2s;
        }
        .new-chat-btn:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.15); }

        .sessions-list { flex: 1; overflow-y: auto; padding: 0 12px 20px; }
        .sessions-list::-webkit-scrollbar { width: 4px; }
        .sessions-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

        .session-item {
          width: 100%; display: flex; align-items: center; gap: 10px;
          padding: 10px 14px; border-radius: 12px; border: none;
          background: transparent; color: rgba(255,255,255,0.5);
          font-size: 13px; font-weight: 500; text-align: left;
          cursor: pointer; transition: all 0.2s; margin-bottom: 4px;
        }
        .session-item:hover { background: rgba(255,255,255,0.04); color: #fff; }
        .session-item.active { background: rgba(99, 102, 241, 0.15); color: #a5b4fc; }
        .session-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

        .sidebar-footer { padding: 20px; border-top: 1px solid rgba(255,255,255,0.05); }
        .user-pill {
          display: flex; align-items: center; gap: 10px; padding: 10px;
          background: rgba(255,255,255,0.03); border-radius: 14px; margin-bottom: 12px;
        }
        .user-pill img { width: 32px; height: 32px; border-radius: 10px; }
        .user-meta { flex: 1; overflow: hidden; }
        .user-meta h4 { color: #fff; font-size: 12px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .user-meta p { color: rgba(255,255,255,0.4); font-size: 10px; }

        .footer-action {
          width: 100%; display: flex; align-items: center; gap: 10px;
          padding: 10px; color: rgba(255,255,255,0.5); font-size: 12px;
          border-radius: 10px; transition: all 0.2s; cursor: pointer; border: none; background: transparent;
        }
        .footer-action:hover { background: rgba(255,255,255,0.05); color: #fff; }
        .footer-action.danger:hover { background: rgba(239, 68, 68, 0.1); color: #fca5a5; }

        /* ── MAIN CONTENT ── */
        .main-content { flex: 1; display: flex; flex-direction: column; background: #fdfdff; position: relative; }

        /* TOPBAR */
        .header {
          height: 70px; display: flex; align-items: center; justify-content: space-between;
          padding: 0 24px; border-bottom: 1px solid var(--border-color); background: #fff;
        }
        .header-left { display: flex; align-items: center; gap: 16px; }
        .menu-toggle {
          width: 40px; height: 40px; border-radius: 12px;
          display: flex; align-items: center; justify-content: center;
          background: #f1f5f9; border: none; color: var(--text-muted); cursor: pointer;
        }
        .system-status { display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px rgba(16,185,129,0.5); }
        .status-text h3 { font-size: 14px; font-weight: 700; color: var(--text-primary); }
        .status-text p { font-size: 10px; color: var(--text-muted); font-weight: 600; }

        /* MESSAGES AREA */
        .chat-area { flex: 1; overflow-y: auto; padding: 40px 24px; scroll-behavior: smooth; }
        .chat-area::-webkit-scrollbar { width: 5px; }
        .chat-area::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }

        .welcome-view { max-width: 800px; margin: 0 auto; text-align: center; padding: 40px 0; }
        .welcome-hero { margin-bottom: 48px; }
        .welcome-icon {
          width: 80px; height: 80px; border-radius: 24px; margin: 0 auto 24px;
          display: flex; align-items: center; justify-content: center; color: #fff;
          box-shadow: 0 20px 40px rgba(99, 102, 241, 0.2);
        }
        .welcome-view h1 { font-size: 32px; font-weight: 800; color: #0f172a; margin-bottom: 12px; tracking: -0.02em; }
        .welcome-view p { font-size: 16px; color: #64748b; line-height: 1.6; max-width: 600px; margin: 0 auto; }

        .suggestions-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; margin-top: 40px; }
        .suggestion-card {
          background: #fff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 20px;
          display: flex; align-items: flex-start; gap: 16px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          cursor: pointer; text-align: left;
        }
        .suggestion-card:hover { border-color: var(--accent-primary); box-shadow: 0 10px 30px rgba(99, 102, 241, 0.08); transform: translateY(-3px); }
        .suggestion-icon {
          width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center;
          flex-shrink: 0; background: rgba(99, 102, 241, 0.05); color: var(--accent-primary);
        }
        .suggestion-card:hover .suggestion-icon { background: var(--accent-primary); color: #fff; }
        .suggestion-card h4 { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
        .suggestion-card p { font-size: 12px; color: #64748b; line-height: 1.5; }

        /* MESSAGE BUBBLES */
        .message-list { max-width: 850px; margin: 0 auto; display: flex; flex-direction: column; gap: 32px; }
        .msg-row { display: flex; gap: 20px; }
        .msg-row.user-msg { flex-direction: row-reverse; }

        .avatar-box { width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .avatar-box.ai { background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); color: #fff; box-shadow: 0 4px 10px rgba(99, 102, 241, 0.2); }
        .avatar-box.user { background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; }

        .bubble-wrap { max-width: 80%; }
        .msg-info { font-size: 11px; font-weight: 700; color: #94a3b8; margin-bottom: 8px; text-transform: uppercase; tracking: 0.05em; }
        .user-msg .msg-info { text-align: right; }

        .bubble {
          padding: 16px 20px; border-radius: 20px; font-size: 15px; line-height: 1.6; position: relative;
        }
        .assistant-bubble { background: #fff; color: #1e293b; border: 1px solid #edf2f7; border-bottom-left-radius: 4px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); }
        .user-bubble { background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); color: #fff; border-bottom-right-radius: 4px; box-shadow: 0 10px 25px rgba(99, 102, 241, 0.2); }

        /* SOURCES SECTION */
        .sources-area {
            margin-top: 16px; padding-top: 16px; border-top: 1px solid #f1f5f9;
        }
        .sources-label { display: flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 800; color: #a1a1aa; text-transform: uppercase; margin-bottom: 10px; }
        .source-chip {
            display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px;
            background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
            font-size: 12px; font-weight: 600; color: #475569; margin-right: 8px; margin-bottom: 8px;
            cursor: pointer; transition: all 0.2s;
        }
        .source-chip:hover { border-color: var(--accent-primary); background: #f5f3ff; color: var(--accent-primary); }

        /* INPUT AREA */
        .input-view { padding: 24px 24px 32px; background: #fff; border-top: 1px solid var(--border-color); z-index: 10; }
        .input-container { max-width: 850px; margin: 0 auto; position: relative; }
        .input-box {
          display: flex; align-items: flex-end; gap: 12px; padding: 12px 16px;
          background: #f8fafc; border: 2px solid #f1f5f9; border-radius: 24px;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .input-box:focus-within { border-color: var(--accent-primary); background: #fff; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.1); }
        
        .text-area {
          flex: 1; border: none; background: transparent; outline: none; padding: 8px 0;
          font-family: inherit; font-size: 15px; color: #1e293b; resize: none;
          max-height: 200px;
        }
        .send-btn {
          width: 44px; height: 44px; border-radius: 14px; border: none;
          display: flex; align-items: center; justify-content: center;
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          color: #fff; cursor: pointer; transition: all 0.2s;
        }
        .send-btn:disabled { background: #e2e8f0; cursor: not-allowed; }
        .send-btn:not(:disabled):hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(99, 102, 241, 0.4); }

        .input-footer { text-align: center; margin-top: 12px; font-size: 11px; color: #94a3b8; font-weight: 500; }

        /* ANIMATIONS */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .msg-row { animation: fadeIn 0.4s ease-out backwards; }

        .chat-typing { display: flex; gap: 4px; padding: 12px 16px; background: #f8fafc; border-radius: 16px; width: fit-content; }
        .chat-typing span { width: 6px; height: 6px; border-radius: 50%; background: var(--accent-primary); opacity: 0.4; animation: blink 1.4s infinite both; }
        .chat-typing span:nth-child(2) { animation-delay: 0.2s; }
        .chat-typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.4; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1.2); } }

        /* PROSE OVERRIDES */
        .prose pre { background: #0f172a; border-radius: 12px; padding: 16px; color: #e2e8f0; margin: 12px 0; }
        .prose code { background: #f1f5f9; color: #6366f1; padding: 2px 4px; border-radius: 4px; font-size: 0.9em; }
        .prose blockquote { border-left: 4px solid var(--accent-primary); padding-left: 16px; color: var(--text-muted); font-style: italic; }

      `}</style>

      <div className="app-container">
        {/* ── SIDEBAR ── */}
        <aside className={`sidebar ${sidebarVisible ? 'visible' : ''}`}>
          <div className="sidebar-header">
            <div className="logo-box">
              <Shield size={20} color="#fff" />
            </div>
            <div className="logo-text">
              <h2>Enterprise RAG</h2>
              <p>Intelligence Pipeline</p>
            </div>
          </div>

          <button className="new-chat-btn" onClick={handleNewChat}>
            <Plus size={16} />
            New Analysis
          </button>

          <div className="sessions-list">
            {sessions.map(s => (
              <button
                key={s.id}
                className={`session-item ${currentSession === s.id ? 'active' : ''}`}
                onClick={() => loadSession(s.id)}
              >
                <div className="session-title">{s.title}</div>
                <div onClick={(e) => deleteSession(s.id, e)}>
                  <Trash2 size={12} className="hover:text-red-400 opacity-40 hover:opacity-100 transition-all" />
                </div>
              </button>
            ))}
          </div>

          <div className="sidebar-footer">
            <div className="user-pill">
              <img
                src={user?.profile_photo || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.full_name || user?.username || 'U')}&background=6366f1&size=64`}
                alt="u"
              />
              <div className="user-meta">
                <h4>{user?.full_name || user?.username}</h4>
                <p>{roleLabel}</p>
              </div>
            </div>

            <button className="footer-action" onClick={() => setShowProfileModal(true)}>
              <User size={14} /> Account Settings
            </button>
            {isAdmin() && (
              <button className="footer-action" onClick={() => navigate('/dashboard')}>
                <LayoutDashboard size={14} /> Infrastructure Hub
              </button>
            )}
            <button className="footer-action danger" onClick={handleLogout}>
              <LogOut size={14} /> Terminate Session
            </button>
          </div>
        </aside>

        {/* ── MAIN CONTENT ── */}
        <main className="main-content">
          <header className="header">
            <div className="header-left">
              {isMobile && (
                <button className="menu-toggle" onClick={() => setSidebarVisible(!sidebarVisible)}>
                  <Menu size={20} />
                </button>
              )}
              <div className="system-status">
                <div className="status-dot" />
                <div className="status-text">
                  <h3>{roleInfo.title}</h3>
                  <p>Secured · Neural Ingress Active</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-slate-50 border border-slate-100 rounded-lg text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                <Database size={12} />
                Cluster: US-East-1
              </div>
            </div>
          </header>

          <div className="chat-area">
            {messages.length === 0 ? (
              <div className="welcome-view">
                <div className="welcome-hero">
                  <div className="welcome-icon" style={{ background: `linear-gradient(135deg, ${roleInfo.gradientFrom}, ${roleInfo.gradientTo})` }}>
                    <Sparkles size={32} />
                  </div>
                  <h1>Intelligence Interface</h1>
                  <p>{roleInfo.description}</p>
                </div>

                <div className="suggestions-grid">
                  {roleInfo.suggestions.map((item, i) => (
                    <div key={i} className="suggestion-card" onClick={() => handleSubmit(null, item.label)}>
                      <div className="suggestion-icon">
                        <item.Icon size={20} />
                      </div>
                      <div>
                        <h4>{item.label}</h4>
                        <p>{item.desc}</p>
                      </div>
                      <ChevronRight size={14} className="ml-auto opacity-20" />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="message-list">
                {messages.map((msg, i) => {
                  if (msg.role === 'error') {
                    return (
                      <div key={i} className="msg-row assistant-msg">
                        <div className="avatar-box ai" style={{ background: '#e72525ff' }}><Bot size={18} /></div>
                        <div className="bubble-wrap">
                          <div className="msg-info">System Error</div>
                          <div className="bubble assistant-bubble border-red-100 bg-red-50/30">
                            <div className="flex items-start gap-3">
                              <AlertTriangle size={18} className="text-red-500 mt-1" />
                              <div>
                                <div className="font-bold text-red-700 text-sm mb-1">{msg.errorType?.toUpperCase()} EXCEPTION</div>
                                <div className="text-sm text-red-600/80">{msg.errorMsg}</div>
                                <button
                                  className="mt-4 px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-xl text-xs font-bold transition-all border border-red-200 flex items-center gap-2"
                                  onClick={() => { setMessages(prev => prev.slice(0, i)); textareaRef.current?.focus(); }}
                                >
                                  <RefreshCw size={12} /> Re-initiate Analysis
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div key={i} className={`msg-row ${msg.role === 'user' ? 'user-msg' : 'assistant-msg'}`}>
                      <div className={`avatar-box ${msg.role === 'user' ? 'user' : 'ai'}`}>
                        {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                      </div>
                      <div className="bubble-wrap">
                        <div className="msg-info">
                          {msg.role === 'user' ? (user?.full_name || 'Authorized User') : 'Neural Response'}
                        </div>
                        <div className={`bubble ${msg.role === 'user' ? 'user-bubble' : 'assistant-bubble'}`}>
                          {msg.role === 'user' ? (
                            <div className="whitespace-pre-wrap">{msg.content}</div>
                          ) : (
                            <>
                              {msg.thinking ? (
                                <TypingIndicator color={roleInfo.accentColor} />
                              ) : (
                                <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-sm prose-slate max-w-none">
                                  {msg.content || '▌'}
                                </ReactMarkdown>
                              )}

                              {msg.sources && msg.sources.length > 0 && !msg.thinking && (
                                <div className="sources-area">
                                  <div className="sources-label">
                                    <Search size={10} />
                                    Knowledge Sources
                                  </div>
                                  <div className="flex flex-wrap">
                                    {msg.sources.map((src, idx) => (
                                      <div key={idx} className="source-chip" title={`Chunk ${src.chunk_index}`}>
                                        <FileText size={12} className="text-indigo-400" />
                                        <span>{src.filename}</span>
                                        <ExternalLink size={10} className="ml-1 opacity-40" />
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {loading && messages[messages.length - 1]?.role !== 'assistant' && (
                  <div className="msg-row assistant-msg">
                    <div className="avatar-box ai"><Bot size={18} /></div>
                    <div className="bubble-wrap">
                      <div className="msg-info">Scanning Knowledge Base...</div>
                      <TypingIndicator color={roleInfo.accentColor} />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <div className="input-view">
            <form className="input-container" onSubmit={handleSubmit}>
              <div className="input-box">
                <textarea
                  ref={textareaRef}
                  className="text-area"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
                  }}
                  placeholder={roleInfo.placeholder}
                  rows={1}
                />
                <button type="submit" disabled={loading || !input.trim()} className="send-btn shadow-lg">
                  {loading
                    ? <RefreshCw size={18} className="animate-spin" />
                    : <ArrowRight size={20} />
                  }
                </button>
              </div>
              <div className="input-footer">
                Secured Pipeline · RAG Engine v2.4 · <kbd className="px-1.5 py-0.5 bg-slate-100 rounded text-[9px] uppercase font-bold text-slate-400 border border-slate-200">Shift + Enter</kbd> for new line
              </div>
            </form>
          </div>
        </main>

        {showProfileModal && (
          <ProfileModal
            isOpen={showProfileModal}
            onClose={() => setShowProfileModal(false)}
            user={user}
            onUpdate={(updated) => {
              setUser(updated);
              localStorage.setItem('user', JSON.stringify(updated));
            }}
          />
        )}
      </div>
    </>
  );
}
