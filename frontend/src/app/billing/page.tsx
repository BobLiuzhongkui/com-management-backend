'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';

type Billing = {
  id: number;
  tenant_id: number | null;
  amount: number;
  status: 'paid' | 'pending' | 'overdue';
  billing_period: string | null;
  description: string | null;
};

type Tenant = {
  id: number;
  name: string;
};

const statusBadge: Record<string, string> = {
  paid: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  overdue: 'bg-red-100 text-red-700',
};

export default function BillingPage() {
  const [records, setRecords] = useState<Billing[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('all');
  const [form, setForm] = useState({ tenant_id: '', amount: '', status: 'pending', billing_period: '', description: '' });
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      router.push('/login');
      return;
    }

    Promise.all([api.get('/billing'), api.get('/tenants')])
      .then(([billingRes, tenantsRes]) => {
        setRecords(billingRes.data);
        setTenants(tenantsRes.data);
      })
      .catch(() => router.push('/login'))
      .finally(() => setLoading(false));
  }, [router]);

  const periods = useMemo(() => {
    const values = Array.from(new Set(records.map((record) => record.billing_period).filter(Boolean))) as string[];
    return ['all', ...values.sort().reverse()];
  }, [records]);

  const filtered = useMemo(
    () => (period === 'all' ? records : records.filter((record) => record.billing_period === period)),
    [period, records]
  );

  const total = filtered.reduce((sum, record) => sum + record.amount, 0);
  const paid = filtered.filter((record) => record.status === 'paid').reduce((sum, record) => sum + record.amount, 0);
  const outstanding = filtered.filter((record) => record.status !== 'paid').reduce((sum, record) => sum + record.amount, 0);

  const tenantMap = useMemo(
    () => Object.fromEntries(tenants.map((tenant) => [tenant.id, tenant.name])),
    [tenants]
  );

  async function handleCreate() {
    if (!form.amount || !form.billing_period) return;
    try {
      const payload = {
        tenant_id: form.tenant_id ? Number(form.tenant_id) : null,
        amount: Number(form.amount),
        status: form.status,
        billing_period: form.billing_period,
        description: form.description || null,
      };
      const { data } = await api.post('/billing', payload);
      setRecords((current) => [...current, data]);
      setForm({ tenant_id: '', amount: '', status: 'pending', billing_period: '', description: '' });
    } catch (error) {
      console.error(error);
    }
  }

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing</h1>
          <p className="text-sm text-gray-500 mt-1">Live billing data from the `/api/v1/billing` endpoint</p>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-4 grid gap-3 md:grid-cols-5">
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
          type="number"
          value={form.amount}
          onChange={(e) => setForm((current) => ({ ...current, amount: e.target.value }))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
          placeholder="Amount"
        />
        <select
          value={form.status}
          onChange={(e) => setForm((current) => ({ ...current, status: e.target.value }))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="pending">Pending</option>
          <option value="paid">Paid</option>
          <option value="overdue">Overdue</option>
        </select>
        <input
          value={form.billing_period}
          onChange={(e) => setForm((current) => ({ ...current, billing_period: e.target.value }))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
          placeholder="2026-04"
        />
        <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium">
          Create Invoice
        </button>
        <input
          value={form.description}
          onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))}
          className="md:col-span-5 px-3 py-2 border border-gray-200 rounded-lg text-sm"
          placeholder="Description"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Total Invoiced</div>
          <div className="text-2xl font-bold text-gray-900">${total.toFixed(2)}</div>
          <div className="text-xs text-gray-400 mt-1">{period === 'all' ? 'All periods' : period}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Paid</div>
          <div className="text-2xl font-bold text-green-600">${paid.toFixed(2)}</div>
          <div className="text-xs text-gray-400 mt-1">{filtered.filter((record) => record.status === 'paid').length} invoices</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Outstanding</div>
          <div className="text-2xl font-bold text-yellow-600">${outstanding.toFixed(2)}</div>
          <div className="text-xs text-gray-400 mt-1">{filtered.filter((record) => record.status !== 'paid').length} invoices</div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500">Period:</span>
        {periods.map((value) => (
          <button
            key={value}
            onClick={() => setPeriod(value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              period === value
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {value}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">ID</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tenant</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Amount</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Period</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((record) => (
              <tr key={record.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 text-sm font-mono text-gray-900">{record.id}</td>
                <td className="px-6 py-4 text-sm font-medium text-gray-900">
                  {record.tenant_id ? tenantMap[record.tenant_id] || `Tenant #${record.tenant_id}` : 'Unassigned'}
                </td>
                <td className="px-6 py-4 text-sm font-semibold text-gray-900">${record.amount.toFixed(2)}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${statusBadge[record.status]}`}>
                    {record.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{record.billing_period || '-'}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{record.description || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <div className="py-12 text-center text-gray-500">No invoices found</div>}
      </div>
    </div>
  );
}
