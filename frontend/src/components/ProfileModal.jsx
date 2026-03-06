import { useState, useRef } from 'react';
import { X, Camera, Mail, Phone, User, Lock, Save, Shield, UserCircle, CheckCircle } from 'lucide-react';
import api from '../services/api';

const ProfileModal = ({ user, onClose, onUpdate }) => {
    const [formData, setFormData] = useState({
        full_name: user?.full_name || '',
        email: user?.email || '',
        phone: user?.phone || '',
        password: '',
        confirmPassword: ''
    });
    const [profilePhoto, setProfilePhoto] = useState(user?.profile_photo || null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const fileInputRef = useRef(null);

    const handlePhotoChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) {
                setError('Identity asset size exceeds 5MB limit.');
                return;
            }

            const reader = new FileReader();
            reader.onloadend = () => {
                setProfilePhoto(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (formData.password && formData.password !== formData.confirmPassword) {
            setError('Security authentication mismatch: Passwords do not correlate.');
            return;
        }

        setLoading(true);

        try {
            const updateData = {
                full_name: formData.full_name,
                email: formData.email,
                phone: formData.phone,
                profile_photo: profilePhoto
            };

            if (formData.password) {
                updateData.password = formData.password;
            }

            const response = await api.put('/users/me', updateData);

            const userData = JSON.parse(localStorage.getItem('user') || '{}');
            const updatedUser = { ...userData, ...response.data };
            localStorage.setItem('user', JSON.stringify(updatedUser));

            setSuccess('Identity synchronization complete.');
            onUpdate && onUpdate(response.data);

            setTimeout(() => {
                onClose();
            }, 1500);
        } catch (err) {
            setError(err.response?.data?.detail || 'Identity synchronization failed.');
        } finally {
            setLoading(false);
        }
    };

    const getInitials = (name) => {
        return name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'OP';
    };

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-md animate-in fade-in duration-300">
            <div className="bg-white w-full max-w-2xl rounded-[2.5rem] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300 relative flex flex-col md:flex-row">

                {/* Left side branding */}
                <div className="w-full md:w-1/3 bg-slate-950 p-10 flex flex-col items-center justify-center text-center relative overflow-hidden">
                    <div className="absolute inset-0 opacity-5 pointer-events-none"
                        style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '24px 24px' }}></div>

                    <div className="relative z-10">
                        <div className="relative mb-6 inline-block">
                            <div className="w-24 h-24 rounded-3xl overflow-hidden border-2 border-indigo-500/30 p-1">
                                {profilePhoto ? (
                                    <img src={profilePhoto} alt="Identity" className="w-full h-full object-cover rounded-2xl grayscale hover:grayscale-0 transition-all duration-500" />
                                ) : (
                                    <div className="w-full h-full bg-slate-900 rounded-2xl flex items-center justify-center text-2xl font-black text-white italic">
                                        {getInitials(formData.full_name)}
                                    </div>
                                )}
                            </div>
                            <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className="absolute -bottom-2 -right-2 w-9 h-9 bg-indigo-600 hover:bg-slate-800 text-white rounded-xl flex items-center justify-center shadow-lg transition-all active:scale-90"
                            >
                                <Camera size={16} />
                            </button>
                        </div>
                        <h3 className="text-white font-black text-lg tracking-tight mb-1">{formData.full_name || 'System Operator'}</h3>
                        <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.2em] italic">Identity Node</p>
                    </div>

                    <input ref={fileInputRef} type="file" accept="image/*" onChange={handlePhotoChange} className="hidden" />
                </div>

                {/* Right side form */}
                <div className="flex-1 p-10 md:p-14 bg-white max-h-[90vh] overflow-y-auto custom-scrollbar">
                    <div className="flex justify-between items-center mb-10">
                        <div className="flex items-center gap-3">
                            <UserCircle size={24} className="text-indigo-600" />
                            <h2 className="text-2xl font-black text-slate-900 tracking-tight italic">Security Profile</h2>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-slate-50 rounded-full text-slate-300 transition-colors">
                            <X size={24} />
                        </button>
                    </div>

                    {error && (
                        <div className="mb-8 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm font-bold flex items-center gap-3 animate-in slide-in-from-top-2">
                            <X size={18} className="shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {success && (
                        <div className="mb-8 p-4 bg-emerald-50 border-l-4 border-emerald-500 text-emerald-700 text-sm font-bold flex items-center gap-3 animate-in slide-in-from-top-2">
                            <CheckCircle size={18} className="shrink-0" />
                            <span>{success}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-8">
                        <div className="grid gap-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <User size={12} /> Legal Full Name
                                </label>
                                <input
                                    type="text"
                                    className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-indigo-500/5 focus:border-indigo-500 outline-none transition-all font-bold text-slate-900 italic-none"
                                    value={formData.full_name}
                                    onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                                    placeholder="Enter full name"
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <Mail size={12} /> Corporate Communication
                                </label>
                                <input
                                    type="email"
                                    className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-indigo-500/5 focus:border-indigo-500 outline-none transition-all font-bold text-slate-900 italic-none"
                                    value={formData.email}
                                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                                    placeholder="corporate.id@enterprise.com"
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                    <Phone size={12} /> Direct Contact Link
                                </label>
                                <input
                                    type="tel"
                                    className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-indigo-500/5 focus:border-indigo-500 outline-none transition-all font-bold text-slate-900 italic-none"
                                    value={formData.phone}
                                    onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                    placeholder="+1-000-000-0000"
                                />
                            </div>
                        </div>

                        <div className="pt-8 border-t border-slate-50 space-y-6">
                            <div className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Temporal Credential Update</div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest italic">New Entropy</label>
                                    <input
                                        type="password"
                                        className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-indigo-500/5 focus:border-indigo-500 outline-none transition-all font-bold text-slate-900"
                                        value={formData.password}
                                        onChange={e => setFormData({ ...formData, password: e.target.value })}
                                        placeholder="••••••••"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest italic">Correlation</label>
                                    <input
                                        type="password"
                                        className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-4 focus:ring-indigo-500/5 focus:border-indigo-500 outline-none transition-all font-bold text-slate-900"
                                        value={formData.confirmPassword}
                                        onChange={e => setFormData({ ...formData, confirmPassword: e.target.value })}
                                        placeholder="••••••••"
                                    />
                                </div>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-5 bg-slate-950 hover:bg-indigo-600 text-white font-black text-xs uppercase tracking-[0.2em] rounded-2xl transition-all active:scale-[0.98] flex items-center justify-center gap-3 shadow-xl"
                        >
                            {loading ? (
                                <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Save size={18} />
                                    <span>Synchronize Identity</span>
                                </>
                            )}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default ProfileModal;