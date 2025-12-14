import { useState, useRef, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { ZoomIn, ZoomOut, RefreshCw } from 'lucide-react';

export const NetworkGraph = ({ data, loading, height = 500 }) => {
  const fgRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height });
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());

  useEffect(() => {
    const updateDimensions = () => {
      const container = fgRef.current?.parentElement;
      if (container) {
        setDimensions({
          width: container.clientWidth,
          height,
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, [height]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[500px] bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Loading network graph...
          </p>
        </div>
      </div>
    );
  }

  if (!data?.nodes || data.nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="text-gray-400 dark:text-gray-500 mb-4">
          <RefreshCw className="h-12 w-12 mx-auto" />
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          No network data available. Try adjusting your filters.
        </p>
      </div>
    );
  }

  const handleNodeHover = (node) => {
    if (node) {
      const connectedNodes = new Set();
      const connectedLinks = new Set();

      // Find connected nodes
      data.links.forEach((link) => {
        if (link.source.id === node.id || link.target.id === node.id) {
          connectedLinks.add(link);
          connectedNodes.add(link.source);
          connectedNodes.add(link.target);
        }
      });

      setHighlightNodes(connectedNodes);
      setHighlightLinks(connectedLinks);
    } else {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  };

  const handleZoomIn = () => {
    if (fgRef.current) {
      fgRef.current.zoom(1.2, 100);
    }
  };

  const handleZoomOut = () => {
    if (fgRef.current) {
      fgRef.current.zoom(0.8, 100);
    }
  };

  const handleReset = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400);
    }
  };

  return (
    <div className="relative bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="absolute top-4 right-4 z-10 flex space-x-2">
        <button
          onClick={handleZoomIn}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        </button>
        <button
          onClick={handleReset}
          className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          title="Reset View"
        >
          <RefreshCw className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        </button>
      </div>

      <ForceGraph2D
        ref={fgRef}
        graphData={data}
        width={dimensions.width}
        height={dimensions.height}
        nodeLabel={(node) => node.id}
        nodeColor={(node) => {
          if (highlightNodes.has(node)) return '#3b82f6';
          return '#6b7280';
        }}
        nodeRelSize={6}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const label = node.id;
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = highlightNodes.has(node) ? '#3b82f6' : '#6b7280';
          ctx.fillText(label, node.x, node.y + 8);
        }}
        linkColor={(link) => {
          if (highlightLinks.has(link)) return '#3b82f6';
          return '#9ca3af';
        }}
        linkWidth={(link) => (highlightLinks.has(link) ? 2 : 1)}
        onNodeHover={handleNodeHover}
        cooldownTime={1000}
        d3VelocityDecay={0.3}
        warmupTicks={20}
      />

      <div className="absolute bottom-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-3">
        <div className="text-xs text-gray-600 dark:text-gray-400">
          <div className="flex items-center mb-1">
            <div className="w-3 h-3 rounded-full bg-gray-500 mr-2"></div>
            <span>Product Node</span>
          </div>
          <div className="flex items-center">
            <div className="w-8 h-0.5 bg-gray-400 mr-2"></div>
            <span>Association Link</span>
          </div>
        </div>
      </div>
    </div>
  );
};