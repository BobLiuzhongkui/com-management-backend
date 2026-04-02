/**
 * Com Providers page - From Figma design
 */
'use client';

import { useState } from 'react';

interface ComProvider {
  id: string;
  name: string;
  type: 'Email' | 'SMS' | 'Voice';
  status: 'Active' | 'Inactive';
  created_at: string;
}

const mockData: ComProvider[] = [
  { id: '1', name: 'Demo Corp', type: 'Email', status: 'Active', created_at: '2025-02-11' },
];

export default function ComProvidersPage() {
  const [search, setSearch] = useState('');
  const [selectedFields, setSelectedFields] = useState<string[]>([]);
  const [allSelected, setAllSelected] = useState(false);

  const showTotal = selectedFields.length > 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Com Providers</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your communication service providers</p>
      </div>

      {/* Stats bar - shows when filters/selection active */}
      {(showTotal || allSelected) && (
        <div className="bg-white rounded-lg border border-gray-200 p-3">
          <span className="text-sm">Total: <strong>1</strong></span>
        </div>
      )}

      {/* Toolbar */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <input
            type="text"
            placeholder="Search providers..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-4 pr-10 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white"
          />
          <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <button className="px-4 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
          Refresh
        </button>
        <button className="px-4 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Provider
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="w-10 px-6 py-3">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={e => setAllSelected(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-blue-500 focus:ring-blue-500"
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Created Date</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {mockData.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4">
                  <input
                    type="checkbox"
                    checked={selectedFields.includes(p.id)}
                    onChange={() => {}}
                    className="w-4 h-4 rounded border-gray-300 text-blue-500 focus:ring-blue-500"
                  />
                </td>
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{p.name}</td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">{p.type}</span>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">{p.status}</span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{p.created_at}</td>
                <td className="px-6 py-4">
                  <button className="px-4 py-1.5 text-xs font-medium text-white bg-blue-500 rounded-md hover:bg-blue-600 transition-colors">
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {mockData.length === 0 && (
          <div className="py-12 text-center text-gray-500 text-sm">No providers found</div>
        )}
      </div>
    </div>
  );
}
