import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createStoreApi } from '../../api/adminApi';
import toast from 'react-hot-toast';

export const StoreForm = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    description: '',
    manager_email: '',
    manager_full_name: '',
    theme_mode: 'light',
    brand_primary_color: '#2563eb',
  });
  const [submitting, setSubmitting] = useState(false);
  const [tempPassword, setTempPassword] = useState(null);

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await createStoreApi(form);
      if (res.data.temp_password) {
        setTempPassword(res.data.temp_password);
        toast.error('Email could not be sent — copy the password below.');
      } else {
        toast.success('Store created. Credentials emailed to manager.');
        navigate('/admin/stores');
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Could not create store');
    } finally {
      setSubmitting(false);
    }
  };

  if (tempPassword) {
    return (
      <div className="max-w-xl mx-auto bg-white dark:bg-gray-800 rounded-xl p-8 border border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-bold text-red-600 mb-2">Save these credentials</h2>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          The system could not deliver the welcome email. Copy this temporary password and send it to the manager manually.
        </p>
        <div className="bg-yellow-50 border border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800 rounded p-4 mb-4">
          <p><strong>Email:</strong> {form.manager_email}</p>
          <p><strong>Temporary password:</strong> <code className="bg-white dark:bg-gray-900 px-2 py-1 rounded">{tempPassword}</code></p>
        </div>
        <button onClick={() => navigate('/admin/stores')} className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg">
          Done
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Create a new store</h1>
      <form onSubmit={handleSubmit} className="space-y-4 bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Store name *</label>
          <input value={form.name} onChange={update('name')} required
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
          <textarea value={form.description} onChange={update('description')} rows={2}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Manager email *</label>
            <input type="email" value={form.manager_email} onChange={update('manager_email')} required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Manager name</label>
            <input value={form.manager_full_name} onChange={update('manager_full_name')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Theme</label>
            <select value={form.theme_mode} onChange={update('theme_mode')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Brand color</label>
            <input type="color" value={form.brand_primary_color} onChange={update('brand_primary_color')}
              className="w-full h-10 border border-gray-300 dark:border-gray-600 rounded-lg" />
          </div>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/40 p-3 rounded">
          A welcome email with a temporary password will be sent to the manager.
        </div>
        <div className="flex justify-end space-x-2">
          <button type="button" onClick={() => navigate('/admin/stores')} className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">Cancel</button>
          <button type="submit" disabled={submitting} className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg disabled:opacity-60">
            {submitting ? 'Creating...' : 'Create store & send email'}
          </button>
        </div>
      </form>
    </div>
  );
};
