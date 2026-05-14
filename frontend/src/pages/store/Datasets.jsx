import { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { listDatasetsApi, uploadDatasetApi, activateDatasetApi, deleteDatasetApi } from '../../api/storeApi';
import { Upload, CheckCircle2, Trash2, Play, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';

export const Datasets = () => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const load = async () => {
    setLoading(true);
    try {
      const res = await listDatasetsApi();
      setDatasets(res.data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onDrop = useCallback(async (files) => {
    if (!files?.length) return;
    setUploading(true);
    setProgress(0);
    try {
      await uploadDatasetApi(files[0], (e) => {
        if (e.total) setProgress(Math.round((e.loaded / e.total) * 100));
      });
      toast.success('Dataset uploaded and processed');
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'application/vnd.ms-excel': ['.xls'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    multiple: false,
    disabled: uploading,
  });

  const activate = async (id) => {
    try {
      await activateDatasetApi(id);
      toast.success('Dataset activated');
      load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Could not activate');
    }
  };

  const remove = async (id) => {
    if (!confirm('Delete this dataset? This cannot be undone.')) return;
    try {
      await deleteDatasetApi(id);
      toast.success('Dataset deleted');
      load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Could not delete');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Datasets</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">Upload retail transaction data to run Market Basket Analysis. CSV or Excel up to 50 MB.</p>
      </div>

      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${isDragActive ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800'}`}>
        <input {...getInputProps()} />
        <Upload className="h-10 w-10 mx-auto text-gray-400 mb-3" />
        {uploading ? (
          <>
            <p className="text-gray-700 dark:text-gray-300 font-medium">Uploading... {progress}%</p>
            <div className="w-full max-w-md mx-auto mt-3 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
              <div className="bg-primary-600 h-2" style={{ width: `${progress}%` }} />
            </div>
          </>
        ) : isDragActive ? (
          <p className="text-primary-600 font-medium">Drop the file here…</p>
        ) : (
          <>
            <p className="text-gray-700 dark:text-gray-300 font-medium">Drag & drop a file here, or click to browse</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Required columns: Invoice, Description, Quantity, UnitPrice. Optional: InvoiceDate, CustomerID, Country.</p>
          </>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {loading ? (
          <p className="p-6 text-gray-500">Loading...</p>
        ) : datasets.length === 0 ? (
          <div className="p-10 text-center text-gray-500">No datasets yet. Upload one above to get started.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900 text-xs uppercase text-gray-500 dark:text-gray-400">
              <tr>
                <th className="px-4 py-3 text-left">Filename</th>
                <th className="px-4 py-3 text-left">Rows</th>
                <th className="px-4 py-3 text-left">Size</th>
                <th className="px-4 py-3 text-left">Uploaded</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {datasets.map((d) => (
                <tr key={d.id}>
                  <td className="px-4 py-3 text-gray-900 dark:text-white">{d.original_filename}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{d.row_count?.toLocaleString() ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{d.file_size_bytes ? `${(d.file_size_bytes / 1024 / 1024).toFixed(2)} MB` : '—'}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300 text-xs">{new Date(d.uploaded_at).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    {d.is_active ? (
                      <span className="inline-flex items-center text-green-600 text-xs"><CheckCircle2 className="h-4 w-4 mr-1" /> Active</span>
                    ) : d.status === 'failed' ? (
                      <span className="inline-flex items-center text-red-600 text-xs"><AlertTriangle className="h-4 w-4 mr-1" /> Failed</span>
                    ) : (
                      <span className="text-gray-500 text-xs capitalize">{d.status}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {!d.is_active && d.status === 'ready' && (
                      <button onClick={() => activate(d.id)} className="text-xs font-medium px-3 py-1 rounded-md bg-primary-50 text-primary-600 hover:bg-primary-100">
                        <Play className="h-3 w-3 inline mr-1" /> Activate
                      </button>
                    )}
                    {!d.is_active && (
                      <button onClick={() => remove(d.id)} className="text-xs font-medium px-3 py-1 rounded-md bg-red-50 text-red-600 hover:bg-red-100">
                        <Trash2 className="h-3 w-3 inline mr-1" /> Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
