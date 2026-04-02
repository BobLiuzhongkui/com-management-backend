'use client';

import { useState } from 'react';

const timeRanges = ['Last 7 days', 'Last 30 days', 'Last 90 days', 'This year'];
const metrics = [
  { label: 'Total Messages', value: '12,847', change: '+12.3%', positive: true, icon: '💬' },
  { label: 'Email Delivered', value: '8,234', change: '+8.1%', positive: true, icon: '📧' },
  { label: 'SMS Delivered', value: '4,521', change: '+18.5%', positive: true, icon: '📱' },
  { label: 'Voice Calls', value: '92', change: '-3.2%', positive: false, icon: '📞' },
  { label: 'Avg. Delivery Time', value: '1.2s', change: '-15ms', positive: true, icon: '⚡' },
  { label: 'Success Rate', value: '98.7%', change: '+0.3%', positive: true, icon: '✅' },
];

const hourlyData = [
  { hour: '00:00', email: 12, sms: 8, voice: 1 },
  { hour: '04:00', email: 8, sms: 5, voice: 0 },
  { hour: '08:00', email: 89, sms: 45, voice: 5 },
  { hour: '12:00', email: 156, sms: 89, voice: 12 },
  { hour: '16:00', email: 234, sms: 112, voice: 18 },
  { hour: '20:00', email: 98, sms: 67, voice: 8 },
];

export default function AnalyticsPage() {
  const [range, setRange] = useState('Last 30 days');
  const [activeTab, setActiveTab] = useState<'overview' | 'providers' | 'tenants'>('overview');

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-sm text-gray-500 mt-1">Monitor communication metrics and trends</p>
        </div>
        <select
          value={range}
          onChange={e => setRange(e.target.value)}
          className="px-4 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {timeRanges.map(t => <option key={t}>{t}</option>)}
        </select>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {(['overview', 'providers', 'tenants'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {metrics.map(m => (
          <div key={m.label} className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg">{m.icon}</span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                m.positive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                {m.change}
              </span>
            </div>
            <div className="text-xl font-bold text-gray-900">{m.value}</div>
            <div className="text-xs text-gray-500 mt-1">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Chart Placeholder */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Message Volume by Hour</h3>
        <div className="h-64 flex items-end gap-3">
          {hourlyData.map((d, i) => (
            <div key={d.hour} className="flex-1 flex flex-col items-center gap-1">
              <div className="w-full flex items-end gap-1 h-48">
                <div
                  className="flex-1 bg-blue-400 rounded-t transition-all hover:bg-blue-500"
                  style={{ height: `${(d.email / 250) * 100}%` }}
                  title={`Email: ${d.email}`}
                />
                <div
                  className="flex-1 bg-green-400 rounded-t transition-all hover:bg-green-500"
                  style={{ height: `${(d.sms / 250) * 100}%` }}
                  title={`SMS: ${d.sms}`}
                />
                <div
                  className="flex-1 bg-orange-400 rounded-t transition-all hover:bg-orange-500"
                  style={{ height: `${(d.voice / 250) * 100}%` }}
                  title={`Voice: ${d.voice}`}
                />
              </div>
              <span className="text-xs text-gray-400 mt-1">{d.hour}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center justify-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-400 rounded"></div>
            <span className="text-xs text-gray-500">Email</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-400 rounded"></div>
            <span className="text-xs text-gray-500">SMS</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-orange-400 rounded"></div>
            <span className="text-xs text-gray-500">Voice</span>
          </div>
        </div>
      </div>
    </div>
  );
}
