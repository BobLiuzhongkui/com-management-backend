'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';

type Message = {
  id: number;
  tenant_id: number | null;
  from_number: string | null;
  to_number: string | null;
  content: string | null;
  direction: string;
  status: 'sent' | 'delivered' | 'failed' | 'pending';
};

type Tenant = {
  id: number;
  name: string;
};

const statusBadge: Record<string, string> = {
  delivered: 'bg-green-100 text-green-700',
  sent: 'bg-blue-100 text-blue-700',
  failed: 'bg-red-100 text-red-700',
  pending: 'bg-yellow-100 text-yellow-700',
};

export default function ComPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ tenant_id: '', from_number: '', to_number: '', content: '' });
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      router.push('/login');
      return;
    }

    Promise.all([api.get('/messages'), api.get('/tenants')])
      .then(([messagesRes, tenantsRes]) => {
        setMessages(messagesRes.data);
        setTenants(tenantsRes.data);
      })
      .catch(() => router.push('/login'))
      .finally(() => setLoading(false));
  }, [router]);

  const filtered = useMemo(
    () => (filter === 'all' ? messages : messages.filter((message) => message.status === filter)),
    [filter, messages]
  );

  const tenantMap = useMemo(
    () => Object.fromEntries(tenants.map((tenant) => [tenant.id, tenant.name])),
    [tenants]
  );

  async function handleCreate() {
    if (!form.to_number.trim() || !form.content.trim()) return;
    const payload = {
      tenant_id: form.tenant_id ? Number(form.tenant_id) : null,
      from_number: form.from_number || null,
      to_number: form.to_number,
      content: form.content,
      direction: 'outbound',
      status: 'sent',
    };

    try {
      const { data } = await api.post('/messages', payload);
      setMessages((current) => [...current, data]);
      setForm({ tenant_id: '', from_number: '', to_number: '', content: '' });
    } catch (error) {
      console.error(error);
    }
  }

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Com Messages</h1>
        <p className="text-sm text-gray-500 mt-1">Track real messages from the `/api/v1/messages` endpoint</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-4 grid gap-3 md:grid-cols-4">
        <select
          value={form.tenant_id}
          onChange={(e) => setForm((current) => ({ ...current, tenant_id: e.target.value }))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">No tenant</option>
          {tenants.map((tenant) => (
            <option key={tenant.id} value={tenant.id}>
              {tenant.name}
            </option>
          ))}
        </select>
        <input
          value={form.from_number}
          onChange={(e) => setForm((current) => ({ ...current, from_number: e.target.value }))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
          placeholder="From"
        />
        <input
          value={form.to_number}
          onChange={(e) => setForm((current) => ({ ...current, to_number: e.target.value }))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
          placeholder="To"
        />
        <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium">
          Send Message
        </button>
        <textarea
          value={form.content}
          onChange={(e) => setForm((current) => ({ ...current, content: e.target.value }))}
          className="md:col-span-4 px-3 py-2 border border-gray-200 rounded-lg text-sm min-h-24"
          placeholder="Message content"
        />
      </div>

      <div className="flex gap-2">
        {['all', 'sent', 'delivered', 'failed', 'pending'].map((value) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              filter === value
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {value.charAt(0).toUpperCase() + value.slice(1)}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tenant</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">From</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">To</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Content</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((message) => (
              <tr key={message.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">
                  {message.tenant_id ? tenantMap[message.tenant_id] || `Tenant #${message.tenant_id}` : 'Unassigned'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 font-mono">{message.from_number || '-'}</td>
                <td className="px-6 py-4 text-sm text-gray-500 font-mono">{message.to_number || '-'}</td>
                <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">{message.content || '-'}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${statusBadge[message.status] || 'bg-gray-100 text-gray-700'}`}>
                    {message.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <div className="py-12 text-center text-gray-500">No messages found</div>}
      </div>
    </div>
  );
}
