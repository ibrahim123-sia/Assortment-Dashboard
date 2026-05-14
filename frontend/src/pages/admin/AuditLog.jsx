import { useEffect, useState } from 'react';
import { auditLogApi } from '../../api/adminApi';

export const AuditLog = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ action: '', target_type: '' });

  const load = async () => {
    setLoading(true);
    try {
      const params = { per_page: 100 };
      if (filters.action) params.action = filters.action;
      if (filters.target_type) params.target_type = filters.target_type;
      const res = await auditLogApi(params);
      setItems(res.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Audit Log</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">All admin and security events</p>
      </div>
      <div className="flex space-x-3">
        <input value={filters.action} onChange={(e) => setFilters({ ...filters, action: e.target.value })} placeholder="Filter by action"
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm" />
        <input value={filters.target_type} onChange={(e) => setFilters({ ...filters, target_type: e.target.value })} placeholder="Target type"
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm" />
        <button onClick={load} className="bg-primary-600 hover:bg-primary-700 text-white text-sm px-4 py-2 rounded-lg">Apply</button>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
        {loading ? <p className="p-6 text-gray-500">Loading...</p> : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900 text-xs uppercase text-gray-500 dark:text-gray-400">
              <tr>
                <th className="px-3 py-2 text-left">When</th>
                <th className="px-3 py-2 text-left">Actor</th>
                <th className="px-3 py-2 text-left">Action</th>
                <th className="px-3 py-2 text-left">Target</th>
                <th className="px-3 py-2 text-left">IP</th>
                <th className="px-3 py-2 text-left">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {items.map((a) => (
                <tr key={a.id} className="text-gray-700 dark:text-gray-300">
                  <td className="px-3 py-2 whitespace-nowrap text-xs">{new Date(a.created_at).toLocaleString()}</td>
                  <td className="px-3 py-2">{a.actor_email || '—'}</td>
                  <td className="px-3 py-2 font-mono text-xs">{a.action}</td>
                  <td className="px-3 py-2">{a.target_type ? `${a.target_type}:${a.target_id}` : '—'}</td>
                  <td className="px-3 py-2 text-xs">{a.ip_address || '—'}</td>
                  <td className="px-3 py-2 text-xs max-w-xs truncate">{a.metadata ? JSON.stringify(a.metadata) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
