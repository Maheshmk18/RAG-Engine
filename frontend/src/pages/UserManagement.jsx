import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Edit2, Trash2, Check, X, Plus, Users,
  Home, Shield, User, Mail, Lock, ShieldCheck,
  AtSign, Search, Filter, Activity, UserPlus
} from 'lucide-react';
import api from '../services/api';

const ROLES = [
  { id: 'admin', name: 'Administrator', color: 'bg-indigo-600', icon: Shield },
  { id: 'manager', name: 'Ops Manager', color: 'bg-amber-600', icon: Activity },
  { id: 'hr', name: 'HR Admin', color: 'bg-rose-600', icon: Users },
  { id: 'employee', name: 'Standard Operator', color: 'bg-slate-600', icon: User }
];

function UserManagement() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'employee'
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/users/');
      setUsers(response.data || []);
    } catch (err) {
      console.error('Core identity fetch failed:', err);
      setError('System Error: Identity retrieval failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user.id);
    setEditForm({
      email: user.email,
      full_name: user.full_name || '',
      is_active: user.is_active,
      role: user.role
    });
  };

  const handleSave = async (userId) => {
    try {
      await api.put(`/users/${userId}`, editForm);
      setEditingUser(null);
      setSuccess('Identity protocols updated.');
      setTimeout(() => setSuccess(''), 3000);
      await loadUsers();
    } catch (err) {
      setError('Validation Error: Protocol update failed.');
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Wipe user identity from corporate directory? This action is irreversible.')) return;
    try {
      await api.delete(`/users/${userId}`);
      setSuccess('Identity purged successfully.');
      setTimeout(() => setSuccess(''), 3000);
      await loadUsers();
    } catch (err) {
      setError('Security Error: Identity purge failed.');
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/users/', createForm);
      setShowCreateModal(false);
      setCreateForm({ username: '', email: '', password: '', full_name: '', role: 'employee' });
      setSuccess('New identity synchronized.');
      setTimeout(() => setSuccess(''), 3000);
      await loadUsers();
    } catch (err) {
      setError('Sync Error: Registration failed.');
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFDFD] selection:bg-indigo-100 flex flex-col italic-none">
      {/* Governance Header - Updated to Bold/Non-Italic */}
      <header className="h-24 bg-white flex items-center justify-between px-10 border-b border-slate-100 sticky top-0 z-[100] shadow-xl shadow-sky-100/30">
        <div className="flex items-center gap-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="w-12 h-12 bg-white hover:bg-slate-50 border border-slate-100 rounded-2xl flex items-center justify-center transition-all group active:scale-95 shadow-lg shadow-slate-200/20"
          >
            <ArrowLeft size={18} className="text-slate-400 group-hover:text-indigo-600" />
          </button>

          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-600/10">
              <ShieldCheck size={22} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-900 tracking-tightest uppercase leading-none">User Governance</h1>
              <div className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-1">Directory v4.2</div>
            </div>
          </div>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-indigo-600 text-white flex items-center gap-3 px-8 py-4 rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-slate-900 transition-all active:scale-95 shadow-xl shadow-indigo-600/20"
        >
          <UserPlus size={18} />
          <span>Synchronize New Identity</span>
        </button>
      </header>

      <main className="flex-1 p-8 md:p-14 max-w-7xl w-full mx-auto">
        {error && (
          <div className="mb-10 p-5 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm font-bold flex items-center gap-4 animate-in slide-in-from-top-2">
            <X size={20} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="mb-10 p-5 bg-emerald-50 border-l-4 border-emerald-500 text-emerald-700 text-sm font-bold flex items-center gap-4 animate-in slide-in-from-top-2">
            <Check size={20} className="shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {/* Directory Manifest */}
        <div className="bg-white rounded-[3rem] border border-slate-100 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.06)] overflow-hidden flex flex-col">
          <div className="p-10 border-b border-slate-50 flex items-center justify-between gap-6 bg-slate-50/30">
            <div>
              <h3 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-4 uppercase">
                <Users size={24} className="text-indigo-600" />
                Directory Manifest
              </h3>
              <p className="text-sm font-bold text-slate-400 mt-1 uppercase tracking-widest">Real-time sync with corporate identity nodes.</p>
            </div>

            <div className="flex items-center gap-4">
              <div className="relative">
                <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" />
                <input
                  type="text"
                  placeholder="Query identity..."
                  className="pl-11 pr-6 py-3 bg-white border border-slate-100 rounded-xl text-xs font-bold tracking-widest text-slate-900 outline-none focus:ring-4 focus:ring-sky-500/5 focus:border-indigo-400 transition-all w-64 uppercase"
                />
              </div>
              <button className="p-3 bg-white border border-slate-100 rounded-xl text-slate-400 hover:text-indigo-600 transition-colors shadow-sm">
                <Filter size={18} />
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-10 py-6 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Identity Metadata</th>
                  <th className="px-6 py-6 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Communication Alias</th>
                  <th className="px-6 py-6 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Priority Clearance</th>
                  <th className="px-6 py-6 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Operational Status</th>
                  <th className="px-10 py-6 text-[10px] font-bold text-slate-400 uppercase tracking-widest text-right">Access Controls</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {loading ? (
                  [1, 2, 3].map(n => (
                    <tr key={n} className="animate-pulse">
                      <td colSpan="5" className="px-10 py-10"><div className="h-4 bg-slate-100 rounded-full w-3/4"></div></td>
                    </tr>
                  ))
                ) : users.map(user => {
                  const roleConfig = ROLES.find(r => r.id === user.role) || ROLES[3];
                  return (
                    <tr key={user.id} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-10 py-8">
                        <div className="flex items-center gap-5">
                          <div className={`w-14 h-14 rounded-[1.5rem] flex items-center justify-center text-white shrink-0 shadow-lg ${roleConfig.color} group-hover:scale-105 transition-transform shadow-indigo-600/10`}>
                            <roleConfig.icon size={22} />
                          </div>
                          <div>
                            {editingUser === user.id ? (
                              <input
                                type="text"
                                className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold tracking-tight outline-none border-indigo-500"
                                value={editForm.full_name}
                                onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                              />
                            ) : (
                              <div className="text-base font-bold text-slate-900 tracking-tight">{user.full_name || 'System Operator'}</div>
                            )}
                            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1 flex items-center gap-1.5 leading-none">
                              <AtSign size={10} className="text-indigo-500" /> {user.username}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-8">
                        {editingUser === user.id ? (
                          <input
                            type="email"
                            className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold tracking-tight outline-none border-indigo-500"
                            value={editForm.email}
                            onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                          />
                        ) : (
                          <span className="text-sm font-bold text-slate-500 tracking-tight">{user.email}</span>
                        )}
                      </td>
                      <td className="px-6 py-8">
                        {editingUser === user.id ? (
                          <select
                            className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold tracking-widest outline-none border-indigo-500 uppercase"
                            value={editForm.role}
                            onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                          >
                            {ROLES.map(r => (
                              <option key={r.id} value={r.id}>{r.name.toUpperCase()}</option>
                            ))}
                          </select>
                        ) : (
                          <span className={`px-4 py-1.5 rounded-full text-[9px] font-bold uppercase tracking-widest text-white shadow-sm ${roleConfig.color}`}>
                            {roleConfig.name}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-8">
                        <div className="flex items-center gap-3">
                          <div className={`w-2.5 h-2.5 rounded-full ${user.is_active ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-red-500'}`}></div>
                          <span className={`text-[10px] font-bold uppercase tracking-widest ${user.is_active ? 'text-emerald-600' : 'text-red-600'}`}>
                            {user.is_active ? 'Synchronized' : 'Purged'}
                          </span>
                        </div>
                      </td>
                      <td className="px-10 py-8 text-right">
                        <div className="flex justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                          {editingUser === user.id ? (
                            <>
                              <button onClick={() => handleSave(user.id)} className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center hover:bg-emerald-600 hover:text-white transition-all shadow-sm">
                                <Check size={18} />
                              </button>
                              <button onClick={() => setEditingUser(null)} className="w-12 h-12 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center hover:bg-red-600 hover:text-white transition-all shadow-sm">
                                <X size={18} />
                              </button>
                            </>
                          ) : (
                            <>
                              <button onClick={() => handleEdit(user)} className="w-12 h-12 bg-white border border-slate-50 text-slate-300 hover:text-indigo-600 hover:bg-indigo-50 rounded-2xl flex items-center justify-center transition-all shadow-sm">
                                <Edit2 size={16} />
                              </button>
                              <button onClick={() => handleDelete(user.id)} className="w-12 h-12 bg-white border border-slate-50 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-2xl flex items-center justify-center transition-all shadow-sm">
                                <Trash2 size={16} />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Sync Request Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-md animate-in fade-in duration-300">
          <div className="bg-white w-full max-w-lg rounded-[3rem] shadow-[0_40px_100px_-20px_rgba(0,0,0,0.15)] overflow-hidden animate-in zoom-in-95 duration-300 border border-slate-100 relative">
            <div className="bg-white p-10 text-slate-900 relative border-b border-slate-50">
              <div className="absolute top-0 right-0 w-32 h-32 bg-slate-50 rounded-full blur-3xl"></div>
              <h2 className="text-2xl font-black tracking-tightest uppercase mb-1 flex items-center gap-4">
                <div className="w-10 h-10 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-indigo-600/10">
                  <UserPlus size={22} />
                </div>
                Scale Manifest
              </h2>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] mt-2">Initialize new identity correlation</p>
              <button onClick={() => setShowCreateModal(false)} className="absolute top-8 right-8 text-slate-300 hover:text-slate-900 transition-colors p-2">
                <X size={26} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-10 space-y-6 bg-[#fcfdfe]">
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2"><User size={12} className="text-indigo-500" /> Identity Full Name</label>
                  <input
                    type="text"
                    className="w-full px-6 py-4 bg-white border border-slate-100 rounded-2xl outline-none focus:border-indigo-500 focus:ring-4 focus:ring-sky-500/10 transition-all text-sm font-bold tracking-tight uppercase"
                    value={createForm.full_name}
                    onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                    placeholder="OPERATOR IDENTITY"
                  />
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2"><AtSign size={12} className="text-indigo-500" /> Alias</label>
                    <input
                      type="text"
                      className="w-full px-6 py-4 bg-white border border-slate-100 rounded-2xl outline-none focus:border-indigo-500 focus:ring-4 focus:ring-sky-500/10 transition-all text-sm font-bold uppercase tracking-widest"
                      value={createForm.username}
                      onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
                      required
                      placeholder="ALIAS_ID"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2"><Lock size={12} className="text-indigo-500" /> Entropy</label>
                    <input
                      type="password"
                      className="w-full px-6 py-4 bg-white border border-slate-100 rounded-2xl outline-none focus:border-indigo-500 focus:ring-4 focus:ring-sky-500/10 transition-all text-sm font-bold tracking-widest"
                      value={createForm.password}
                      onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                      required
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2"><Mail size={12} className="text-indigo-500" /> Communication Node</label>
                  <input
                    type="email"
                    className="w-full px-6 py-4 bg-white border border-slate-100 rounded-2xl outline-none focus:border-indigo-500 focus:ring-4 focus:ring-sky-500/10 transition-all text-sm font-bold tracking-tight"
                    value={createForm.email}
                    onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                    required
                    placeholder="identity@corporate.systems"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2"><Shield size={12} className="text-indigo-500" /> Clearance Level</label>
                  <select
                    className="w-full px-6 py-4 bg-white border border-slate-100 rounded-2xl outline-none focus:border-indigo-500 focus:ring-4 focus:ring-sky-500/10 transition-all text-sm font-bold tracking-widest cursor-pointer uppercase"
                    value={createForm.role}
                    onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                  >
                    {ROLES.map(r => (
                      <option key={r.id} value={r.id}>{r.name.toUpperCase()}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-6 flex gap-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-5 bg-slate-50 text-slate-400 hover:text-slate-900 font-bold text-[10px] uppercase tracking-[0.3em] rounded-2xl transition-all"
                >
                  Terminate
                </button>
                <button
                  type="submit"
                  className="flex-[2] px-10 py-5 bg-indigo-600 hover:bg-slate-950 text-white font-bold text-[10px] uppercase tracking-[0.3em] rounded-2xl transition-all shadow-xl shadow-indigo-600/20 active:scale-[0.98]"
                >
                  Synchronize Node
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <footer className="py-14 border-t border-slate-100 text-center">
        <div className="text-[10px] font-bold text-slate-200 uppercase tracking-[0.6em]">
          Identity Governance Control Node • Secure Link Established
        </div>
      </footer>
    </div>
  );
}

export default UserManagement;
