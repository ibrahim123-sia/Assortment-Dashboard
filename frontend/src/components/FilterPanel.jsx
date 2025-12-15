import { useState, useEffect } from 'react';
import { Filter, ChevronDown } from 'lucide-react';
import axios from 'axios';

export const FilterPanel = ({ onFilterChange, loading }) => {
  const [filters, setFilters] = useState({
    country: 'all',
    year: 'all',
    month: 'all',
    hour: 'all',
    min_support: 0.02,
    min_confidence: 0.3,
    sample_size: 10000, // Added sample size
    limit: 50, // Added limit
  });

  const [filterOptions, setFilterOptions] = useState({
    countries: [],
    years: [],
    months: [],
    hours: [],
  });

  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const response = await axios.get('/api/filters');
      if (response.data.success) {
        setFilterOptions(response.data.filters);
      }
    } catch (error) {
      console.error('Error fetching filters:', error);
    }
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    const resetFilters = {
      country: 'all',
      year: 'all',
      month: 'all',
      hour: 'all',
      min_support: 0.02,
      min_confidence: 0.3,
      sample_size: 10000,
      limit: 50,
    };
    setFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Filter className="h-5 w-5 text-gray-500 dark:text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Performance Filters
            </h3>
          </div>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <ChevronDown
              className={`h-5 w-5 text-gray-500 dark:text-gray-400 transition-transform ${
                isOpen ? 'rotate-180' : ''
              }`}
            />
          </button>
        </div>
      </div>

      <div className={`px-4 py-4 space-y-4 ${isOpen ? 'block' : 'hidden'}`}>
        {/* Performance Settings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Sample Size: {filters.sample_size?.toLocaleString()}
            </label>
            <input
              type="range"
              min="1000"
              max="20000"
              step="1000"
              value={filters.sample_size}
              onChange={(e) => handleFilterChange('sample_size', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>1k</span>
              <span>10k</span>
              <span>20k</span>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Lower = Faster, Higher = More detailed
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Results Limit: {filters.limit}
            </label>
            <input
              type="range"
              min="10"
              max="100"
              step="10"
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>10</span>
              <span>50</span>
              <span>100</span>
            </div>
          </div>
        </div>

        {/* Support & Confidence Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Min Support: {filters.min_support.toFixed(3)}
            </label>
            <input
              type="range"
              min="0.001"
              max="0.1"
              step="0.001"
              value={filters.min_support}
              onChange={(e) => handleFilterChange('min_support', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>0.001</span>
              <span>0.05</span>
              <span>0.1</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Min Confidence: {filters.min_confidence.toFixed(2)}
            </label>
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.05"
              value={filters.min_confidence}
              onChange={(e) => handleFilterChange('min_confidence', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>0.1</span>
              <span>0.5</span>
              <span>1.0</span>
            </div>
          </div>
        </div>

        {/* Country, Year, Month, Hour Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Country
            </label>
            <select
              value={filters.country}
              onChange={(e) => handleFilterChange('country', e.target.value)}
              className="input-field"
              disabled={loading}
            >
              <option value="all">All Countries</option>
              {filterOptions.countries?.map((country) => (
                <option key={country} value={country}>
                  {country}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Year
            </label>
            <select
              value={filters.year}
              onChange={(e) => handleFilterChange('year', e.target.value)}
              className="input-field"
              disabled={loading}
            >
              <option value="all">All Years</option>
              {filterOptions.years?.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Month
            </label>
            <select
              value={filters.month}
              onChange={(e) => handleFilterChange('month', e.target.value)}
              className="input-field"
              disabled={loading}
            >
              <option value="all">All Months</option>
              {filterOptions.months?.map((month) => (
                <option key={month.value} value={month.value}>
                  {month.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Hour
            </label>
            <select
              value={filters.hour}
              onChange={(e) => handleFilterChange('hour', e.target.value)}
              className="input-field"
              disabled={loading}
            >
              <option value="all">All Hours</option>
              {filterOptions.hours?.map((hour) => (
                <option key={hour} value={hour}>
                  {hour}:00
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleReset}
            className="btn-secondary px-4 py-2"
            disabled={loading}
          >
            Reset Filters
          </button>
          <button
            onClick={() => onFilterChange(filters)}
            className="btn-primary px-4 py-2"
            disabled={loading}
          >
            {loading ? 'Applying...' : 'Apply Filters'}
          </button>
        </div>
      </div>
    </div>
  );
};