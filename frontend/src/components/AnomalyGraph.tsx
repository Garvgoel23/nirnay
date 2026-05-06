import React, { useRef, useEffect, useCallback } from 'react';
import { Anomaly } from '../types';

interface AnomalyGraphProps {
  anomalies: Anomaly[];
}

interface GraphNode {
  id: string;
  label: string;
  type: 'bidder' | 'entity';
  x?: number;
  y?: number;
}

interface GraphLink {
  source: string;
  target: string;
  color: string;
  anomalyType: string;
}

const edgeColors: Record<string, string> = {
  SHARED_ENTITY_DETECTED: '#ef4444',
  RECYCLED_DOCUMENT_SUSPECTED: '#f97316',
  COORDINATED_BIDDING_SUSPECTED: '#a855f7',
};

const AnomalyGraph: React.FC<AnomalyGraphProps> = ({ anomalies }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = React.useState<{ x: number; y: number; text: string } | null>(null);

  // Build graph data
  const { nodes, links } = React.useMemo(() => {
    const nodesMap = new Map<string, GraphNode>();
    const links: GraphLink[] = [];

    anomalies.forEach(a => {
      a.bidder_ids.forEach(bid => {
        if (!nodesMap.has(bid)) {
          nodesMap.set(bid, { id: bid, label: bid, type: 'bidder' });
        }
      });

      // Create entity nodes from evidence
      const evidenceValues = a.evidence?.shared_values || [];
      evidenceValues.forEach((val: string) => {
        if (!nodesMap.has(val)) {
          nodesMap.set(val, { id: val, label: val.length > 15 ? val.slice(0, 15) + '...' : val, type: 'entity' });
        }
        a.bidder_ids.forEach(bid => {
          links.push({ source: bid, target: val, color: edgeColors[a.anomaly_type] || '#94a3b8', anomalyType: a.anomaly_type });
        });
      });

      // If no entity nodes, connect bidders directly
      if (evidenceValues.length === 0 && a.bidder_ids.length >= 2) {
        for (let i = 0; i < a.bidder_ids.length - 1; i++) {
          links.push({ source: a.bidder_ids[i], target: a.bidder_ids[i + 1], color: edgeColors[a.anomaly_type] || '#94a3b8', anomalyType: a.anomaly_type });
        }
      }
    });

    // Position nodes in a circle
    const nodeArr = Array.from(nodesMap.values());
    const cx = 300, cy = 200, r = 150;
    nodeArr.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / nodeArr.length;
      n.x = cx + r * Math.cos(angle);
      n.y = cy + r * Math.sin(angle);
    });

    return { nodes: nodeArr, links };
  }, [anomalies]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    // Draw links
    links.forEach(l => {
      const s = nodeMap.get(l.source);
      const t = nodeMap.get(l.target);
      if (!s || !t) return;
      ctx.beginPath();
      ctx.moveTo(s.x!, s.y!);
      ctx.lineTo(t.x!, t.y!);
      ctx.strokeStyle = l.color;
      ctx.lineWidth = 2;
      ctx.stroke();
    });

    // Draw nodes
    nodes.forEach(n => {
      ctx.beginPath();
      if (n.type === 'bidder') {
        ctx.arc(n.x!, n.y!, 20, 0, 2 * Math.PI);
        ctx.fillStyle = '#4f46e5';
      } else {
        ctx.rect(n.x! - 10, n.y! - 10, 20, 20);
        ctx.fillStyle = '#94a3b8';
      }
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Label
      ctx.fillStyle = '#1e293b';
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(n.label, n.x!, n.y! + 32);
    });
  }, [nodes, links]);

  useEffect(() => { draw(); }, [draw]);

  if (anomalies.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <p className="text-lg">No anomalies detected</p>
        <p className="text-sm mt-1">All bidders appear independent</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <canvas ref={canvasRef} width={600} height={400} className="w-full max-w-[600px] mx-auto border border-slate-200 rounded-xl bg-white" />
      {/* Legend */}
      <div className="flex flex-wrap gap-4 justify-center mt-4">
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-500" /> <span className="text-xs text-slate-600">Shared Entity</span></div>
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-orange-500" /> <span className="text-xs text-slate-600">Recycled Document</span></div>
        <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-purple-500" /> <span className="text-xs text-slate-600">Coordinated Bidding</span></div>
      </div>
    </div>
  );
};

export default AnomalyGraph;
