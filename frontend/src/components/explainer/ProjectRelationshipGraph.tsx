import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { RelationshipGraphData, RelationshipNode } from '../../types';
import { Share2, AlertTriangle, CheckCircle, Info, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

interface ProjectRelationshipGraphProps {
  workCode: string;
  onSelectProject?: (workCode: string) => void;
}

export const ProjectRelationshipGraph: React.FC<ProjectRelationshipGraphProps> = ({ workCode, onSelectProject }) => {
  const [data, setData] = useState<RelationshipGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<RelationshipNode | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);
    api.getProjectRelationships(workCode)
      .then((res) => {
        if (isMounted) {
          setData(res);
          const target = res.nodes.find((n) => n.is_target) || res.nodes[0] || null;
          setSelectedNode(target);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load relationship graph');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [workCode]);

  if (loading) {
    return (
      <div className="h-72 flex items-center justify-center bg-slate-900/40 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2 text-slate-400 text-xs font-mono">
          <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          Mapping Semantic & Geographic Relationships...
        </div>
      </div>
    );
  }

  if (error || !data || data.nodes.length === 0) {
    return (
      <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-800 text-center text-slate-400 text-xs">
        No direct relationship cluster identified for this record.
      </div>
    );
  }

  // Radial layout calculations
  const width = 640;
  const height = 340;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 110;

  const otherNodes = data.nodes.filter((n) => !n.is_target);
  const targetNode = data.nodes.find((n) => n.is_target) || data.nodes[0];

  const nodePositions = new Map<string, { x: number; y: number }>();
  nodePositions.set(targetNode.id, { x: centerX, y: centerY });

  otherNodes.forEach((node, idx) => {
    const angle = (2 * Math.PI * idx) / Math.max(1, otherNodes.length) - Math.PI / 2;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    nodePositions.set(node.id, { x, y });
  });

  const getRiskColor = (level?: string) => {
    switch (level) {
      case 'CRITICAL': return '#ef4444';
      case 'HIGH': return '#f97316';
      case 'MEDIUM': return '#eab308';
      default: return '#10b981';
    }
  };

  return (
    <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Share2 className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-semibold text-slate-200 tracking-wide">
            PROJECT RELATIONSHIP INTELLIGENCE GRAPH
          </span>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          {data.nodes.length} Connected Nodes • {data.edges.length} Semantic Edges
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* SVG Network Canvas */}
        <div className="lg:col-span-2 relative bg-slate-950/70 rounded-lg border border-slate-800/80 overflow-hidden flex items-center justify-center">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto max-h-[300px]">
            <defs>
              <radialGradient id="targetGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* Connection Edges */}
            {data.edges.map((edge, idx) => {
              const src = nodePositions.get(edge.source) || { x: centerX, y: centerY };
              const tgt = nodePositions.get(edge.target) || { x: centerX, y: centerY };
              const isMatch = edge.relation_type.includes('SIMILAR') || edge.relation_type.includes('DUPLICATE');
              return (
                <g key={`edge-${idx}`}>
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke={isMatch ? '#f97316' : '#475569'}
                    strokeWidth={isMatch ? 2 : 1.2}
                    strokeDasharray={isMatch ? 'none' : '4,3'}
                    strokeOpacity={0.7}
                  />
                  {/* Midpoint Label */}
                  <text
                    x={(src.x + tgt.x) / 2}
                    y={(src.y + tgt.y) / 2 - 4}
                    fill={isMatch ? '#fb923c' : '#94a3b8'}
                    fontSize="9"
                    fontFamily="monospace"
                    textAnchor="middle"
                    className="select-none"
                  >
                    {edge.label}
                  </text>
                </g>
              );
            })}

            {/* Target Central Glow */}
            <circle cx={centerX} cy={centerY} r="35" fill="url(#targetGlow)" />

            {/* Nodes */}
            {data.nodes.map((node) => {
              const pos = nodePositions.get(node.id) || { x: centerX, y: centerY };
              const isSelected = selectedNode?.id === node.id;
              const isTarget = node.is_target;
              const nodeColor = getRiskColor(node.risk_level);

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  className="cursor-pointer transition-transform duration-150 hover:scale-110"
                  onClick={() => {
                    setSelectedNode(node);
                    if (onSelectProject && !node.is_target) {
                      onSelectProject(node.id);
                    }
                  }}
                >
                  <circle
                    r={isTarget ? 18 : 13}
                    fill={isTarget ? '#1e1b4b' : '#0f172a'}
                    stroke={isSelected ? '#38bdf8' : isTarget ? '#818cf8' : nodeColor}
                    strokeWidth={isSelected ? 3 : isTarget ? 2.5 : 1.5}
                  />
                  <circle r={isTarget ? 7 : 5} fill={nodeColor} />
                  <text
                    y={isTarget ? 28 : 22}
                    fill={isSelected ? '#38bdf8' : isTarget ? '#c7d2fe' : '#94a3b8'}
                    fontSize="8.5"
                    fontFamily="monospace"
                    fontWeight={isTarget || isSelected ? 'bold' : 'normal'}
                    textAnchor="middle"
                    className="select-none"
                  >
                    {isTarget ? 'TARGET' : node.id.split('/').pop() || node.id}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Selected Node Inspector */}
        <div className="bg-slate-950/70 rounded-lg border border-slate-800/80 p-3 flex flex-col justify-between text-xs">
          {selectedNode ? (
            <div>
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                <span className="font-mono text-[10px] uppercase tracking-wider text-indigo-400">
                  {selectedNode.is_target ? 'Primary Investigated Record' : 'Connected Peer Record'}
                </span>
                <span
                  className="px-1.5 py-0.5 rounded text-[10px] font-bold font-mono"
                  style={{
                    backgroundColor: `${getRiskColor(selectedNode.risk_level)}20`,
                    color: getRiskColor(selectedNode.risk_level),
                  }}
                >
                  {selectedNode.risk_level || 'LOW'}
                </span>
              </div>

              <div className="space-y-2">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase font-mono">Work ID</div>
                  <div className="font-mono text-slate-200 text-[11px] break-all">{selectedNode.id}</div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-500 uppercase font-mono">Description</div>
                  <div className="text-slate-300 text-[11px] line-clamp-2 leading-relaxed">
                    {selectedNode.title}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Sanctioned</div>
                    <div className="text-slate-200 font-mono text-[11px]">
                      ₹{(selectedNode.sanctioned_amount || 0).toLocaleString('en-IN')}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Geography</div>
                    <div className="text-slate-300 text-[11px] truncate">
                      {selectedNode.district || '—'}, {selectedNode.state || '—'}
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <Link
                  to={`/projects/${encodeURIComponent(selectedNode.id)}`}
                  className="inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300 font-medium"
                >
                  Open Dossier <ExternalLink className="w-3 h-3" />
                </Link>
                {selectedNode.is_target && (
                  <span className="text-[10px] text-emerald-400 font-mono">Active Target</span>
                )}
              </div>
            </div>
          ) : (
            <div className="text-slate-500 text-center py-8">Click a node to inspect relationships</div>
          )}
        </div>
      </div>
    </div>
  );
};
