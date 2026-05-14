import { useEffect, useState } from 'react';
import { fetchCustomerSegments, fetchCohortRetention } from '../../api/insightsApi';
import { Users, TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';

const SEGMENT_COLORS = {
  'Champions':         'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  'Loyal Customers':   'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  'Potential Loyalists':'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
  'New Customers':     'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300',
  'Big Spenders':      'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  'At Risk':           'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  'Cannot Lose Them':  'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  'Hibernating':       'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
  'Lost':              'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  'Others':            'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
};

const heatColor = (v) => {
  if (v === null || v === undefined) return 'bg-gray-50 dark:bg-gray-900';
  if (v >= 60) return 'bg-green-600 text-white';
  if (v >= 40) return 'bg-green-400 text-white';
  if (v >= 20) return 'bg-green-200 dark:bg-green-900/40 text-gray-900 dark:text-white';
  if (v >= 10) return 'bg-green-100 dark:bg-green-900/20 text-gray-900 dark:text-gray-200';
  return 'bg-gray-50 dark:bg-gray-900 text-gray-500';
};

export const Customers = () => {
  const [data, setData] = useState(null);
  const [cohorts, setCohorts] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchCustomerSegments(), fetchCohortRetention(12)])
      .then(([rfm, cr]) => { setData(rfm); setCohorts(cr); })
      .catch(() => toast.error('Could not load customer analytics'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading customer analytics...</p>;
  if (data?.error) return <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 rounded-xl p-4 text-sm">{data.error}</div>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center"><Users className="h-6 w-6 mr-2 text-primary-600" /> Customers</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">RFM segmentation + monthly cohort retention. Use this to target marketing and prevent churn.</p>
      </div>

      <section>
        <h2 className="font-semibold text-gray-900 dark:text-white mb-3">RFM segments (as of {data?.as_of})</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900 text-xs uppercase text-gray-500 dark:text-gray-400">
              <tr>
                <th className="px-4 py-3 text-left">Segment</th>
                <th className="px-4 py-3 text-right">Customers</th>
                <th className="px-4 py-3 text-right">Revenue</th>
                <th className="px-4 py-3 text-right">Share</th>
                <th className="px-4 py-3 text-right">Avg recency (d)</th>
                <th className="px-4 py-3 text-right">Avg frequency</th>
                <th className="px-4 py-3 text-right">Avg spend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data?.segments?.map((s) => (
                <tr key={s.segment}>
                  <td className="px-4 py-3"><span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${SEGMENT_COLORS[s.segment] || SEGMENT_COLORS.Others}`}>{s.segment}</span></td>
                  <td className="px-4 py-3 text-right text-gray-900 dark:text-white">{s.customers.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right text-gray-900 dark:text-white">${s.total_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                  <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{s.revenue_share}%</td>
                  <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{s.avg_recency_days}</td>
                  <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{s.avg_frequency}</td>
                  <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">${s.avg_monetary.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="font-semibold text-gray-900 dark:text-white mb-3">Top customers (by total spend)</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900 text-xs uppercase text-gray-500 dark:text-gray-400">
              <tr>
                <th className="px-4 py-3 text-left">Customer ID</th>
                <th className="px-4 py-3 text-left">Segment</th>
                <th className="px-4 py-3 text-right">Recency (d)</th>
                <th className="px-4 py-3 text-right">Orders</th>
                <th className="px-4 py-3 text-right">Total spend</th>
                <th className="px-4 py-3 text-center">R/F/M</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data?.top_customers?.map((c) => (
                <tr key={c.CustomerID}>
                  <td className="px-4 py-3 text-gray-900 dark:text-white font-mono text-xs">{c.CustomerID}</td>
                  <td className="px-4 py-3"><span className={`inline-block px-2 py-0.5 rounded text-xs ${SEGMENT_COLORS[c.segment] || SEGMENT_COLORS.Others}`}>{c.segment}</span></td>
                  <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{c.recency_days}</td>
                  <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{c.frequency}</td>
                  <td className="px-4 py-3 text-right text-gray-900 dark:text-white">${c.monetary.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                  <td className="px-4 py-3 text-center text-gray-700 dark:text-gray-300 text-xs">{c.R}/{c.F}/{c.M}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center"><TrendingUp className="h-5 w-5 mr-2" /> Cohort retention (% of cohort returning)</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
          <table className="text-xs">
            <thead className="bg-gray-50 dark:bg-gray-900 text-gray-500 dark:text-gray-400">
              <tr>
                <th className="px-3 py-2 text-left sticky left-0 bg-gray-50 dark:bg-gray-900">Cohort</th>
                <th className="px-3 py-2 text-right">Size</th>
                {Array.from({ length: cohorts?.max_periods || 12 }, (_, i) => (
                  <th key={i} className="px-2 py-2 text-center w-14">M{i}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {cohorts?.cohorts?.map((c) => (
                <tr key={c.cohort}>
                  <td className="px-3 py-2 text-gray-900 dark:text-white sticky left-0 bg-white dark:bg-gray-800 font-mono">{c.cohort}</td>
                  <td className="px-3 py-2 text-right text-gray-700 dark:text-gray-300">{c.size}</td>
                  {c.retention.map((v, i) => (
                    <td key={i} className={`px-2 py-2 text-center ${heatColor(v)}`}>{v != null ? `${v}%` : ''}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
