import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Shield, ArrowRight, Brain, FileText, Bot,
    Lock, Zap, Users, Building2,
    CheckCircle, Menu, X, Database, Sparkles, ChevronRight, Globe, BarChart3,
    Search, Server, Cloud, Cpu, ArrowDownCircle, Layers
} from 'lucide-react';

const features = [
    {
        icon: Brain,
        title: 'Multi-Modal AI Engine',
        desc: 'Built on Gemini 1.5 & GPT-4o. Our system dynamically routes queries based on context length and task complexity.',
        color: 'text-indigo-600', bg: 'bg-indigo-50'
    },
    {
        icon: Database,
        title: 'Neural Vector Store',
        desc: 'Industry-standard PostgreSQL (pgvector) ensures ultra-low latency retrieval with billion-scale semantic indexing.',
        color: 'text-emerald-600', bg: 'bg-emerald-50'
    },
    {
        icon: Lock,
        title: 'Enterprise Security',
        desc: 'Military-grade encryption for documents at rest and in transit. Fully isolated tenant environments and RBAC.',
        color: 'text-rose-600', bg: 'bg-rose-50'
    },
    {
        icon: Zap,
        title: 'Adaptive Streaming',
        desc: 'Hardware-accelerated token streaming provides sub-200ms time-to-first-token for an ultra-responsive experience.',
        color: 'text-amber-600', bg: 'bg-amber-50'
    },
    {
        icon: FileText,
        title: 'Smart Ingestion',
        desc: 'Advanced OCR and layout-aware parsing for PDFs, Word, and Excel. Preserving hierarchical document context.',
        color: 'text-blue-600', bg: 'bg-blue-50'
    },
    {
        icon: BarChart3,
        title: 'Insight Analytics',
        desc: 'Comprehensive telemetry and audit trails. Monitor usage patterns, knowledge gaps, and system performance.',
        color: 'text-purple-600', bg: 'bg-purple-50'
    },
];

const stats = [
    { value: '< 200ms', label: 'Average Latency' },
    { value: '99.99%', label: 'Infrastructure Uptime' },
    { value: 'Zero', label: 'Data Leakage Risk' },
    { value: '100+', label: 'Supported Formats' },
];

