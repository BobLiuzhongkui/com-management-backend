'use client';

import { useState } from 'react';

interface ComMessage {
  id: string;
  tenant: string;
  provider: string;
  type: 'SMS' | 'Email' | 'Voice';
  status: 'sent' | 'delivered' | 'failed' | 'pending';
  to: string;
  content: string;
  timestamp: string;
}

const mockMessages: ComMessage[] = [
  { id: '1', tenant: 'Acme Corp', provider: 'SMS Gateway A', type: 'SMS', status: 'delivered', to: '+1234567890', content: 'Your verification code is 123456', timestamp: '2026-04-02 12:05' },
  { id: '2', tenant: 'Widget Inc', provider: 'Email Provider B', type: 'Email', status: 'sent', to: 'user@widget.inc', content: 'Welcome to our platform!', timestamp: '2026-04-02 11:58' },
  { id: '3', tenant: 'Test Corp', provider: 'Voice Gateway C', type: 'Voice', status: 'failed', to: '+0987654321', content: 'Automated notification call', timestamp: '2026-04-02 11:45' },
  { id: '4', tenant: 'Sample Corp', provider: 'SMS Gateway A', type: 'SMS', status: 'pending', to: '+1122334455', content: 'Your order has shipped', timestamp: '2026-04-02 11:30' },
  { id: '5', tenant: 'Demo Corp', provider: 'Email Provider B', type: 'Email', status: 'delivered', to: 'admin@demo.com', content: 'Monthly report attached', timestamp: '2026-04-02 11:15' },
];

const statusBadge: Record<string, string> = {
  delivered: 'bg-green-100 text-green-700',
  sent: 'bg-blue-100 text-blue-700',
  failed: 'bg-red-100 text-red-700',
  pending: 'bg-yellow-100 text-yellow-700',
};

export default function ComPage() {
  const [filter, setFilter] = useState('all');

  const filtered = filter === 'all' ? mockMessages : mockMessages.filter(m => m.status === filter);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Com Messages</h1>
        <p className="text-sm text-gray-500 mt-1">Send and track communication messages across all providers</p>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3">
        {['SMS', 'Email', 'Voice'].map(type => (
          <button key={type} className="flex-1 bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all text-center group">
            <div className="text-2xl mb-1">
              {type === 'SMS' ? '💬' : type === 'Email' ? '📧' : '📞'}
            </div>
            <div className="text-sm font-medium text-gray-700 group-hover:text-blue-600">Send {type}</div>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'sent', 'delivered', 'failed', 'pending'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Messages Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tenant</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">To</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Content</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((m) => (
              <tr key={m.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4">
                  <span className="text-lg">
                    {m.type === 'SMS' ? '💬' : m.type === 'Email' ? '📧' : '📞'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{m.tenant}</td>
                <td className="px-6 py-4 text-sm text-gray-500 font-mono">{m.to}</td>
                <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">{m.content}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${statusBadge[m.status]}`}>
                    {m.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-400 whitespace-nowrap">{m.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="py-12 text-center text-gray-500">No messages found</div>
        )}
      </div>
    </div>
  );
}
