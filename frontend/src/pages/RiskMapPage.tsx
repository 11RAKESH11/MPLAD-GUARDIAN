import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { IndiaRiskMap } from '../components/map/IndiaRiskMap';
import { CardSkeleton } from '../components/common/LoadingSkeleton';

export const RiskMapPage: React.FC = () => {
  const [mapData, setMapData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRiskMapData().then((res) => {
      setMapData(res.states);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-20 bg-white rounded-lg animate-pulse border border-[#E5E7EB]" />
        <CardSkeleton count={4} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h2 className="text-xl lg:text-2xl font-extrabold text-[#172033] tracking-tight font-display">
          National Risk Command Center
        </h2>
        <p className="text-xs text-[#667085] mt-0.5">
          Geospatial anomaly density, fund concentration, and completion metrics across all 36 States & Union Territories
        </p>
      </div>

      {/* Main Map */}
      <IndiaRiskMap statesData={mapData} showFilters={true} />
    </div>
  );
};
