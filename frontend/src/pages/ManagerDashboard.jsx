import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, FileText, MessageSquare, ArrowLeft, UserPlus, Upload, Trash2, LogOut } from 'lucide-react';
import { usersAPI, documentsAPI, chatAPI } from '../services/api';
import { getUser, logout } from '../utils/auth';

function ManagerDashboard() {
    const navigate = useNavigate();
    const [stats, setStats] = useState({
        users: 0,
        documents: 0,
        sessions: 0,
    });
    const [loading, setLoading] = useState(true);
    const [documents, setDocuments] = useState([]);
    const [showDocuments, setShowDocuments] = useState(false);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef(null);
    const user = getUser();

    useEffect(() => {
        loadStats();
        loadDocuments();
    }, []);

    const loadStats = async () => {
        try {
            const [users, documents, sessions] = await Promise.all([
                usersAPI.list(),
                documentsAPI.list(),
                chatAPI.getSessions(),
            ]);
            setStats({
                users: users.length,
                documents: documents.length,
                sessions: sessions.length,
            });
        } catch (err) {
            console.error('Failed to load stats:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadDocuments = async () => {
        try {
            const data = await documentsAPI.list();
            setDocuments(data);
        } catch (err) {
            console.error('Failed to load documents:', err);
        }
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        try {
            await documentsAPI.upload(file);
            await loadDocuments();
            await loadStats();
            alert('Document uploaded and processed successfully!');
        } catch (err) {
            alert('Failed to upload document: ' + (err.response?.data?.detail || err.message));
        } finally {
            setUploading(false);
            fileInputRef.current.value = '';
        }
    };

    const handleDeleteDocument = async (id) => {
        if (!confirm('Are you sure you want to delete this document? This will remove it from the knowledge base.')) return;
        try {
            await documentsAPI.delete(id);
            await loadDocuments();
            await loadStats();
        } catch (err) {
            alert('Failed to delete document');
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            <div className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/chat')}
                            className="text-gray-600 hover:text-gray-800"
                        >
                            <ArrowLeft size={24} />
                        </button>
                        <h1 className="text-2xl font-bold text-gray-800">Manager Dashboard</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-orange-600 rounded-full flex items-center justify-center text-white">
                                {user?.username?.charAt(0).toUpperCase()}
                            </div>
                            <div>
                                <span className="text-gray-700">{user?.username}</span>
                                <span className="ml-2 px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">Manager</span>
                            </div>
                        </div>
                        <button
                            onClick={logout}
                            className="flex items-center gap-1 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                        >
                            <LogOut size={18} />
                            Logout
                        </button>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 py-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-xl shadow">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-500 text-sm">Total Users</p>
                                <p className="text-3xl font-bold text-gray-800">
                                    {loading ? '-' : stats.users}
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                                <Users className="text-blue-600" size={24} />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-500 text-sm">Documents in KB</p>
                                <p className="text-3xl font-bold text-gray-800">
                                    {loading ? '-' : stats.documents}
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                                <FileText className="text-green-600" size={24} />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-500 text-sm">Chat Sessions</p>
                                <p className="text-3xl font-bold text-gray-800">
                                    {loading ? '-' : stats.sessions}
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                                <MessageSquare className="text-purple-600" size={24} />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    <div
                        onClick={() => navigate('/admin/users')}
                        className="bg-white p-6 rounded-xl shadow cursor-pointer hover:shadow-lg transition-shadow"
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                                <UserPlus className="text-blue-600" size={32} />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-gray-800">User Management</h2>
                                <p className="text-gray-500">Create and manage users with specific roles</p>
                            </div>
                        </div>
                    </div>

                    <div
                        onClick={() => setShowDocuments(!showDocuments)}
                        className={`bg-white p-6 rounded-xl shadow cursor-pointer hover:shadow-lg transition-shadow ${showDocuments ? 'ring-2 ring-green-500' : ''}`}
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                                <FileText className="text-green-600" size={32} />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-gray-800">Knowledge Base</h2>
                                <p className="text-gray-500">Upload and manage documents for RAG</p>
                            </div>
                        </div>
                    </div>
                </div>

                {showDocuments && (
                    <div className="bg-white rounded-xl shadow p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-semibold text-gray-800">Document Management</h2>
                            <div>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf,.docx,.txt"
                                    onChange={handleFileUpload}
                                    className="hidden"
                                />
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={uploading}
                                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                                >
                                    <Upload size={18} />
                                    {uploading ? 'Uploading...' : 'Upload Document'}
                                </button>
                            </div>
                        </div>

                        <p className="text-gray-500 mb-4">
                            Upload PDF, DOCX, or TXT files. These documents will be processed and added to the knowledge base for all users to query.
                        </p>

                        <div className="border rounded-lg overflow-hidden">
                            <table className="w-full">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Document</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Chunks</th>
                                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {documents.length === 0 ? (
                                        <tr>
                                            <td colSpan="4" className="px-4 py-8 text-center text-gray-500">
                                                No documents uploaded yet. Upload your first document to enable RAG.
                                            </td>
                                        </tr>
                                    ) : (
                                        documents.map((doc) => (
                                            <tr key={doc.id}>
                                                <td className="px-4 py-3">
                                                    <div className="flex items-center gap-2">
                                                        <FileText size={18} className="text-blue-600" />
                                                        <span className="font-medium">{doc.original_filename}</span>
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${doc.status === 'processed' ? 'bg-green-100 text-green-800' :
                                                        doc.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                                                            'bg-gray-100 text-gray-800'
                                                        }`}>
                                                        {doc.status}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-gray-600">{doc.chunk_count}</td>
                                                <td className="px-4 py-3 text-right">
                                                    <button
                                                        onClick={() => handleDeleteDocument(doc.id)}
                                                        className="text-red-600 hover:text-red-800"
                                                    >
                                                        <Trash2 size={18} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                <div className="mt-8">
                    <div
                        onClick={() => navigate('/chat')}
                        className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 rounded-xl shadow cursor-pointer hover:shadow-lg transition-shadow text-white"
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                                <MessageSquare className="text-white" size={32} />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold">Go to Chat</h2>
                                <p className="text-white/80">Start chatting with the AI Assistant</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ManagerDashboard;
