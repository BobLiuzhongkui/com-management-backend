/**
 * Tenants page - connected to real API
 */
'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';

type Tenant = {
  id: number;
  name: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  status: string;
};

const statusConfig: Record<string, { badge: string; dot: string }> = {
  active: { badge: 'bg-green-100 text-green-800', dot: 'bg-green-500' },
  inactive: { badge: 'bg-red-100 text-red-800', dot: 'bg-red-500' },
  suspended: { badge: 'bg-yellow-100 text-yellow-800', dot: 'bg-yellow-500' },
};

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [newName, setNewName] = useState('');
  const [showForm, setShowForm] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) { router.push('/login'); return; }
    api.get('/tenants')
      .then(r => setTenants(r.data))
      .catch(() => router.push('/login'))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const { data } = await api.post('/tenants', { name: newName, status: 'active' });
      setTenants(prev => [...prev, data]);
      setNewName('');
      setShowForm(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/tenants/${id}`);
      setTenants(prev => prev.filter(t => t.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const filtered = tenants.filter(t =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.status.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tenants</h1>
          <p className="text-sm text-gray-500 mt-1">Manage all communication tenants</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm font-medium">
          {showForm ? 'Cancel' : '+ New Tenant'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 flex gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Name</label>
            <input value={newName} onChange={e => setNewName(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm" placeholder="Tenant name" />
          </div>
          <button onClick={handleCreate} className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium">Create</button>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total', value: tenants.length, color: 'text-gray-900' },
          { label: 'Active', value: tenants.filter(t => t.status === 'active').length, color: 'text-green-600' },
          { label: 'Suspended', value: tenants.filter(t => t.status === 'suspended').length, color: 'text-yellow-600' },
          { label: 'Inactive', value: tenants.filter(t => t.status === 'inactive').length, color: 'text-red-600' },
        ].map((stat, i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-500">{stat.label}</div>
            <div className={`text-3xl font-bold mt-1 ${stat.color}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="relative max-w-sm">
        <input type="text" placeholder="Search tenants..." value={search} onChange={e => setSearch(e.target.value)}
          className="w-full pl-4 pr-10 py-2.5 border border-gray-200 rounded-lg text-sm" />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Contact</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((t) => (
              <tr key={t.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{t.name}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{t.contact_email}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusConfig[t.status]?.badge || 'bg-gray-100 text-gray-800'}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${statusConfig[t.status]?.dot || 'bg-gray-500'}`} />
                    {t.status.charAt(0).toUpperCase() + t.status.slice(1)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <button onClick={() => handleDelete(t.id)} className="px-3 py-1.5 text-xs font-medium text-white bg-red-500 rounded-md hover:bg-red-600">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <div className="py-12 text-center text-gray-500 text-sm">No tenants found</div>}
      </div>
    </div>
  );
}
