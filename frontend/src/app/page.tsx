/**
 * Dashboard page - connected to real API
 */
'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api-client';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) { router.push('/login'); return; }
    api.get('/dashboard/stats')
      .then(r => setStats(r.data))
      .catch(() => router.push('/login'));
  }, []);

  if (!stats) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Overview of your communication system</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <span className="text-sm text-green-600 font-medium">System Online</span>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { label: 'Total Tenants', value: stats.total_tenants, icon: '🏢', color: 'text-blue-600' },
          { label: 'Active Tenants', value: stats.active_tenants, icon: '✅', color: 'text-green-600' },
          { label: 'Com Providers', value: stats.total_providers, icon: '📡', color: 'text-purple-600' },
          { label: 'Active Providers', value: stats.active_providers, icon: '🔗', color: 'text-teal-600' },
          { label: 'Total Messages', value: stats.total_messages, icon: '📨', color: 'text-orange-600' },
          { label: 'Pending Revenue', value: `$${stats.pending_revenue.toFixed(2)}`, icon: '💰', color: 'text-red-600' },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-500">{s.label}</span>
              <span className="text-2xl">{s.icon}</span>
            </div>
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
