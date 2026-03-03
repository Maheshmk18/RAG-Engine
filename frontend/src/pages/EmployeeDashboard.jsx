import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Users, FileText, MessageSquare, ArrowLeft,
    Upload, Trash2, LogOut, Shield,
    Activity, Database, RefreshCw, ChevronRight,
    Search, Filter, ExternalLink, CheckCircle, Sparkles
} from 'lucide-react';
import { usersAPI, documentsAPI, chatAPI } from '../services/api';
import { getUser, logout } from '../utils/auth';
import ProfileModal from '../components/ProfileModal';

function EmployeeDashboard() {
    const navigate = useNavigate();
    const [stats, setStats] = useState({
        users: 0,
        documents: 0,
        sessions: 0,
    });
    const [loading, setLoading] = useState(true);
    const [documents, setDocuments] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const fileInputRef = useRef(null);
    const [user, setUser] = useState(getUser());

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
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

            setStats({
                users: usersList.length,
                documents: docsList.length,
                sessions: sessionsList.length,
            });
            setDocuments(docsList);
        } catch (err) {
            console.error('Data orchestration failed:', err);
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
            console.error('Ingestion failed:', err);
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDeleteDocument = async (id) => {
        if (!window.confirm('Wipe document from corporate knowledge vault?')) return;
        try {
            await documentsAPI.delete(id);
            await loadAllData();
        } catch (err) {
            console.error('Purge failed:', err);
        }
    };

    if (!user) return null;

    return (
        <div className="min-h-screen bg-[#FDFDFD] selection:bg-indigo-100 flex flex-col">
            {/* Professional Header - Updated to Bold/Non-Italic */}
            <header className="h-20 bg-white border-b border-slate-100 flex items-center justify-between px-8 text-slate-900 sticky top-0 z-50 shadow-xl shadow-sky-100/30">
                <div className="flex items-center gap-6">
                    <div
                        className="flex items-center gap-3 cursor-pointer group"
                        onClick={() => navigate('/')}
                    >
                        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform shadow-sky-400/20">
                            <Shield size={22} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-sm font-bold tracking-widest uppercase leading-none text-slate-900">Intelligence Hub</h1>
                            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-1">Operator Console</div>
                        </div>
                    </div>

                    <div className="hidden lg:flex items-center gap-1.5 px-4 py-1.5 bg-indigo-50 rounded-full border border-indigo-100">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-600">Node Sync Active</span>
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    <button
                        onClick={() => navigate('/chat')}
                        className="text-xs font-bold uppercase tracking-widest text-slate-400 hover:text-indigo-600 transition-colors flex items-center gap-2 group"
                    >
                        <Sparkles size={16} className="text-indigo-400 group-hover:text-indigo-600 transition-colors" /> Intelligence Terminal
                    </button>

                    <div className="h-8 w-px bg-slate-100"></div>

                    <div className="flex items-center gap-3 pl-2">
                        <div className="text-right hidden sm:block">
                            <div className="text-sm font-bold text-slate-900 tracking-tight">{user.full_name || user.username}</div>
                            <div className="text-[9px] text-indigo-400 font-bold uppercase tracking-widest leading-none mt-1">Authorized Operator</div>
                        </div>
                        <button
                            onClick={logout}
                            className="w-10 h-10 bg-white hover:bg-red-50 border border-slate-100 hover:border-red-100 rounded-xl flex items-center justify-center transition-all group shadow-sm"
                        >
                            <LogOut size={18} className="text-slate-400 group-hover:text-red-500" />
                        </button>
                    </div>
                </div>
            </header>

            <main className="flex-1 p-8 md:p-12 max-w-[1400px] w-full mx-auto">
                <div className="mb-10">
                    <h2 className="text-3xl font-black text-slate-900 tracking-tightest uppercase">Sector Dashboard</h2>
                    <p className="text-[10px] font-bold text-slate-400 mt-2 uppercase tracking-widest leading-none">Managing synchronized assets for localized operations.</p>
                </div>

                {/* Stats Grid with SkyBlue Shadows */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
                    {[
                        { label: 'Network Personnels', value: stats.users, icon: Users, color: 'text-indigo-600', bg: 'bg-indigo-50' },
                        { label: 'Knowledge Assets', value: stats.documents, icon: FileText, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                        { label: 'Intelligence Links', value: stats.sessions, icon: MessageSquare, color: 'text-blue-600', bg: 'bg-blue-50' }
                    ].map((stat, i) => (
                        <div key={i} className="p-8 bg-white rounded-[2rem] border border-slate-100 shadow-[0_20px_50px_-20px_rgba(135,206,235,0.4)] hover:shadow-[0_40px_80px_-20px_rgba(135,206,235,0.6)] transition-all group relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-24 h-24 bg-slate-50 rounded-bl-[4rem] -mr-8 -mt-8 -z-10 transition-transform group-hover:scale-110"></div>
                            <div className="flex items-center justify-between mb-6">
                                <div className={`w-12 h-12 ${stat.bg} ${stat.color} rounded-2xl flex items-center justify-center group-hover:rotate-6 transition-transform shadow-sm`}>
                                    <stat.icon size={22} />
                                </div>
                                <Activity size={14} className={`${stat.color} opacity-20`} />
                            </div>
                            <div className="text-4xl font-black text-slate-900 tracking-tightest mb-1">{loading ? '...' : stat.value}</div>
                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{stat.label}</div>
                        </div>
                    ))}
                </div>

                <div className="grid lg:grid-cols-[1fr_350px] gap-8">
                    {/* Repository Terminal */}
                    <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-[0_30px_70px_-20px_rgba(135,206,235,0.35)] flex flex-col overflow-hidden">
                        <div className="p-10 border-b border-slate-50 flex items-center justify-between bg-slate-50/30">
                            <div>
                                <h3 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3 uppercase">
                                    <Database size={24} className="text-indigo-600" />
                                    Knowledge Vault
                                </h3>
                                <p className="text-[10px] font-bold text-slate-400 mt-2 uppercase tracking-widest leading-none">Active synchronization manifest for vectorized documentation.</p>
                            </div>
                            <button
                                onClick={loadAllData}
                                className="p-3 bg-white border border-slate-100 rounded-xl text-slate-400 hover:text-indigo-600 hover:shadow-lg transition-all shadow-sm"
                            >
                                <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
                            </button>
                        </div>

                        <div className="flex-1 overflow-x-auto">
                            <table className="w-full text-left">
                                <thead>
                                    <tr className="bg-slate-50/50">
                                        <th className="px-10 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Asset Identity</th>
                                        <th className="px-6 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Complexity</th>
                                        <th className="px-6 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Vector Status</th>
                                        <th className="px-10 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest text-right">Gateways</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-50">
                                    {loading ? (
                                        [1, 2, 3].map(n => (
                                            <tr key={n} className="animate-pulse">
                                                <td colSpan="4" className="px-10 py-8"><div className="h-4 bg-slate-100 rounded-full w-2/3"></div></td>
                                            </tr>
                                        ))
                                    ) : documents.length === 0 ? (
                                        <tr>
                                            <td colSpan="4" className="px-10 py-24 text-center">
                                                <div className="flex flex-col items-center gap-4">
                                                    <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center border border-dashed border-slate-200">
                                                        <Database size={32} className="text-slate-200" />
                                                    </div>
                                                    <div>
                                                        <p className="text-slate-950 font-bold uppercase text-sm tracking-widest">Vault Empty</p>
                                                        <p className="text-slate-400 text-[10px] mt-1 font-bold uppercase tracking-widest leading-none">Initiate data ingestion to populate.</p>
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        documents.map(doc => (
                                            <tr key={doc.id} className="hover:bg-slate-50 transition-colors group">
                                                <td className="px-10 py-6">
                                                    <div className="flex items-center gap-4">
                                                        <div className="w-12 h-12 bg-slate-50 border border-slate-100 text-slate-400 rounded-2xl flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white group-hover:border-indigo-600 transition-all shadow-sm">
                                                            <FileText size={20} />
                                                        </div>
                                                        <div>
                                                            <div className="text-sm font-bold text-slate-900 tracking-tight">{doc.original_filename}</div>
                                                            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">UID-{doc.id.slice(0, 8)}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-6">
                                                    <div className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                                                        {doc.chunk_count || '0'} <span className="text-slate-300 font-bold ml-1">Nodes</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-6">
                                                    <div className="flex items-center gap-3">
                                                        <div className={`w-2 h-2 rounded-full ${doc.status === 'processed' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-amber-500 animate-pulse'}`}></div>
                                                        <span className={`text-[10px] font-bold uppercase tracking-widest ${doc.status === 'processed' ? 'text-emerald-600' : 'text-amber-600'}`}>
                                                            {doc.status}
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-10 py-6 text-right">
                                                    <button
                                                        onClick={() => handleDeleteDocument(doc.id)}
                                                        className="w-10 h-10 bg-white border border-slate-100 text-slate-300 hover:text-red-500 hover:border-red-500/20 hover:bg-red-50 rounded-xl transition-all opacity-0 group-hover:opacity-100 flex items-center justify-center shadow-sm"
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

                    {/* Quick Ingestion Panel */}
                    <div className="space-y-8">
                        <div className="bg-white rounded-[2.5rem] p-10 text-slate-900 relative shadow-[0_30px_70px_-20px_rgba(135,206,235,0.4)] overflow-hidden border border-slate-100">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50/50 rounded-full blur-3xl"></div>
                            <div className="flex items-center gap-3 mb-8">
                                <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center border border-indigo-100">
                                    <Upload size={20} className="text-indigo-600" />
                                </div>
                                <h4 className="text-lg font-black uppercase tracking-tightest">Data Ingestion</h4>
                            </div>

                            <div className="space-y-6">
                                <div className="p-8 bg-slate-50 border border-slate-100 rounded-3xl text-center flex flex-col items-center gap-4 group">
                                    <div className="w-16 h-16 bg-white border border-slate-100 rounded-[1.5rem] flex items-center justify-center group-hover:scale-110 transition-transform shadow-xl shadow-sky-100">
                                        <Database size={28} className="text-slate-950" />
                                    </div>
                                    <div>
                                        <div className="text-xs font-bold uppercase tracking-widest text-slate-900 mb-2">Vector Import Gateway</div>
                                        <div className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em]">PDF • DOCX • TXT</div>
                                    </div>
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={uploading}
                                        className="w-full mt-4 py-4 bg-indigo-600 hover:bg-slate-900 hover:text-white text-white rounded-2xl font-bold text-[10px] uppercase tracking-widest transition-all active:scale-95 disabled:opacity-50 shadow-lg shadow-indigo-600/20"
                                    >
                                        {uploading ? 'INGESTING...' : 'INITIALIZE UPLOAD'}
                                    </button>
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        onChange={handleFileUpload}
                                        className="hidden"
                                        accept=".pdf,.txt,.doc,.docx"
                                    />
                                </div>

                                <div className="flex items-center justify-between px-2 opacity-40">
                                    <div className="flex items-center gap-2">
                                        <CheckCircle size={14} className="text-emerald-500" />
                                        <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Security: AES-256</span>
                                    </div>
                                    <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-widest">LOCAL NODE</span>
                                </div>
                            </div>
                        </div>

                        <div
                            onClick={() => navigate('/chat')}
                            className="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-[0_20px_60px_-15px_rgba(135,206,235,0.4)] hover:shadow-[0_40px_80px_-20px_rgba(135,206,235,0.6)] transition-all group cursor-pointer relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50/50 rounded-bl-[4rem] -mr-12 -mt-12 transition-transform group-hover:scale-110"></div>
                            <div className="flex items-center justify-between mb-8">
                                <div className="w-14 h-14 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                                    <Sparkles size={24} />
                                </div>
                                <ChevronRight size={20} className="text-slate-200 group-hover:text-indigo-600 transition-colors" />
                            </div>
                            <h4 className="text-xl font-black text-slate-900 uppercase tracking-tightest mb-2">Neural Workspace</h4>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-relaxed">Direct link to RAG-powered intelligence terminal.</p>
                        </div>
                    </div>
                </div>
            </main>

            <footer className="py-12 border-t border-slate-100 text-center bg-white">
                <div className="text-[10px] font-bold text-slate-200 uppercase tracking-[0.8em]">
                    Enterprise Intelligence Console • Secured Identity Node
                </div>
            </footer>
        </div>
    );
}

export default EmployeeDashboard;
