import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, FileText, MessageSquare,
  UserPlus, Upload, Trash2, LogOut, Shield,
  RefreshCw, ChevronRight, Sparkles,
  Database, CheckCircle, AlertCircle, Activity
} from 'lucide-react';
import { usersAPI, documentsAPI, chatAPI } from '../services/api';
import { getUser, logout } from '../utils/auth';

function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ users: 0, documents: 0, sessions: 0 });
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  const user = getUser();

  useEffect(() => {
    if (!user) { navigate('/login'); return; }
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [usersList, docsList, sessionsList] = await Promise.all([
        usersAPI.list(),
        documentsAPI.list(),
        chatAPI.getSessions(),
      ]);
      setStats({ users: usersList.length, documents: docsList.length, sessions: sessionsList.length });
      setDocuments(docsList);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      await documentsAPI.upload(file);
      await loadAllData();
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteDocument = async (id) => {
    if (!window.confirm('Delete this document from the knowledge base?')) return;
    try {
      await documentsAPI.delete(id);
      await loadAllData();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  if (!user) return null;

  const statCards = [
    { label: 'System Users', value: stats.users, icon: Users, color: 'text-indigo-600', bg: 'bg-indigo-50', link: '/admin/users' },
    { label: 'Documents', value: stats.documents, icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-50', link: null },
    { label: 'Chat Sessions', value: stats.sessions, icon: MessageSquare, color: 'text-blue-600', bg: 'bg-blue-50', link: '/chat' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 font-['Outfit',sans-serif]">

      {/* ── HEADER ── */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Shield size={18} className="text-white" />
            </div>
            <div>
              <div className="font-bold text-slate-800 text-sm leading-none">Admin Panel</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-xs text-slate-400">Full Access</span>
              </div>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-1">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 text-sm font-medium text-slate-500 hover:text-slate-800 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Dashboard
            </button>
            <button
              onClick={() => navigate('/chat')}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
            >
              <Sparkles size={14} />
              AI Chat
            </button>
            <button
              onClick={() => navigate('/admin/users')}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-500 hover:text-slate-800 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <UserPlus size={14} />
              Users
            </button>
          </nav>

          <div className="flex items-center gap-3">
            <div className="hidden md:block text-right">
              <div className="text-sm font-semibold text-slate-800 leading-none">{user.full_name || user.username}</div>
              <div className="text-xs text-indigo-500 font-medium mt-0.5">Administrator</div>
            </div>
            <button
              onClick={logout}
              className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="Sign out"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* ── MAIN ── */}
      <main className="max-w-7xl mx-auto px-6 py-8">

        {/* Page title */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">System Governance</h1>
          <p className="text-slate-500 text-sm mt-1">Manage users, documents, and AI knowledge base.</p>
        </div>

        {/* ── STAT CARDS ── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
          {statCards.map((card, i) => (
            <div
              key={i}
              onClick={() => card.link && navigate(card.link)}
              className={`bg-white rounded-2xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-all ${card.link ? 'cursor-pointer' : ''}`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-10 h-10 ${card.bg} ${card.color} rounded-xl flex items-center justify-center`}>
                  <card.icon size={20} />
                </div>
                {card.link && <ChevronRight size={16} className="text-gray-300" />}
              </div>
              <div className="text-3xl font-bold text-slate-800 mb-1">
                {loading ? <span className="text-gray-200 animate-pulse">—</span> : card.value}
              </div>
              <div className="text-sm text-slate-500 font-medium">{card.label}</div>
            </div>
          ))}
        </div>

        {/* ── CONTENT GRID ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Documents Table (2/3) */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h2 className="font-bold text-slate-800">Knowledge Vault</h2>
                <p className="text-xs text-slate-400 mt-0.5">{documents.length} document{documents.length !== 1 ? 's' : ''} stored</p>
              </div>
              <button
                onClick={loadAllData}
                className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                title="Refresh"
              >
                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Document</th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                    <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {loading ? (
                    [1, 2, 3].map(n => (
                      <tr key={n}>
                        <td colSpan="4" className="px-6 py-4">
                          <div className="h-4 bg-gray-100 rounded animate-pulse w-2/3" />
                        </td>
                      </tr>
                    ))
                  ) : documents.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-6 py-16 text-center">
                        <Database size={32} className="text-gray-200 mx-auto mb-3" />
                        <p className="text-slate-400 text-sm font-medium">No documents in vault</p>
                        <p className="text-slate-300 text-xs mt-1">Upload documents to build the knowledge base</p>
                      </td>
                    </tr>
                  ) : (
                    documents.map(doc => (
                      <tr key={doc.id} className="hover:bg-gray-50 transition-colors group">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-blue-50 text-blue-500 rounded-lg flex items-center justify-center shrink-0">
                              <FileText size={14} />
                            </div>
                            <div>
                              <div className="text-sm font-medium text-slate-700 truncate max-w-[200px]">
                                {doc.original_filename}
                              </div>
                              <div className="text-xs text-slate-400">ID: {doc.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4 text-xs text-slate-400 uppercase font-medium">
                          {doc.file_type || '—'}
                        </td>
                        <td className="px-4 py-4">
                          {doc.status === 'processed' ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-semibold rounded-full">
                              <CheckCircle size={10} />
                              Ready
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 text-amber-700 text-xs font-semibold rounded-full">
                              <AlertCircle size={10} />
                              Processing
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-4 text-right">
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* ── RIGHT SIDEBAR ── */}
          <div className="space-y-5">

            {/* Upload */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center">
                  <Upload size={17} />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-sm">Upload Document</h3>
                  <p className="text-xs text-slate-400">PDF, DOCX, TXT</p>
                </div>
              </div>

              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-200 hover:border-indigo-400 hover:bg-indigo-50/30 rounded-xl p-6 text-center cursor-pointer transition-all group"
              >
                <Database size={24} className="text-gray-300 group-hover:text-indigo-400 mx-auto mb-2 transition-colors" />
                <p className="text-sm text-slate-400 font-medium">Click to upload file</p>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                accept=".pdf,.txt,.doc,.docx"
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="w-full mt-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-200 text-white disabled:text-gray-400 rounded-xl text-sm font-semibold transition-colors"
              >
                {uploading ? 'Uploading...' : 'Choose File'}
              </button>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <h3 className="font-bold text-slate-800 text-sm mb-4">Admin Actions</h3>
              <div className="space-y-2">
                <button
                  onClick={() => navigate('/admin/users')}
                  className="w-full flex items-center gap-3 px-4 py-3 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-sm font-semibold transition-colors"
                >
                  <UserPlus size={16} />
                  Manage Users
                  <ChevronRight size={14} className="ml-auto" />
                </button>
                <button
                  onClick={() => navigate('/chat')}
                  className="w-full flex items-center gap-3 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold transition-colors"
                >
                  <Sparkles size={16} />
                  AI Chat Interface
                  <ChevronRight size={14} className="ml-auto" />
                </button>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="w-full flex items-center gap-3 px-4 py-3 bg-gray-100 hover:bg-gray-200 text-slate-700 rounded-xl text-sm font-semibold transition-colors"
                >
                  <Activity size={16} />
                  Main Dashboard
                  <ChevronRight size={14} className="ml-auto" />
                </button>
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}

export default AdminDashboard;