function LandingPage() {
    const navigate = useNavigate();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 30);
        window.addEventListener('scroll', onScroll);
        return () => window.removeEventListener('scroll', onScroll);
    }, []);

    const scrollTo = (id) => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
        setMobileMenuOpen(false);
    };

    return (
        <div className="min-h-screen bg-[#fcfdfe] font-['Outfit',sans-serif] antialiased text-[#111827]">

            {/* ── TOP ANNOUNCEMENT ── */}
            <div className="bg-slate-900 py-2.5 px-6 text-center">
                <p className="text-[10px] font-bold text-white uppercase tracking-[0.2em] flex items-center justify-center gap-3">
                    <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />
                    New: Gemini 1.5 Pro integration now active for all enterprise nodes
                </p>
            </div>

            {/* ── NAVBAR ── */}
            <nav className={`fixed top-12 left-1/2 -translate-x-1/2 w-[90%] max-w-7xl z-50 transition-all duration-500 rounded-2xl ${scrolled ? 'bg-white/80 backdrop-blur-xl border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] py-3' : 'bg-transparent py-5'}`}>
                <div className="px-8 flex items-center justify-between">
                    <div className="flex items-center gap-3 cursor-pointer group" onClick={() => navigate('/')}>
                        <div className="w-10 h-10 bg-gradient-to-tr from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200 group-hover:scale-105 transition-transform">
                            <Shield size={18} className="text-white" />
                        </div>
                        <div className="flex flex-col">
                            <span className="font-extrabold text-slate-900 text-sm tracking-tight leading-none uppercase">Enterprise RAG</span>
                            <span className="text-[9px] text-slate-400 font-bold tracking-widest mt-1">INDUSTRIAL INTELLIGENCE</span>
                        </div>
                    </div>

                    <div className="hidden md:flex items-center gap-10">
                        {[['Platform', 'platform'], ['Architecture', 'how-it-works'], ['Security', 'features']].map(([label, id]) => (
                            <button key={id} onClick={() => scrollTo(id)} className="text-[13px] text-slate-500 hover:text-indigo-600 font-bold transition-colors uppercase tracking-wider">
                                {label}
                            </button>
                        ))}
                    </div>

                    <div className="hidden md:flex items-center gap-4">
                        <button
                            onClick={() => navigate('/login')}
                            className="text-[13px] font-bold text-slate-600 hover:text-slate-900"
                        >
                            Sign In
                        </button>
                        <button
                            onClick={() => navigate('/login')}
                            className="px-6 py-2.5 bg-slate-900 text-white text-[13px] font-bold rounded-xl hover:bg-indigo-600 transition-all shadow-xl shadow-slate-100 active:scale-95"
                        >
                            Get Started
                        </button>
                    </div>

                    <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden p-2 text-slate-600">
                        {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
                    </button>
                </div>

                {mobileMenuOpen && (
                    <div className="md:hidden absolute top-full left-0 w-full bg-white/95 backdrop-blur-xl border border-gray-100 rounded-2xl mt-2 p-6 space-y-4 shadow-2xl">
                        {[['Features', 'features'], ['Architecture', 'how-it-works']].map(([label, id]) => (
                            <button key={id} onClick={() => scrollTo(id)} className="block w-full text-left text-sm font-bold text-slate-600 py-2">
                                {label}
                            </button>
                        ))}
                        <button onClick={() => navigate('/login')} className="block w-full py-4 bg-indigo-600 text-white text-sm font-bold rounded-xl text-center">
                            Launch Platform
                        </button>
                    </div>
                )}
            </nav>

            {/* ── HERO ── */}
            <section id="platform" className="relative pt-60 pb-32 overflow-hidden">
                {/* Visual accents */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -z-10 w-full max-w-6xl aspect-square bg-[#eef2ff] rounded-full blur-[160px] opacity-40" />

                <div className="max-w-7xl mx-auto px-6 text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border border-gray-100 shadow-sm rounded-full mb-10">
                        <span className="w-1.5 h-1.5 bg-indigo-600 rounded-full animate-pulse" />
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic">V2.4 Enterprise Deployment</span>
                    </div>

                    <h1 className="text-6xl md:text-8xl font-[1000] text-slate-900 leading-[0.95] tracking-[-0.04em] mb-8">
                        The Neural Bridge to your <br />
                        <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">Corporate Memory.</span>
                    </h1>

                    <p className="text-lg md:text-xl text-slate-500 max-w-3xl mx-auto mb-14 leading-relaxed font-medium">
                        Enterprise RAG transforms your static documentation into a dynamic knowledge network.
                        Deploy intelligent agents that understand, retrieve, and synthesize your proprietary data with sub-second precision.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-5 justify-center">
                        <button
                            onClick={() => navigate('/login')}
                            className="px-10 py-5 bg-slate-900 text-white font-black rounded-2xl transition-all shadow-2xl shadow-slate-200 hover:bg-indigo-600 hover:-translate-y-1 active:scale-95 flex items-center justify-center gap-3 group"
                        >
                            Launch Pipeline
                            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                        </button>
                        <button
                            onClick={() => scrollTo('how-it-works')}
                            className="px-10 py-5 bg-white border border-gray-100 text-slate-900 font-black rounded-2xl transition-all hover:bg-slate-50 shadow-sm border-b-4 border-b-slate-100 active:border-b-0 active:translate-y-1 flex items-center justify-center gap-3"
                        >
                            Read Specification
                            <ChevronRight size={18} />
                        </button>
                    </div>

                    <div className="mt-24 max-w-5xl mx-auto relative">
                        <div className="absolute -inset-4 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-[2.5rem] blur-2xl opacity-10" />
                        <div className="relative bg-white rounded-[2rem] border border-gray-100 shadow-2xl overflow-hidden">
                            <div className="bg-slate-50 border-b border-gray-100 px-6 py-4 flex items-center justify-between">
                                <div className="flex gap-1.5">
                                    <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
                                    <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
                                    <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
                                </div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                    Secure Session: NODE_ALPHA_04
                                </div>
                                <div className="w-10" />
                            </div>
                            <div className="flex h-96">
                                <div className="w-64 bg-slate-900 p-8 shrink-0 text-left border-r border-white/5">
                                    <div className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] mb-6">Pipeline Status</div>
                                    <div className="space-y-6">
                                        <div>
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-[10px] text-white/40 font-bold uppercase tracking-tighter">Vector Cache</span>
                                                <span className="text-[10px] text-emerald-400 font-bold">100%</span>
                                            </div>
                                            <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                                <div className="h-full bg-emerald-500 w-full" />
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-[10px] text-white/40 font-bold uppercase tracking-tighter">Embedding Load</span>
                                                <span className="text-[10px] text-indigo-400 font-bold">42%</span>
                                            </div>
                                            <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                                <div className="h-full bg-indigo-500 w-[42%]" />
                                            </div>
                                        </div>
                                        <div className="pt-4 space-y-3">
                                            <div className="text-[11px] text-white/60 font-medium flex items-center gap-2">
                                                <div className="w-1 h-1 bg-indigo-500 rounded-full" /> Document Index
                                            </div>
                                            <div className="text-[11px] text-white/30 font-medium flex items-center gap-2">
                                                <div className="w-1 h-1 bg-white/10 rounded-full" /> Neural Logs
                                            </div>
                                            <div className="text-[11px] text-white/30 font-medium flex items-center gap-2">
                                                <div className="w-1 h-1 bg-white/10 rounded-full" /> System Config
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex-1 bg-[#fdfdff] p-10 flex flex-col">
                                    <div className="flex-1 space-y-6">
                                        <div className="flex justify-end animate-pulse">
                                            <div className="px-6 py-3 bg-indigo-600 text-white text-[13px] font-medium rounded-2xl rounded-tr-sm shadow-lg shadow-indigo-100">
                                                Explain the cross-departmental impact of Project Orion.
                                            </div>
                                        </div>
                                        <div className="flex gap-4">
                                            <div className="w-10 h-10 bg-slate-900 border border-white/10 rounded-xl flex items-center justify-center shrink-0 shadow-lg">
                                                <Bot size={18} className="text-white" />
                                            </div>
                                            <div className="p-6 bg-white border border-gray-100 text-[13px] text-slate-600 rounded-2xl rounded-tl-sm shadow-sm leading-relaxed text-left flex-1">
                                                <div className="flex items-center gap-2 mb-3">
                                                    <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded uppercase tracking-tighter">Source: Strategic_Review_Q4.pdf</span>
                                                </div>
                                                Project Orion is projected to reduce inter-departmental friction by <strong>24%</strong> through centralized neural data routing. Primary impacts observed in:
                                                <ul className="mt-2 space-y-1 list-disc list-inside">
                                                    <li><strong>Operations:</strong> Automated compliance verification</li>
                                                    <li><strong>HR:</strong> Streamlined talent acquisition workflows</li>
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── STATS ── */}
            <section className="py-24 border-y border-gray-50 bg-white">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-12">
                        {stats.map((stat, i) => (
                            <div key={i} className="text-center group">
                                <div className="text-5xl font-black text-slate-900 mb-2 tracking-tighter group-hover:text-indigo-600 transition-colors">{stat.value}</div>
                                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em]">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── HOW IT WORKS (ARCHITECTURE) ── */}
            <section id="how-it-works" className="py-32 relative overflow-hidden bg-slate-900">
                <div className="absolute inset-0 -z-10 opacity-20">
                    <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-indigo-500 rounded-full blur-[200px] -mr-96 -mt-96" />
                    <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-violet-500 rounded-full blur-[200px] -ml-96 -mb-96" />
                </div>

                <div className="max-w-7xl mx-auto px-6">
                    <div className="text-center mb-24">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 border border-white/10 text-white text-[10px] font-bold uppercase tracking-widest rounded-full mb-6">
                            <Server size={12} /> System Specification
                        </div>
                        <h2 className="text-5xl font-black text-white mb-6 tracking-tight">How Corporate Intelligence is Built</h2>
                        <p className="text-slate-400 max-w-2xl mx-auto text-lg">Our RAG (Retrieval-Augmented Generation) pipeline ensures that AI responses are factually grounded in your proprietary documentation.</p>
                    </div>

                    <div className="grid md:grid-cols-4 gap-4">
                        {[
                            { step: '01', title: 'Data Ingress', desc: 'Documents (PDF, Word, TXT) are ingested via secure API. Metadata headers are preserved for RBAC compliance.', icon: ArrowDownCircle },
                            { step: '02', title: 'Neural Partitioning', desc: 'Advanced recursive character splitting segments documents into semantic "chunks" to maximize context relevance.', icon: Layers },
                            { step: '03', title: 'Vector Encoding', desc: 'Each chunk is processed through an embedding model (Gemini/Ada) and indexed into ours high-speed PostgreSQL vector store.', icon: Database },
                            { step: '04', title: 'Semantic Matching', desc: 'Queries trigger a k-nearest neighbor (k-NN) search to retrieve the most semantically relevant knowledge fragments.', icon: Search },
                        ].map((item, i) => (
                            <div key={i} className="group p-8 bg-white/5 border border-white/5 rounded-[2rem] hover:bg-white/10 transition-all duration-300">
                                <div className="text-4xl font-black text-indigo-500/20 mb-6 font-mono tracking-tighter">{item.step}</div>
                                <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-indigo-900 group-hover:scale-110 transition-transform">
                                    <item.icon size={22} className="text-white" />
                                </div>
                                <h3 className="font-bold text-white mb-4 text-xl tracking-tight">{item.title}</h3>
                                <p className="text-sm text-slate-400 leading-relaxed font-medium">{item.desc}</p>
                            </div>
                        ))}
                    </div>

                    <div className="mt-20 p-10 bg-indigo-600 rounded-[2.5rem] flex flex-col md:flex-row items-center gap-10 shadow-2xl shadow-indigo-950">
                        <div className="flex-1 text-center md:text-left">
                            <h3 className="text-2xl font-black text-white mb-4 tracking-tight">Built for Maximum Reliability</h3>
                            <p className="text-indigo-100 text-sm leading-relaxed max-w-xl">By combining retrieval with generation, we eliminate hallucinations. Every AI response includes a traceable link back to the source material, ensuring 100% accountability.</p>
                        </div>
                        <div className="flex items-center gap-6">
                            <div className="flex -space-x-4">
                                {[1, 2, 3].map(n => (
                                    <div key={n} className="w-12 h-12 rounded-full border-4 border-indigo-600 bg-slate-100 flex items-center justify-center text-[10px] font-black">AI</div>
                                ))}
                            </div>
                            <div className="text-white">
                                <div className="text-2xl font-black leading-none">99.9%</div>
                                <div className="text-[10px] font-bold uppercase tracking-widest text-indigo-200 mt-1">Accuracy SLA</div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── FEATURES section & more ── */}
            <section id="features" className="py-32">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="flex flex-col md:flex-row md:items-end justify-between gap-10 mb-20">
                        <div className="max-w-2xl">
                            <h2 className="text-5xl font-black text-slate-900 tracking-tight leading-none mb-6">Industrial Grade <br />Capabilities.</h2>
                            <p className="text-slate-500 text-lg font-medium leading-relaxed">Enterprise RAG isnt just a chatbot. Its a robust infrastructure for high-scale document orchestration and authorized knowledge retrieval.</p>
                        </div>
                        <div className="flex gap-4">
                            <div className="px-6 py-3 bg-slate-50 border border-slate-100 rounded-2xl">
                                <div className="text-2xl font-black text-slate-900">4+</div>
                                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">Role Tiers</div>
                            </div>
                        </div>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {features.map((f, i) => (
                            <div key={i} className="p-8 bg-white border border-gray-100 rounded-[2rem] hover:shadow-2xl hover:shadow-indigo-50 transition-all group">
                                <div className={`w-14 h-14 ${f.bg} ${f.color} rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300 shadow-inner`}>
                                    <f.icon size={26} />
                                </div>
                                <h3 className="text-xl font-black text-slate-900 mb-3 tracking-tight">{f.title}</h3>
                                <p className="text-sm text-slate-500 leading-relaxed font-medium">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── CTA ── */}
            <section className="py-32 bg-slate-950 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                <div className="max-w-5xl mx-auto px-6 text-center relative z-10">
                    <div className="w-20 h-20 bg-gradient-to-tr from-indigo-600 to-violet-600 rounded-3xl flex items-center justify-center mx-auto mb-10 shadow-2xl shadow-indigo-600/40">
                        <Shield size={36} className="text-white" />
                    </div>
                    <h2 className="text-5xl md:text-7xl font-[1000] text-white mb-10 tracking-[-0.03em] leading-tight">
                        Standardize your <br />
                        Knowledge Network.
                    </h2>
                    <p className="text-slate-400 text-lg mb-14 max-w-xl mx-auto font-medium">
                        Join hundreds of departments leveraging enterprise RAG for secure, accurate, and compliant AI intelligence retrieval.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-5 justify-center mt-12">
                        <button
                            onClick={() => navigate('/login')}
                            className="px-12 py-5 bg-white text-slate-900 font-black rounded-2xl transition-all shadow-xl hover:bg-slate-50 hover:-translate-y-1 active:scale-95 flex items-center justify-center gap-3"
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </section>

            {/* ── FOOTER ── */}
            <footer className="bg-black py-16 px-6 border-t border-white/5">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-10">
                    <div className="flex flex-col items-center md:items-start gap-3">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                                <Shield size={14} className="text-white" />
                            </div>
                            <span className="text-sm font-black text-white uppercase tracking-widest">Enterprise RAG</span>
                        </div>
                        <p className="text-slate-600 text-[11px] font-bold tracking-widest mt-2 uppercase">© 2026 Industrial Intelligence Systems Inc.</p>
                    </div>
                    <div className="flex gap-10">
                        <div>
                            <h4 className="text-[11px] font-black text-white uppercase tracking-[0.2em] mb-4">Core Stack</h4>
                            <ul className="text-[11px] text-slate-500 font-bold uppercase space-y-2">
                                <li>Google Gemini 1.5</li>
                                <li>PostgreSQL Vector</li>
                                <li>FastAPI Backend</li>
                            </ul>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-full border border-white/5">
                        <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                        <span className="text-[11px] text-white/60 font-black uppercase tracking-widest">Global Node Online</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}

export default LandingPage;
