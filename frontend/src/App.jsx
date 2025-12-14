// App.jsx
import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './context/ThemeContext';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { AssociationRules } from './pages/AssociationRules';
import { ProductBundles } from './pages/ProductBundles';
import { RevenueAnalysis } from './pages/RevenueAnalysis';
import { SeasonalAnalysis } from './pages/SeasonalAnalysis';
import { NetworkView } from './pages/NetworkView';
import { DataSummary } from './pages/DataSummary'; // Add this import

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <Header toggleSidebar={toggleSidebar} isSidebarOpen={sidebarOpen} />
          
          <div className="flex">
            <Sidebar isOpen={sidebarOpen} />
            
            <main 
              className="flex-1 p-4 md:p-6 lg:p-8 overflow-auto"
              onClick={() => sidebarOpen && closeSidebar()}
            >
              <div className="max-w-7xl mx-auto">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/association-rules" element={<AssociationRules />} />
                  <Route path="/product-bundles" element={<ProductBundles />} />
                  <Route path="/revenue-analysis" element={<RevenueAnalysis />} />
                  <Route path="/seasonal-analysis" element={<SeasonalAnalysis />} />
                  <Route path="/network-view" element={<NetworkView />} />
                  <Route path="/data-summary" element={<DataSummary />} /> {/* Add this route */}
                </Routes>
              </div>
            </main>
          </div>
        </div>
        
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#1f2937',
              color: '#fff',
            },
            success: {
              duration: 3000,
              style: {
                background: '#10b981',
              },
            },
            error: {
              duration: 4000,
              style: {
                background: '#ef4444',
              },
            },
          }}
        />
      </Router>
    </ThemeProvider>
  );
}

export default App;