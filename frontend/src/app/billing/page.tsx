'use client';

import { useState } from 'react';

interface Invoice {
  id: string;
  tenant: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'overdue';
  period: string;
  dueDate: string;
}

const mockInvoices: Invoice[] = [
  { id: 'INV-001', tenant: 'Acme Corp', amount: 1299.00, currency: 'USD', status: 'paid', period: '2026-03', dueDate: '2026-03-15' },
  { id: 'INV-002', tenant: 'Widget Inc', amount: 899.50, currency: 'USD', status: 'paid', period: '2026-03', dueDate: '2026-03-15' },
  { id: 'INV-003', tenant: 'Test Corp', amount: 2499.00, currency: 'USD', status: 'pending', period: '2026-03', dueDate: '2026-04-15' },
  { id: 'INV-004', tenant: 'Sample Corp', amount: 599.00, currency: 'USD', status: 'overdue', period: '2026-02', dueDate: '2026-02-15' },
  { id: 'INV-005', tenant: 'Demo Corp', amount: 1799.00, currency: 'USD', status: 'pending', period: '2026-03', dueDate: '2026-04-15' },
];

const statusBadge: Record<string, string> = {
  paid: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  overdue: 'bg-red-100 text-red-700',
};

export default function BillingPage() {
  const [period, setPeriod] = useState('2026-03');

  const filtered = mockInvoices.filter(i => i.period === period);
  const total = filtered.reduce((sum, i) => sum + i.amount, 0);
  const paid = filtered.filter(i => i.status === 'paid').reduce((sum, i) => sum + i.amount, 0);
  const pending = filtered.filter(i => i.status === 'pending').reduce((sum, i) => sum + i.amount, 0);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing</h1>
          <p className="text-sm text-gray-500 mt-1">Manage invoices and payment history</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Invoice
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Total Invoiced</div>
          <div className="text-2xl font-bold text-gray-900">${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          <div className="text-xs text-gray-400 mt-1">{period}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Paid</div>
          <div className="text-2xl font-bold text-green-600">${paid.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          <div className="text-xs text-gray-400 mt-1">{filtered.filter(i => i.status === 'paid').length} invoices</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <div className="text-sm text-gray-500 mb-1">Outstanding</div>
          <div className="text-2xl font-bold text-yellow-600">${pending.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
          <div className="text-xs text-gray-400 mt-1">{filtered.filter(i => i.status !== 'paid').length} invoices</div>
        </div>
      </div>

      {/* Period Filter */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500">Period:</span>
        {['2026-03', '2026-02', '2026-01'].map(p => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              period === p
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Invoice ID</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tenant</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Amount</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Due Date</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((inv) => (
              <tr key={inv.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 text-sm font-mono text-gray-900">{inv.id}</td>
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{inv.tenant}</td>
                <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                  ${inv.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${statusBadge[inv.status]}`}>
                    {inv.status.charAt(0).toUpperCase() + inv.status.slice(1)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{inv.dueDate}</td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button className="px-3 py-1.5 text-xs font-medium text-blue-600 border border-blue-200 rounded-md hover:bg-blue-50 transition-colors">
                      View
                    </button>
                    <button className="px-3 py-1.5 text-xs font-medium text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors">
                      Download
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="py-12 text-center text-gray-500">No invoices found</div>
        )}
      </div>
    </div>
  );
}
