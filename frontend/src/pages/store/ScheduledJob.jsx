import { useEffect, useState } from 'react';
import { getScheduledJobApi, updateScheduledJobApi } from '../../api/storeApi';
import toast from 'react-hot-toast';

export const ScheduledJob = () => {
  const [job, setJob] = useState({ is_enabled: false, cron_expression: '0 2 * * *', email_summary_to: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getScheduledJobApi().then((r) => {
      if (r.data) setJob(r.data);
    }).finally(() => setLoading(false));
  }, []);

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await updateScheduledJobApi(job);
      setJob(res.data);
      toast.success('Schedule updated');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Scheduled Re-analysis</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">Re-run MBA on a cron schedule and email a summary.</p>
      </div>
      <form onSubmit={save} className="space-y-4 bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
        <label className="flex items-center space-x-2">
          <input type="checkbox" checked={job.is_enabled} onChange={(e) => setJob({ ...job, is_enabled: e.target.checked })} />
          <span className="text-sm text-gray-700 dark:text-gray-300">Enable nightly re-analysis</span>
        </label>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cron expression (UTC)</label>
          <input value={job.cron_expression} onChange={(e) => setJob({ ...job, cron_expression: e.target.value })} placeholder="0 2 * * *"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white font-mono text-sm" />
          <p className="text-xs text-gray-500 mt-1">Example: <code>0 2 * * *</code> = every day at 02:00 UTC</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Summary recipient (defaults to manager)</label>
          <input type="email" value={job.email_summary_to || ''} onChange={(e) => setJob({ ...job, email_summary_to: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
        </div>
        {job.last_run_at && (
          <div className="text-xs bg-gray-50 dark:bg-gray-900/40 p-3 rounded">
            <p>Last run: {new Date(job.last_run_at).toLocaleString()} — <strong>{job.last_run_status}</strong></p>
            {job.last_run_error && <p className="text-red-600 mt-1">{job.last_run_error}</p>}
          </div>
        )}
        <div className="flex justify-end">
          <button type="submit" disabled={saving} className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg disabled:opacity-60">
            {saving ? 'Saving...' : 'Save schedule'}
          </button>
        </div>
      </form>
    </div>
  );
};
