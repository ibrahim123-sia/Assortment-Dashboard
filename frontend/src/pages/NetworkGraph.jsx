import React, { useState, useEffect, useRef } from 'react';
import { useApi } from '../context/ApiContext';
import { 
  Network, 
  ZoomIn, 
  ZoomOut, 
  Search, 
  Filter,
  Download,
  Share2,
  MousePointer,
  GitBranch
} from 'lucide-react';

const NetworkGraph = () => {
  const { getNetworkGraphData, loading } = useApi();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [viewMode, setViewMode] = useState('force');
  const canvasRef = useRef(null);

  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    const data = await getNetworkGraphData({});
    setGraphData(data);
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5));

  const getStrengthColor = (strength) => {
    switch(strength) {
      case 'strong': return 'stroke-red-500';
      case 'medium': return 'stroke-yellow-500';
      case 'weak': return 'stroke-blue-300';
      default: return 'stroke-gray-300';
    }
  };

  const getStrengthLabel = (strength) => {
    switch(strength) {
      case 'strong': return 'High Association';
      case 'medium': return 'Medium Association';
      case 'weak': return 'Low Association';
      default: return 'Unknown';
    }
  };

  const getNodeColor = (group) => {
    const colors = [
      'bg-blue-500 border-blue-600',
      'bg-green-500 border-green-600',
      'bg-purple-500 border-purple-600',
      'bg-yellow-500 border-yellow-600',
      'bg-pink-500 border-pink-600'
    ];
    return colors[(group - 1) % colors.length];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            <Network className="mr-3" size={28} />
            Network Graph Visualization
          </h2>
          <p className="text-gray-600 mt-1">
            Interactive product association network - Nodes represent products, edges show association strength
          </p>
        </div>
        <div className="flex space-x-3 mt-4 md:mt-0">
          <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center">
            <Download size={18} className="mr-2" />
            Export
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center">
            <Share2 size={18} className="mr-2" />
            Share
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <button
                onClick={handleZoomOut}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <ZoomOut size={20} />
              </button>
              <span className="text-sm font-medium">Zoom: {zoom.toFixed(1)}x</span>
              <button
                onClick={handleZoomIn}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <ZoomIn size={20} />
              </button>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setViewMode('force')}
                className={`px-3 py-1 rounded-lg ${viewMode === 'force' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
              >
                Force Layout
              </button>
              <button
                onClick={() => setViewMode('circular')}
                className={`px-3 py-1 rounded-lg ${viewMode === 'circular' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
              >
                Circular
              </button>
              <button
                onClick={() => setViewMode('hierarchical')}
                className={`px-3 py-1 rounded-lg ${viewMode === 'hierarchical' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
              >
                Hierarchical
              </button>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-sm">Strong Link</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <span className="text-sm">Medium Link</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-blue-300"></div>
              <span className="text-sm">Weak Link</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Graph Visualization */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm p-6 h-[600px] relative">
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                  <p className="mt-4 text-gray-600">Loading network graph...</p>
                </div>
              </div>
            ) : (
              <div className="relative w-full h-full border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                {/* Simulated Network Graph */}
                <div className="absolute inset-0" style={{ transform: `scale(${zoom})` }}>
                  {/* Links */}
                  {graphData.links.map((link, index) => (
                    <div
                      key={index}
                      className={`absolute ${getStrengthColor(link.strength)}`}
                      style={{
                        top: `${20 + index * 15}%`,
                        left: '20%',
                        width: '60%',
                        height: '2px',
                        opacity: link.strength === 'strong' ? 0.8 : link.strength === 'medium' ? 0.6 : 0.4
                      }}
                    >
                      <div className="absolute -top-2 -right-2 w-4 h-4 bg-white border rounded-full flex items-center justify-center">
                        <GitBranch size={10} />
                      </div>
                    </div>
                  ))}

                  {/* Nodes */}
                  {graphData.nodes.map((node, index) => {
                    const row = Math.floor(index / 4);
                    const col = index % 4;
                    const top = 15 + row * 30;
                    const left = 10 + col * 25;
                    
                    return (
                      <div
                        key={node.id}
                        onClick={() => setSelectedNode(node)}
                        className={`absolute cursor-pointer transform transition-transform hover:scale-110 ${getNodeColor(node.group)} border-2 rounded-full flex items-center justify-center text-white font-semibold shadow-lg`}
                        style={{
                          top: `${top}%`,
                          left: `${left}%`,
                          width: `${node.size}px`,
                          height: `${node.size}px`
                        }}
                      >
                        {node.id.charAt(0)}
                        {selectedNode?.id === node.id && (
                          <div className="absolute -top-2 -right-2 w-6 h-6 bg-yellow-400 rounded-full border-2 border-white animate-pulse"></div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Instructions */}
                <div className="absolute bottom-4 left-4 bg-white/80 backdrop-blur-sm p-3 rounded-lg border">
                  <div className="flex items-center text-sm text-gray-600">
                    <MousePointer size={16} className="mr-2" />
                    Click on nodes to see details
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          {/* Selected Node Info */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">
              {selectedNode ? 'Node Details' : 'Select a Node'}
            </h3>
            {selectedNode ? (
              <div className="space-y-4">
                <div className="flex items-center">
                  <div className={`w-12 h-12 ${getNodeColor(selectedNode.group)} rounded-full flex items-center justify-center text-white font-bold text-lg mr-4`}>
                    {selectedNode.id.charAt(0)}
                  </div>
                  <div>
                    <h4 className="font-bold text-lg">{selectedNode.id}</h4>
                    <p className="text-gray-600">Group {selectedNode.group}</p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Monthly Sales:</span>
                    <span className="font-semibold">${selectedNode.sales?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Connections:</span>
                    <span className="font-semibold">
                      {graphData.links.filter(l => l.source === selectedNode.id || l.target === selectedNode.id).length}
                    </span>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium mb-2">Connected Products:</h5>
                  <div className="flex flex-wrap gap-2">
                    {graphData.links
                      .filter(l => l.source === selectedNode.id || l.target === selectedNode.id)
                      .map((link, index) => {
                        const connectedNode = link.source === selectedNode.id ? link.target : link.source;
                        return (
                          <span
                            key={index}
                            className={`px-3 py-1 rounded-full text-sm ${getStrengthColor(link.strength).replace('stroke-', 'bg-').replace('500', '100').replace('300', '100')} ${getStrengthColor(link.strength).replace('stroke-', 'text-')}`}
                          >
                            {connectedNode}
                          </span>
                        );
                      })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Network size={48} className="mx-auto mb-4 opacity-50" />
                <p>Click on any product node to see details</p>
              </div>
            )}
          </div>

          {/* Statistics */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4">Network Statistics</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Nodes:</span>
                <span className="font-bold">{graphData.nodes.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Links:</span>
                <span className="font-bold">{graphData.links.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Strong Associations:</span>
                <span className="font-bold text-red-600">
                  {graphData.links.filter(l => l.strength === 'strong').length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Network Density:</span>
                <span className="font-bold">0.42</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkGraph;