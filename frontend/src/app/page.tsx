/**
 * Dashboard page - 首页概览
 */
'use client';

const stats = [
  { label: 'Total Tenants', value: '1', icon: '🏢', color: 'text-blue-600' },
  { label: 'Active Com Providers', value: '1', icon: '📡', color: 'text-green-600' },
  { label: 'Total Messages', value: '0', icon: '📨', color: 'text-purple-600' },
  { label: 'Active Users', value: '12', icon: '👥', color: 'text-orange-600' },
  { label: 'System Uptime', value: '99.9%', icon: '⚡', color: 'text-teal-600' },
  { label: 'Open Alerts', value: '3', icon: '🔔', color: 'text-red-600' },
];

export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
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

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-500">{s.label}</span>
              <span className="text-2xl">{s.icon}</span>
            </div>
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {[
            { time: '2 min ago', event: 'New tenant created: Acme Corp', type: 'info' },
            { time: '15 min ago', event: 'Com Provider SMS gateway activated', type: 'success' },
            { time: '1 hour ago', event: 'Alert: High message queue on VoipProvider', type: 'warning' },
            { time: '3 hours ago', event: 'System backup completed successfully', type: 'success' },
            { time: '5 hours ago', event: 'Billing cycle report generated', type: 'info' },
          ].map((item, i) => (
            <div key={i} className="px-6 py-3 flex items-center gap-3">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                item.type === 'success' ? 'bg-green-500' :
                item.type === 'warning' ? 'bg-yellow-500' :
                item.type === 'error' ? 'bg-red-500' :
                'bg-blue-500'
              }`} />
              <span className="text-sm text-gray-700 flex-1">{item.event}</span>
              <span className="text-xs text-gray-400 whitespace-nowrap">{item.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
