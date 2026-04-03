/**
 * Com Providers page - connected to real API
 */
'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';

type Provider = {
  id: number;
  name: string;
  provider_type: string;
  status: string;
  monthly_cost: number;
  api_endpoint: string;
  created_at: string;
};

export default function ComProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [newProvider, setNewProvider] = useState({ name: '', provider_type: 'SMS', api_endpoint: '', monthly_cost: 0 });
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) { router.push('/login'); return; }
    api.get('/com-providers')
      .then(r => setProviders(r.data))
      .catch(() => router.push('/login'))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async () => {
    if (!newProvider.name.trim()) return;
    try {
      const { data } = await api.post('/com-providers', newProvider);
      setProviders(prev => [...prev, data]);
      setNewProvider({ name: '', provider_type: 'SMS', api_endpoint: '', monthly_cost: 0 });
      setShowForm(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/com-providers/${id}`);
      setProviders(prev => prev.filter(p => p.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const filtered = providers.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.provider_type.toLowerCase().includes(search.toLowerCase()) ||
    p.status.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="p-6">Loading...</div>;

  const totalType: Record<string, number> = {};
  providers.forEach(p => { totalType[p.provider_type] = (totalType[p.provider_type] || 0) + 1; });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Com Providers</h1>
          <p className="text-sm text-gray-500 mt-1">Manage communication service providers</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600">
          {showForm ? 'Cancel' : '+ New Provider'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
          <h3 className="font-medium text-gray-700">Add Provider</h3>
          <div className="grid grid-cols-2 gap-3">
            <input value={newProvider.name} onChange={e => setNewProvider(p => ({ ...p, name: e.target.value }))}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm" placeholder="Name" />
            <select value={newProvider.provider_type} onChange={e => setNewProvider(p => ({ ...p, provider_type: e.target.value }))}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
              <option>SMS</option><option>Email</option><option>Voice</option><option>VoIP</option>
            </select>
            <input value={newProvider.api_endpoint} onChange={e => setNewProvider(p => ({ ...p, api_endpoint: e.target.value }))}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm" placeholder="API Endpoint" />
            <input type="number" value={newProvider.monthly_cost} onChange={e => setNewProvider(p => ({ ...p, monthly_cost: Number(e.target.value) }))}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm" placeholder="Monthly Cost" />
          </div>
          <button onClick={handleCreate} className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium">Create</button>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total', value: providers.length, color: 'text-gray-900' },
          { label: 'Active', value: providers.filter(p => p.status === 'active').length, color: 'text-green-600' },
          ...Object.entries(totalType).map(([t, c]) => ({ label: t, value: c, color: 'text-blue-600' })),
        ].slice(0, 4).map((stat, i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-500">{stat.label}</div>
            <div className={`text-3xl font-bold mt-1 ${stat.color}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="relative max-w-sm">
        <input type="text" placeholder="Search providers..." value={search} onChange={e => setSearch(e.target.value)}
          className="w-full pl-4 pr-10 py-2.5 border border-gray-200 rounded-lg text-sm" />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Monthly Cost</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Endpoint</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{p.name}</td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">{p.provider_type}</span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${p.status === 'active' ? 'bg-green-100 text-green-800' : p.status === 'maintenance' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                    {p.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-700">${p.monthly_cost}/mo</td>
                <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-[200px]">{p.api_endpoint}</td>
                <td className="px-6 py-4">
                  <button onClick={() => handleDelete(p.id)} className="px-3 py-1.5 text-xs font-medium text-white bg-red-500 rounded-md hover:bg-red-600">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <div className="py-12 text-center text-gray-500 text-sm">No providers found</div>}
      </div>
    </div>
  );
}
