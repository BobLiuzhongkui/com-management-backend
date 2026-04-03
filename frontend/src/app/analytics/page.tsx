'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';

type Stats = {
  total_tenants: number;
  active_tenants: number;
  total_providers: number;
  active_providers: number;
  total_messages: number;
  total_revenue: number;
  pending_revenue: number;
};

type Message = {
  id: number;
  status: string;
};

type Tenant = {
  id: number;
  status: string;
};

type Provider = {
  id: number;
  provider_type: string;
  status: string;
};

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      router.push('/login');
      return;
    }

    Promise.all([
      api.get('/dashboard/stats'),
      api.get('/messages'),
      api.get('/tenants'),
      api.get('/com-providers'),
    ])
      .then(([statsRes, messagesRes, tenantsRes, providersRes]) => {
        setStats(statsRes.data);
        setMessages(messagesRes.data);
        setTenants(tenantsRes.data);
        setProviders(providersRes.data);
      })
      .catch(() => router.push('/login'))
      .finally(() => setLoading(false));
  }, [router]);

  const providerBreakdown = useMemo(() => {
    const totals: Record<string, number> = {};
    providers.forEach((provider) => {
      totals[provider.provider_type] = (totals[provider.provider_type] || 0) + 1;
    });
    return Object.entries(totals);
  }, [providers]);

  const messageBreakdown = useMemo(() => {
    const totals: Record<string, number> = {};
    messages.forEach((message) => {
      totals[message.status] = (totals[message.status] || 0) + 1;
    });
    return Object.entries(totals);
  }, [messages]);

  if (loading || !stats) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-500 mt-1">Derived from `/dashboard/stats`, `/messages`, `/tenants`, and `/com-providers`</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Messages', value: stats.total_messages, tone: 'text-blue-600' },
          { label: 'Active Providers', value: stats.active_providers, tone: 'text-green-600' },
          { label: 'Active Tenants', value: stats.active_tenants, tone: 'text-orange-600' },
          { label: 'Paid Revenue', value: `$${stats.total_revenue.toFixed(2)}`, tone: 'text-gray-900' },
        ].map((metric) => (
          <div key={metric.label} className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <div className="text-sm text-gray-500">{metric.label}</div>
            <div className={`text-3xl font-bold mt-2 ${metric.tone}`}>{metric.value}</div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Message Status</h3>
          <div className="space-y-3">
            {messageBreakdown.map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 capitalize">{status}</span>
                <span className="text-sm font-semibold text-gray-900">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Provider Types</h3>
          <div className="space-y-3">
            {providerBreakdown.map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{type}</span>
                <span className="text-sm font-semibold text-gray-900">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Tenant Status Snapshot</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {['active', 'suspended', 'inactive'].map((status) => (
            <div key={status} className="rounded-lg border border-gray-200 p-4">
              <div className="text-sm text-gray-500 capitalize">{status}</div>
              <div className="text-2xl font-bold mt-2">
                {tenants.filter((tenant) => tenant.status === status).length}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
