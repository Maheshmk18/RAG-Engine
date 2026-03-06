import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Users, FileText, MessageSquare,
    Upload, Trash2, LogOut, Shield, Plus,
    RefreshCw, ChevronRight, Sparkles,
    Database, CheckCircle, AlertCircle, Settings,
    ArrowRight
} from 'lucide-react';
import { usersAPI, documentsAPI, chatAPI } from '../services/api';
import { getUser, logout, isAdmin } from '../utils/auth';
import ProfileModal from '../components/ProfileModal';

const ROLE_DISPLAY = {
    admin: { label: 'System Administrator', color: 'text-indigo-600', bg: 'bg-indigo-50' },
    hr: { label: 'HR Operations', color: 'text-sky-600', bg: 'bg-sky-50' },
    manager: { label: 'Department Manager', color: 'text-teal-700', bg: 'bg-teal-50' },
    employee: { label: 'Associate Staff', color: 'text-slate-600', bg: 'bg-slate-50' }
};

export function DashboardPage() {
    const navigate = useNavigate();
    const [stats, setStats] = useState({ users: 0, documents: 0, sessions: 0, totalChunks: 0, storageUsed: '0 MB' });
    const [loading, setLoading] = useState(true);
    const [documents, setDocuments] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const fileInputRef = useRef(null);
    const [user, setUser] = useState(getUser());

    useEffect(() => {
        if (!user) { navigate('/login'); return; }
        if (!isAdmin()) { navigate('/chat'); return; }
        loadAllData();
    }, []);

    useEffect(() => {
        const hasProcessing = documents.some(doc => doc.status === 'processing');
        let interval;
        if (hasProcessing) {
            interval = setInterval(() => {
                refreshDocumentStatus();
            }, 3000);
        }
        return () => clearInterval(interval);
    }, [documents]);

    const formatSize = (bytes) => {
        if (!bytes || bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const refreshDocumentStatus = async () => {
        try {
            const docsList = await documentsAPI.list();
            setDocuments(docsList);
            const chunks = docsList.reduce((acc, doc) => acc + (doc.chunk_count || 0), 0);
            const storage = docsList.reduce((acc, doc) => acc + (doc.file_size || 0), 0);
            setStats(prev => ({
                ...prev,
                documents: docsList.length,
                totalChunks: chunks,
                storageUsed: formatSize(storage)
            }));
        } catch (err) {
            console.error('Polling failed:', err);
        }
    };

    const loadAllData = async () => {
        setLoading(true);
        try {
            const [usersList, docsList, sessionsList] = await Promise.all([
                usersAPI.list(),
                documentsAPI.list(),
                chatAPI.getSessions(),
            ]);
            const chunks = docsList.reduce((acc, doc) => acc + (doc.chunk_count || 0), 0);
            const storage = docsList.reduce((acc, doc) => acc + (doc.file_size || 0), 0);

            setStats({
                users: usersList.length,
                documents: docsList.length,
                sessions: sessionsList.length,
                totalChunks: chunks,
                storageUsed: formatSize(storage)
            });
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
    const roleInfo = ROLE_DISPLAY[user.role] || ROLE_DISPLAY.employee;

    const statCards = [
        { label: 'Platform Users', value: stats.users, icon: Users, color: 'text-indigo-600', bg: 'bg-indigo-50', sub: 'Authorized access' },
        { label: 'Knowledge Base', value: stats.documents, icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-50', sub: 'Indexed documents' },
        { label: 'Neural Chunks', value: stats.totalChunks, icon: Database, color: 'text-blue-600', bg: 'bg-blue-50', sub: 'Vectorized segments' },
        { label: 'Storage Volume', value: stats.storageUsed, icon: Shield, color: 'text-purple-600', bg: 'bg-purple-50', sub: 'Occupied space' },
    ];

    return (
        <div className="min-h-screen bg-[#fcfdfe] font-['Outfit',sans-serif]">

            {/* ── TOP NAVBAR ── */}
            <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-18 flex items-center justify-between">
                    {/* Brand */}
                    <div className="flex items-center gap-4 py-4">
                        <div className="w-10 h-10 bg-gradient-to-tr from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
                            <Shield size={20} className="text-white" />
                        </div>
                        <div>
                            <div className="font-extrabold text-[#111827] text-base tracking-tight leading-none">Enterprise RAG</div>
                            <div className="text-slate-400 text-[10px] uppercase font-bold tracking-widest mt-1">Industrial Intelligence Platform</div>
                        </div>
                    </div>

                    {/* Nav links */}
                    <nav className="hidden md:flex items-center gap-2">
                        <button
                            onClick={() => navigate('/chat')}
                            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-600 hover:text-indigo-600 hover:bg-indigo-50/50 rounded-xl transition-all"
                        >
                            <Sparkles size={16} />
                            AI Interface
                        </button>
                        <button
                            onClick={loadAllData}
                            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold text-slate-600 hover:text-indigo-600 hover:bg-indigo-50/50 rounded-xl transition-all ${loading ? 'opacity-50' : ''}`}
                        >
                            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                            Sync Node
                        </button>
                    </nav>

                    {/* User Profile */}
                    <div className="relative">
                        <button
                            onClick={() => setShowProfileMenu(!showProfileMenu)}
                            className="flex items-center gap-3 p-1.5 pr-4 bg-slate-50 border border-slate-100 rounded-2xl hover:bg-white hover:shadow-md transition-all active:scale-95"
                        >
                            <img
                                src={user?.profile_photo || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.full_name || user?.username || 'User')}&background=4f46e5&color=fff&size=64`}
                                alt="Profile"
                                className="w-8 h-8 rounded-xl object-cover shadow-sm"
                            />
                            <div className="hidden md:block text-left">
                                <div className="text-xs font-bold text-slate-800 leading-none">{user?.full_name || user?.username}</div>
                                <div className={`text-[10px] mt-1 font-bold uppercase tracking-tighter ${roleInfo.color}`}>{roleInfo.label}</div>
                            </div>
                        </button>

                        {showProfileMenu && (
                            <div className="absolute right-0 top-full mt-3 w-56 bg-white border border-gray-100 rounded-2xl shadow-2xl p-2 z-50 ring-1 ring-black/5">
                                <div className="px-3 py-2 mb-1">
                                    <div className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">Account</div>
                                </div>
                                <button
                                    onClick={() => { setShowProfileModal(true); setShowProfileMenu(false); }}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-700 hover:bg-indigo-50/50 hover:text-indigo-600 rounded-xl transition-all"
                                >
                                    <Shield size={16} className="text-slate-400" />
                                    Security Profile
                                </button>
                                {isAdmin() && (
                                    <button
                                        onClick={() => { navigate('/admin/users'); setShowProfileMenu(false); }}
                                        className="w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-slate-700 hover:bg-indigo-50/50 hover:text-indigo-600 rounded-xl transition-all"
                                    >
                                        <Settings size={16} className="text-slate-400" />
                                        User Management
                                    </button>
                                )}
                                <div className="h-px bg-slate-50 my-1" />
                                <button
                                    onClick={logout}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-xl transition-all"
                                >
                                    <LogOut size={16} />
                                    Terminate Session
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            {/* ── MAIN CONTENT ── */}
            <main className="max-w-7xl mx-auto px-6 py-10">

                {/* Page Hero */}
                <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-50 border border-indigo-100 rounded-full text-[10px] font-bold text-indigo-600 uppercase tracking-widest mb-3">
                            <span className="w-1.5 h-1.5 bg-indigo-600 rounded-full animate-pulse" />
                            Active Environment
                        </div>
                        <h1 className="text-3xl font-black text-slate-900 tracking-tight">System Infrastructure</h1>
                        <p className="text-slate-500 text-sm mt-2 max-w-xl">Enterprise-grade RAG management. Monitor knowledge base health, vectorize documents, and manage authorized neural access.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="px-5 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-bold shadow-lg shadow-slate-200 hover:bg-slate-800 transition-all flex items-center gap-2"
                        >
                            <Upload size={16} />
                            Ingest Data
                        </button>
                    </div>
                </div>

                {/* ── STAT CARDS ── */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                    {statCards.map((card, i) => (
                        <div
                            key={i}
                            className="group bg-white rounded-3xl border border-gray-100 p-6 shadow-sm hover:shadow-xl hover:shadow-indigo-50/50 transition-all duration-300"
                        >
                            <div className="flex items-center justify-between mb-5">
                                <div className={`w-12 h-12 ${card.bg} ${card.color} rounded-2xl flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform duration-300`}>
                                    <card.icon size={22} />
                                </div>
                                <div className="text-[10px] font-bold text-slate-300 group-hover:text-indigo-200 transition-colors uppercase tracking-widest">Global</div>
                            </div>
                            <div className="text-3xl font-black text-slate-900 mb-1.5 tracking-tighter">
                                {loading ? <span className="inline-block w-20 h-8 bg-slate-50 rounded animate-pulse" /> : card.value}
                            </div>
                            <div className="text-xs font-bold text-slate-500 uppercase tracking-tighter">{card.label}</div>
                            <div className="text-[10px] text-slate-400 mt-1 font-medium italic">{card.sub}</div>
                        </div>
                    ))}
                </div>

                {/* ── CENTRAL HUB ── */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Knowledge Base Table */}
                    <div className="lg:col-span-8 space-y-6">
                        <div className="bg-white rounded-[2rem] border border-gray-100 shadow-sm overflow-hidden border-b-4 border-b-indigo-500/10">
                            <div className="px-8 py-6 border-b border-gray-50 flex items-center justify-between bg-gradient-to-r from-white to-slate-50/30">
                                <div>
                                    <h2 className="text-lg font-black text-slate-900">Knowledge Repository</h2>
                                    <div className="flex items-center gap-2 mt-1">
                                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">
                                            {documents.length} Neural Nodes Active
                                        </span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="relative">
                                        <input
                                            type="text"
                                            placeholder="Query repository..."
                                            className="px-4 py-2 bg-slate-50 border-none rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-100 w-48 transition-all"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="bg-slate-50/50 border-b border-gray-50">
                                            <th className="text-left px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Resource Identifier</th>
                                            <th className="text-left px-4 py-4 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Chunks</th>
                                            <th className="text-left px-4 py-4 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Sync Status</th>
                                            <th className="px-8 py-4"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50/50">
                                        {loading ? (
                                            [1, 2, 3, 4, 5].map(n => (
                                                <tr key={n}>
                                                    <td className="px-8 py-6">
                                                        <div className="flex items-center gap-4">
                                                            <div className="w-10 h-10 bg-slate-50 rounded-xl animate-pulse" />
                                                            <div className="space-y-2">
                                                                <div className="h-3 bg-slate-50 rounded animate-pulse w-48" />
                                                                <div className="h-2 bg-slate-50 rounded animate-pulse w-24" />
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td colSpan="3"></td>
                                                </tr>
                                            ))
                                        ) : documents.length === 0 ? (
                                            <tr>
                                                <td colSpan="4" className="px-8 py-24 text-center">
                                                    <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
                                                        <Database size={32} className="text-slate-200" />
                                                    </div>
                                                    <h3 className="text-base font-black text-slate-800">No Intelligence Ingested</h3>
                                                    <p className="text-slate-400 text-sm mt-2 max-w-xs mx-auto">Your knowledge repository is currently empty. Ingest corporate data to train the RAG neural engine.</p>
                                                    <button
                                                        onClick={() => fileInputRef.current?.click()}
                                                        className="mt-6 px-6 py-2.5 bg-indigo-50 text-indigo-600 rounded-xl text-xs font-bold hover:bg-indigo-100 transition-all border border-indigo-100"
                                                    >
                                                        Initiate Ingestion
                                                    </button>
                                                </td>
                                            </tr>
                                        ) : (
                                            documents.map(doc => (
                                                <tr key={doc.id} className="hover:bg-indigo-50/30 transition-all group cursor-default">
                                                    <td className="px-8 py-6">
                                                        <div className="flex items-center gap-4">
                                                            <div className={`w-12 h-12 ${doc.status === 'processed' ? 'bg-indigo-50 text-indigo-600' : doc.status === 'failed' ? 'bg-red-50 text-red-600' : 'bg-slate-50 text-slate-400'} rounded-2xl flex items-center justify-center shrink-0 shadow-sm border border-white group-hover:scale-105 transition-transform`}>
                                                                <FileText size={20} />
                                                            </div>
                                                            <div className="min-w-0">
                                                                <div className="text-sm font-bold text-slate-800 truncate max-w-[300px] group-hover:text-indigo-600 transition-colors">
                                                                    {doc.original_filename}
                                                                </div>
                                                                <div className="flex items-center gap-2 mt-1">
                                                                    <span className="text-[10px] font-bold text-slate-400 uppercase">{doc.file_type || 'binary'}</span>
                                                                    <span className="text-slate-200 text-[8px]">•</span>
                                                                    <span className="text-[10px] font-semibold text-slate-400">{formatSize(doc.file_size)}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-6">
                                                        <div className="text-sm font-black text-slate-700">{doc.chunk_count || 0}</div>
                                                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter mt-1">Vectors</div>
                                                    </td>
                                                    <td className="px-4 py-6">
                                                        {doc.status === 'processed' ? (
                                                            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-emerald-50 text-emerald-700 text-[10px] font-black uppercase rounded-lg border border-emerald-100">
                                                                <CheckCircle size={12} />
                                                                Synced
                                                            </div>
                                                        ) : doc.status === 'failed' ? (
                                                            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-red-50 text-red-700 text-[10px] font-black uppercase rounded-lg border border-red-100">
                                                                <AlertCircle size={12} />
                                                                Corrupt
                                                            </div>
                                                        ) : (
                                                            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-amber-50 text-amber-700 text-[10px] font-black uppercase rounded-lg border border-amber-100">
                                                                <RefreshCw size={12} className="animate-spin" />
                                                                Vectorizing
                                                            </div>
                                                        )}
                                                    </td>
                                                    <td className="px-8 py-6 text-right">
                                                        <button
                                                            onClick={() => handleDeleteDocument(doc.id)}
                                                            className="opacity-0 group-hover:opacity-100 p-2.5 text-slate-300 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Processing Log / Recent Activity */}
                        <div className="bg-slate-900 rounded-[2rem] p-8 text-white relative overflow-hidden shadow-2xl shadow-indigo-200 mt-8">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600 opacity-10 rounded-full blur-3xl -mr-20 -mt-20" />
                            <div className="relative z-10">
                                <div className="flex items-center justify-between mb-8">
                                    <div>
                                        <h3 className="text-lg font-black tracking-tight">System Telemetry</h3>
                                        <p className="text-slate-400 text-xs mt-1">Real-time infrastructure logs and neural activity.</p>
                                    </div>
                                    <div className="px-3 py-1 bg-white/10 rounded-full text-[10px] font-bold border border-white/10 italic">
                                        Live Stream
                                    </div>
                                </div>

                                <div className="space-y-4 font-mono text-[11px]">
                                    <div className="flex gap-4 p-3 bg-white/5 rounded-xl border border-white/5">
                                        <span className="text-indigo-400 shrink-0">[10:42:15]</span>
                                        <span className="text-emerald-400 shrink-0">SUCCESS</span>
                                        <span className="text-slate-300">Vector store optimized. 42 new chunks indexed.</span>
                                    </div>
                                    <div className="flex gap-4 p-3 hover:bg-white/5 rounded-xl transition-colors">
                                        <span className="text-indigo-400 shrink-0">[10:38:02]</span>
                                        <span className="text-blue-400 shrink-0">INFO</span>
                                        <span className="text-slate-300">LLM call initiated: "Explain leave policy" (Tokens: 245)</span>
                                    </div>
                                    <div className="flex gap-4 p-3 hover:bg-white/5 rounded-xl transition-colors">
                                        <span className="text-indigo-400 shrink-0">[10:35:12]</span>
                                        <span className="text-amber-400 shrink-0">SYNC</span>
                                        <span className="text-slate-300">Background ingestion task #883 started.</span>
                                    </div>
                                    <div className="flex gap-4 p-3 hover:bg-white/5 rounded-xl transition-colors">
                                        <span className="text-slate-500 shrink-0">[10:30:00]</span>
                                        <span className="text-slate-500 shrink-0">IDLE</span>
                                        <span className="text-slate-600">Waiting for next data ingestion...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* SIDEBAR */}
                    <div className="lg:col-span-4 space-y-8">

                        {/* Ingestion Module */}
                        <div className="bg-white rounded-[2rem] border border-gray-100 shadow-sm p-8 relative group overflow-hidden">
                            <div className="absolute top-0 right-0 w-2 h-full bg-indigo-600" />
                            <div className="flex items-start justify-between mb-8">
                                <div className="w-12 h-12 bg-indigo-600 text-white rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-100">
                                    <Upload size={24} />
                                </div>
                                <div className="text-[10px] font-black text-indigo-600 uppercase tracking-widest bg-indigo-50 px-2 py-1 rounded-lg">Input Node</div>
                            </div>

                            <h3 className="text-xl font-black text-slate-900 tracking-tight mb-2">Ingestion Engine</h3>
                            <p className="text-slate-500 text-sm mb-8 leading-relaxed">Securely upload corporate documentation. Files are encrypted, segmented into neural chunks, and indexed in the vector space.</p>

                            <div
                                onClick={() => fileInputRef.current?.click()}
                                className="border-2 border-dashed border-slate-100 hover:border-indigo-400 hover:bg-indigo-50/20 rounded-3xl p-10 text-center cursor-pointer transition-all duration-300 group/drop"
                            >
                                <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 group-hover/drop:scale-110 group-hover/drop:bg-indigo-100 transition-all duration-300">
                                    <Database size={28} className="text-slate-300 group-hover/drop:text-indigo-600 transition-colors" />
                                </div>
                                <p className="text-sm text-slate-600 font-bold">Standard Ingestion</p>
                                <p className="text-[10px] text-slate-400 mt-2 font-medium uppercase tracking-tighter">PDF, DOCX, TXT · MAX 10MB</p>
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
                                className="w-full mt-6 py-4 bg-slate-900 hover:bg-indigo-600 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-2xl text-sm font-black transition-all shadow-xl shadow-slate-100 active:scale-95 flex items-center justify-center gap-3"
                            >
                                {uploading ? (
                                    <>
                                        <RefreshCw size={18} className="animate-spin" />
                                        Neural Ingestion...
                                    </>
                                ) : (
                                    <>
                                        <Plus size={18} />
                                        Add Intelligence
                                    </>
                                )}
                            </button>
                        </div>

                        {/* System Health */}
                        <div className="bg-white rounded-[2rem] border border-gray-100 shadow-sm p-8">
                            <h3 className="text-base font-black text-slate-900 tracking-tight mb-6">Neural Health Metrics</h3>
                            <div className="space-y-6">
                                {[
                                    { label: 'RAG Pipeline', status: 'Optimal', health: 100, color: 'bg-emerald-500' },
                                    { label: 'Vector Index', status: 'Healthy', health: 98, color: 'bg-emerald-500' },
                                    { label: 'Database Node', status: 'Online', health: 100, color: 'bg-indigo-500' },
                                    { label: 'API Gateway', status: 'Active', health: 95, color: 'bg-blue-500' },
                                ].map(item => (
                                    <div key={item.label} className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs font-bold text-slate-600">{item.label}</span>
                                            <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md uppercase tracking-tighter">{item.status}</span>
                                        </div>
                                        <div className="h-1.5 w-full bg-slate-50 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full ${item.color} rounded-full transition-all duration-1000`}
                                                style={{ width: `${item.health}%`, opacity: 0.8 }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-8 pt-8 border-t border-slate-50">
                                <button
                                    onClick={() => navigate('/chat')}
                                    className="w-full flex items-center justify-between px-5 py-4 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-2xl transition-all group"
                                >
                                    <div className="flex items-center gap-3">
                                        <Sparkles size={18} />
                                        <span className="text-sm font-black">AI Command Center</span>
                                    </div>
                                    <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                                </button>
                            </div>
                        </div>

                    </div>
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
    );
}

export default DashboardPage;