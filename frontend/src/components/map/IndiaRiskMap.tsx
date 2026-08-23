import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api } from '../../services/api';
import { formatCurrency, formatNumber } from '../../lib/utils';
import indiaGeoJson from '../../data/india_states_geo.json';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize2,
  Minimize2,
  X,
  ArrowRight,
  ChevronRight,
  ShieldAlert,
  Layers,
  MapPin,
  Compass,
  Info
} from 'lucide-react';

export type MapMetric = 'project_count' | 'sanctioned_funds' | 'utilization' | 'completion_rate' | 'risk_signals' | 'signal_density';
export type MapDisplayMode = 'choropleth' | 'clusters' | 'grid';

interface IndiaRiskMapProps {
  statesData?: any[];
  onSelectState?: (state: string) => void;
  showFilters?: boolean;
}

export const IndiaRiskMap: React.FC<IndiaRiskMapProps> = ({
  onSelectState,
  showFilters = true,
}) => {
  // Default metric is PROJECT ACTIVITY (Section 10)
  const [metric, setMetric] = useState<MapMetric>('project_count');
  const [displayMode, setDisplayMode] = useState<MapDisplayMode>('choropleth');
  const [selectedStateName, setSelectedStateName] = useState<string | null>(null);
  const [selectedDistrictName, setSelectedDistrictName] = useState<string | null>(null);
  const [stateDetailData, setStateDetailData] = useState<any | null>(null);
  const [isDistrictView, setIsDistrictView] = useState<boolean>(false);
  const [districtGeoJson, setDistrictGeoJson] = useState<any | null>(null);
  const [loadingDistrictGeo, setLoadingDistrictGeo] = useState<boolean>(false);

  // Hover state (State or District)
  const [hoveredData, setHoveredData] = useState<{
    type: 'state' | 'district';
    name: string;
    code?: string;
    parentState?: string;
    x: number;
    y: number;
  } | null>(null);

  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [mapApiData, setMapApiData] = useState<{ states: any[]; national: any } | null>(null);

  // Filters State
  const [filterYear, setFilterYear] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterRiskLevel, setFilterRiskLevel] = useState<string>('');

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<L.Map | null>(null);
  const geoJsonLayerRef = useRef<L.GeoJSON | null>(null);
  const clusterLayerRef = useRef<L.LayerGroup | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Load backend map data
  const loadMapData = async () => {
    setLoading(true);
    try {
      const res = await api.getAnalyticsMapData({
        year: filterYear,
        category: filterCategory,
        status: filterStatus,
        riskLevel: filterRiskLevel,
      });
      setMapApiData(res);
    } catch (err) {
      console.error('Failed to load map data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMapData();
  }, [filterYear, filterCategory, filterStatus, filterRiskLevel]);

  // Load state detail data when selected
  useEffect(() => {
    if (selectedStateName) {
      api.getStateMapDetails(selectedStateName).then((res) => {
        setStateDetailData(res);
      }).catch(() => {
        setStateDetailData(null);
      });
    } else {
      setStateDetailData(null);
      setSelectedDistrictName(null);
      setIsDistrictView(false);
      setDistrictGeoJson(null);
    }
  }, [selectedStateName]);

  // Load district boundaries when entering district drill-down view (Section 14)
  useEffect(() => {
    if (isDistrictView && selectedStateName && stateDetailData?.code) {
      setLoadingDistrictGeo(true);
      const code = stateDetailData.code;
      fetch(`/data/districts/${code}.json`)
        .then((res) => {
          if (!res.ok) throw new Error('District GeoJSON not found');
          return res.json();
        })
        .then((data) => {
          setDistrictGeoJson(data);
          setLoadingDistrictGeo(false);
        })
        .catch((err) => {
          console.warn('Could not load district geojson for state:', selectedStateName, err);
          setDistrictGeoJson(null);
          setLoadingDistrictGeo(false);
        });
    } else if (!isDistrictView) {
      setDistrictGeoJson(null);
    }
  }, [isDistrictView, selectedStateName, stateDetailData]);

  // State lookup dictionary
  const stateMapDict = useMemo(() => {
    const dict: Record<string, any> = {};
    if (mapApiData?.states) {
      mapApiData.states.forEach((s) => {
        dict[s.state] = s;
        if (s.rawState) dict[s.rawState] = s;
        if (s.code) dict[s.code] = s;
      });
    }
    return dict;
  }, [mapApiData]);

  // District lookup dictionary for selected state
  const districtMapDict = useMemo(() => {
    const dict: Record<string, any> = {};
    if (stateDetailData?.districts) {
      stateDetailData.districts.forEach((d: any) => {
        const key = d.district.toUpperCase().trim();
        dict[key] = d;
      });
    }
    return dict;
  }, [stateDetailData]);

  // Data-Driven Choropleth Color calculation (Section 8 & 9)
  const getChoroplethColor = (itemData: any) => {
    if (!itemData) return '#E2E8F0'; // Subtle neutral for missing data

    if (metric === 'project_count') {
      const count = itemData.projectCount || 0;
      if (count > 10000) return '#102A43'; // Deep Navy
      if (count > 5000) return '#243B53';
      if (count > 2000) return '#486581';
      if (count > 500) return '#829AB1';
      if (count > 50) return '#BCCCDC';
      return '#D9E2EC';                    // Light Blue
    }
    if (metric === 'sanctioned_funds') {
      const sanc = itemData.sanctionedAmount || 0;
      if (sanc > 30000000000) return '#0B1F33'; // Midnight Navy
      if (sanc > 15000000000) return '#102A43';
      if (sanc > 5000000000) return '#334E68';
      if (sanc > 1000000000) return '#627D98';
      return '#D9E2EC';
    }
    if (metric === 'utilization') {
      const util = itemData.utilizationRate || 0;
      if (util >= 75) return '#14804A'; // Strong Green
      if (util >= 60) return '#27AB64';
      if (util >= 45) return '#C27A00'; // Amber
      return '#C2413B';                 // Red
    }
    if (metric === 'completion_rate') {
      const comp = itemData.completionRate || 0;
      if (comp >= 50) return '#14804A'; // Strong Green
      if (comp >= 40) return '#27AB64';
      if (comp >= 30) return '#C27A00'; // Amber
      return '#C2413B';                 // Red
    }
    if (metric === 'risk_signals') {
      const signals = itemData.riskSignals || 0;
      if (signals >= 40) return '#8F1D1D'; // Critical Burgundy
      if (signals >= 15) return '#C2413B'; // High Red
      if (signals >= 5) return '#C27A00';  // Amber Review
      if (signals >= 1) return '#EAB308';  // Mild
      return '#EDF7F1';                    // Neutral Low
    }
    if (metric === 'signal_density') {
      // Normalized risk signal density (Section 19)
      const density = itemData.signalDensity || 0;
      if (density >= 1.5) return '#8F1D1D';
      if (density >= 0.8) return '#C2413B';
      if (density >= 0.3) return '#C27A00';
      return '#EDF7F1';
    }
    return '#D9E2EC';
  };

  // Initialize and update Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!leafletMapRef.current) {
      // Professional GIS viewport bounds centered on India
      const map = L.map(mapContainerRef.current, {
        center: [22.8, 82.5],
        zoom: 4.6,
        minZoom: 3.8,
        maxZoom: 10,
        zoomControl: false,
        attributionControl: false,
      });

      // Subtle Carto Positron basemap for realistic oceans, international boundaries and coastlines (Section 7 & 22)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map);

      leafletMapRef.current = map;
    }

    const map = leafletMapRef.current;

    // Clean previous layers
    if (geoJsonLayerRef.current) {
      map.removeLayer(geoJsonLayerRef.current);
      geoJsonLayerRef.current = null;
    }
    if (clusterLayerRef.current) {
      map.removeLayer(clusterLayerRef.current);
      clusterLayerRef.current = null;
    }

    if (displayMode === 'choropleth') {
      if (isDistrictView && districtGeoJson) {
        // Render District Boundaries Drill-Down Layer (Section 14)
        const distLayer = L.geoJSON(districtGeoJson, {
          style: (feature) => {
            const distName = (feature?.properties?.districtName || '').toUpperCase().trim();
            const data = districtMapDict[distName];
            const color = getChoroplethColor(data);
            const isSelected = selectedDistrictName && selectedDistrictName.toUpperCase() === distName;

            return {
              fillColor: color,
              weight: isSelected ? 2.5 : 0.9,
              opacity: 1,
              color: isSelected ? '#102A43' : '#64748B',
              fillOpacity: 0.86,
              dashArray: isSelected ? '' : '1, 1',
            };
          },
          onEachFeature: (feature, layer) => {
            const distName = feature?.properties?.districtName || '';
            layer.on({
              mouseover: (e) => {
                const l = e.target;
                l.setStyle({
                  weight: 2.2,
                  color: '#1769E0',
                  fillOpacity: 0.96,
                  dashArray: '',
                });
                l.bringToFront();

                const pt = map.mouseEventToContainerPoint(e.originalEvent);
                setHoveredData({
                  type: 'district',
                  name: distName,
                  parentState: selectedStateName || '',
                  x: pt.x,
                  y: pt.y,
                });
              },
              mousemove: (e) => {
                const pt = map.mouseEventToContainerPoint(e.originalEvent);
                setHoveredData((prev) => (prev ? { ...prev, x: pt.x, y: pt.y } : null));
              },
              mouseout: (e) => {
                if (geoJsonLayerRef.current) {
                  geoJsonLayerRef.current.resetStyle(e.target);
                }
                setHoveredData(null);
              },
              click: () => {
                setSelectedDistrictName(distName);
                navigate(`/projects?state=${encodeURIComponent(selectedStateName || '')}&district=${encodeURIComponent(distName)}`);
              },
            });
          },
        }).addTo(map);

        geoJsonLayerRef.current = distLayer;
        map.fitBounds(distLayer.getBounds(), { padding: [30, 30] });
      } else {
        // Render Authoritative India States GeoJSON Layer (Survey of India 36 States/UTs) (Section 2, 4, 6)
        const stateLayer = L.geoJSON(indiaGeoJson as any, {
          style: (feature) => {
            const name = feature?.properties?.stateName || '';
            const data = stateMapDict[name];
            const color = getChoroplethColor(data);
            const isSelected = selectedStateName === name;

            return {
              fillColor: color,
              weight: isSelected ? 2.8 : 1.2,
              opacity: 1,
              color: isSelected ? '#0F172A' : '#FFFFFF',
              fillOpacity: 0.90,
            };
          },
          onEachFeature: (feature, layer) => {
            const stateName = feature?.properties?.stateName || '';
            const stateCode = feature?.properties?.stateCode || '';

            layer.on({
              mouseover: (e) => {
                const l = e.target;
                l.setStyle({
                  weight: 2.2,
                  color: '#1769E0',
                  fillOpacity: 0.98,
                });
                l.bringToFront();

                const pt = map.mouseEventToContainerPoint(e.originalEvent);
                setHoveredData({
                  type: 'state',
                  name: stateName,
                  code: stateCode,
                  x: pt.x,
                  y: pt.y,
                });
              },
              mousemove: (e) => {
                const pt = map.mouseEventToContainerPoint(e.originalEvent);
                setHoveredData((prev) => (prev ? { ...prev, x: pt.x, y: pt.y } : null));
              },
              mouseout: (e) => {
                if (geoJsonLayerRef.current) {
                  geoJsonLayerRef.current.resetStyle(e.target);
                }
                setHoveredData(null);
              },
              click: (e) => {
                setSelectedStateName(stateName);
                if (onSelectState) onSelectState(stateName);
                map.fitBounds(e.target.getBounds(), { padding: [50, 50], maxZoom: 6 });
              },
            });
          },
        }).addTo(map);

        geoJsonLayerRef.current = stateLayer;

        if (!selectedStateName) {
          map.fitBounds(stateLayer.getBounds(), { padding: [15, 15] });
        }
      }
    } else if (displayMode === 'clusters') {
      // Project Location / Centroid Cluster Layer (Section 16 & 17 - District Level Aggregation Only)
      const group = L.layerGroup();

      (indiaGeoJson as any).features.forEach((feat: any) => {
        const stateName = feat.properties?.stateName || '';
        const data = stateMapDict[stateName];
        if (!data || !data.projectCount) return;

        // Approximate centroid for state badge
        const bounds = L.geoJSON(feat).getBounds();
        const center = bounds.getCenter();

        const count = data.projectCount;
        const radius = Math.min(28, Math.max(14, Math.round(Math.sqrt(count) * 0.18)));

        const marker = L.circleMarker(center, {
          radius: radius,
          fillColor: '#102A43',
          fillOpacity: 0.85,
          color: '#FFFFFF',
          weight: 2,
        });

        marker.bindTooltip(
          `<strong>${stateName}</strong><br/>${formatNumber(count)} works (District-level aggregation)`,
          { direction: 'top', className: 'gov-tooltip' }
        );

        marker.on('click', () => {
          setSelectedStateName(stateName);
          if (onSelectState) onSelectState(stateName);
          map.fitBounds(bounds, { padding: [40, 40] });
        });

        marker.addTo(group);
      });

      group.addTo(map);
      clusterLayerRef.current = group;
    }
  }, [mapApiData, metric, displayMode, selectedStateName, selectedDistrictName, isDistrictView, districtGeoJson]);

  // Map Controls Handlers
  const handleZoomIn = () => leafletMapRef.current?.zoomIn();
  const handleZoomOut = () => leafletMapRef.current?.zoomOut();

  const handleResetToNational = () => {
    setSelectedStateName(null);
    setSelectedDistrictName(null);
    setIsDistrictView(false);
    setDistrictGeoJson(null);
    if (geoJsonLayerRef.current && leafletMapRef.current) {
      leafletMapRef.current.fitBounds(geoJsonLayerRef.current.getBounds(), { padding: [15, 15] });
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
      setIsFullscreen(false);
    }
  };

  // Dynamic Subtitle (Section 11)
  const getMapSubtitle = () => {
    if (isDistrictView) {
      return `District-level MPLADS activity breakdown for ${selectedStateName}.`;
    }
    switch (metric) {
      case 'project_count':
        return 'Geographic distribution of MPLADS project activity across India.';
      case 'sanctioned_funds':
        return 'Sanctioned funds concentration across India.';
      case 'utilization':
        return 'Fund expenditure and utilization rate across India.';
      case 'completion_rate':
        return 'Work completion rate across India.';
      case 'risk_signals':
        return 'High-value analytical signal counts across India.';
      case 'signal_density':
        return 'Normalized analytical signal density per 100 projects.';
      default:
        return 'Geographic distribution of MPLADS project activity across India.';
    }
  };

  // Get active hovered stats
  const getHoveredStats = () => {
    if (!hoveredData) return null;
    if (hoveredData.type === 'state') {
      return stateMapDict[hoveredData.name] || null;
    }
    if (hoveredData.type === 'district') {
      return districtMapDict[hoveredData.name.toUpperCase().trim()] || null;
    }
    return null;
  };

  const hoveredStats = getHoveredStats();

  return (
    <div
      ref={containerRef}
      className={`gov-card overflow-hidden flex flex-col bg-white border border-[#E5E7EB] shadow-card transition-all ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none h-screen w-screen p-6' : 'w-full'
      }`}
    >
      {/* 1. Map Header & Mode Selector (Section 9, 10, 11) */}
      <div className="p-4 border-b border-[#E5E7EB] flex flex-wrap items-center justify-between gap-4 bg-white">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#102A43]" />
            <h3 className="text-sm font-bold font-sans uppercase tracking-wider text-[#172033]">
              NATIONAL DEVELOPMENT MAP
            </h3>
            {isDistrictView && (
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-[#102A43]/10 text-[#102A43] rounded">
                District Drill-Down Mode
              </span>
            )}
          </div>
          <p className="text-xs text-[#667085] mt-0.5">{getMapSubtitle()}</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Metric Selector Buttons (Section 9) */}
          <div className="flex items-center gap-1 bg-[#F7F8F6] p-1 rounded border border-[#E5E7EB] text-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085] px-1.5 hidden sm:inline">
              Metric:
            </span>
            {[
              { id: 'project_count', label: 'Projects' },
              { id: 'sanctioned_funds', label: 'Funds' },
              { id: 'utilization', label: 'Utilization' },
              { id: 'completion_rate', label: 'Completion' },
              { id: 'risk_signals', label: 'Risk Signals' },
              { id: 'signal_density', label: 'Signal Density' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setMetric(m.id as MapMetric)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  metric === m.id
                    ? 'bg-white text-[#102A43] font-bold shadow-xs border border-[#E5E7EB]'
                    : 'text-[#667085] hover:text-[#172033]'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Map Display Mode (Section 16) */}
          <div className="flex items-center gap-1 bg-[#F7F8F6] p-1 rounded border border-[#E5E7EB] text-xs">
            <button
              onClick={() => setDisplayMode('choropleth')}
              className={`px-2.5 py-1 rounded text-xs ${
                displayMode === 'choropleth' ? 'bg-white font-bold text-[#102A43] shadow-xs' : 'text-[#667085]'
              }`}
            >
              Choropleth
            </button>
            <button
              onClick={() => setDisplayMode('clusters')}
              className={`px-2.5 py-1 rounded text-xs ${
                displayMode === 'clusters' ? 'bg-white font-bold text-[#102A43] shadow-xs' : 'text-[#667085]'
              }`}
            >
              Project Points
            </button>
            <button
              onClick={() => setDisplayMode('grid')}
              className={`px-2.5 py-1 rounded text-xs ${
                displayMode === 'grid' ? 'bg-white font-bold text-[#102A43] shadow-xs' : 'text-[#667085]'
              }`}
            >
              Matrix
            </button>
          </div>
        </div>
      </div>

      {/* 2. Interactive Breadcrumb Navigation & Filters Bar (Section 15) */}
      {showFilters && (
        <div className="px-4 py-2 bg-[#F7F8F6] border-b border-[#E5E7EB] flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Clickable Breadcrumbs */}
          <div className="flex items-center gap-1.5 font-sans">
            <button
              onClick={handleResetToNational}
              className={`font-semibold transition-colors ${
                selectedStateName ? 'text-[#102A43] hover:underline' : 'text-[#172033] font-bold'
              }`}
            >
              India
            </button>

            {selectedStateName && (
              <>
                <ChevronRight className="w-3.5 h-3.5 text-[#98A2B3]" />
                <button
                  onClick={() => setIsDistrictView(false)}
                  className={`font-bold transition-colors ${
                    isDistrictView ? 'text-[#102A43] hover:underline' : 'text-[#172033]'
                  }`}
                >
                  {selectedStateName}
                </button>

                {isDistrictView && (
                  <>
                    <ChevronRight className="w-3.5 h-3.5 text-[#98A2B3]" />
                    <span className="font-bold text-[#147A73]">
                      {selectedDistrictName || 'All Districts'}
                    </span>
                  </>
                )}

                <button
                  onClick={handleResetToNational}
                  className="ml-2 text-[10px] px-2 py-0.5 rounded bg-white text-[#667085] hover:text-[#172033] border border-[#E5E7EB] transition-colors"
                >
                  ← Back to National
                </button>
              </>
            )}
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-2.5">
            <select
              value={filterYear}
              onChange={(e) => setFilterYear(e.target.value)}
              className="px-2.5 py-1 bg-white border border-[#E5E7EB] rounded text-xs text-[#172033] focus:outline-none"
            >
              <option value="">All Financial Years</option>
              <option value="2025-2026">FY 2025-26</option>
              <option value="2024-2025">FY 2024-25</option>
              <option value="2023-2024">FY 2023-24</option>
              <option value="2022-2023">FY 2022-23</option>
            </select>

            <select
              value={filterRiskLevel}
              onChange={(e) => setFilterRiskLevel(e.target.value)}
              className="px-2.5 py-1 bg-white border border-[#E5E7EB] rounded text-xs text-[#172033] focus:outline-none"
            >
              <option value="">All Risk Tiers</option>
              <option value="CRITICAL">Critical Signals</option>
              <option value="HIGH">High Signals</option>
              <option value="MEDIUM">Review Required</option>
              <option value="LOW">Low Signals</option>
            </select>

            {(filterYear || filterRiskLevel) && (
              <button
                onClick={() => {
                  setFilterYear('');
                  setFilterRiskLevel('');
                }}
                className="px-2 py-1 text-xs text-[#C2413B] hover:bg-[#FDF2F2] rounded inline-flex items-center gap-1 transition-colors"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* 3. GIS Map Canvas with Authoritative Boundary Geometry */}
      <div className="relative flex-1 bg-[#F8FAFC] min-h-[560px] max-h-[660px] overflow-hidden flex items-center justify-center select-none">
        {/* National Snapshot Overlay (Section 13) */}
        {mapApiData?.national && !isDistrictView && (
          <div className="absolute top-4 left-4 z-[400] gov-card p-3.5 bg-white/95 backdrop-blur-xs border border-[#E5E7EB] shadow-xs space-y-1.5 pointer-events-auto max-w-[210px]">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085] block">
              National Snapshot
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-[10px] text-[#667085] block">Projects</span>
                <strong className="text-[#172033] font-mono">{formatNumber(mapApiData.national.totalProjects)}</strong>
              </div>
              <div>
                <span className="text-[10px] text-[#667085] block">States / UTs</span>
                <strong className="text-[#172033] font-mono">{mapApiData.national.totalStates}</strong>
              </div>
              <div>
                <span className="text-[10px] text-[#667085] block">Sanctioned</span>
                <strong className="text-[#102A43] font-semibold text-[11px] truncate block">
                  {formatCurrency(mapApiData.national.sanctionedAmount)}
                </strong>
              </div>
              <div>
                <span className="text-[10px] text-[#667085] block">Utilized</span>
                <strong className="text-[#147A73] font-semibold text-[11px] truncate block">
                  {formatCurrency(mapApiData.national.utilizedAmount)}
                </strong>
              </div>
            </div>
          </div>
        )}

        {/* District View Indicator Badge */}
        {isDistrictView && (
          <div className="absolute top-4 left-4 z-[400] gov-card p-3 bg-white/95 backdrop-blur-xs border border-[#E5E7EB] shadow-xs space-y-1 pointer-events-auto max-w-[230px]">
            <div className="flex items-center gap-1.5 text-[#102A43] font-bold text-xs">
              <Compass className="w-3.5 h-3.5" />
              <span>{selectedStateName} Districts</span>
            </div>
            <p className="text-[10px] text-[#667085]">
              {stateDetailData?.districts ? `${stateDetailData.districts.length} active administrative districts` : 'Loading districts...'}
            </p>
          </div>
        )}

        {/* Map Action Controls (Section 21) */}
        <div className="absolute top-4 right-4 z-[400] flex flex-col gap-1.5 pointer-events-auto">
          <button
            onClick={handleZoomIn}
            className="p-2 bg-white hover:bg-[#F7F8F6] text-[#172033] rounded border border-[#E5E7EB] shadow-xs transition-colors"
            title="Zoom In (+)"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-2 bg-white hover:bg-[#F7F8F6] text-[#172033] rounded border border-[#E5E7EB] shadow-xs transition-colors"
            title="Zoom Out (-)"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetToNational}
            className="p-2 bg-white hover:bg-[#F7F8F6] text-[#172033] rounded border border-[#E5E7EB] shadow-xs transition-colors"
            title="Reset National India View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={toggleFullscreen}
            className="p-2 bg-white hover:bg-[#F7F8F6] text-[#172033] rounded border border-[#E5E7EB] shadow-xs transition-colors"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>

        {/* Real Leaflet Vector Map Container */}
        {displayMode === 'choropleth' || displayMode === 'clusters' ? (
          <div ref={mapContainerRef} className="w-full h-full min-h-[560px]" />
        ) : null}

        {/* Matrix Grid Mode (Alternative Analytical View) */}
        {displayMode === 'grid' && (
          <div className="w-full h-full p-6 overflow-y-auto max-h-[560px] grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 bg-[#F8FAFC]">
            {mapApiData?.states.map((st) => {
              const isSelected = selectedStateName === st.state;
              const fillCol = getChoroplethColor(st);
              const isDark = fillCol === '#102A43' || fillCol === '#0B1F33' || fillCol === '#8F1D1D' || fillCol === '#243B53';

              return (
                <div
                  key={st.state}
                  onClick={() => {
                    setSelectedStateName(st.state);
                    if (onSelectState) onSelectState(st.state);
                  }}
                  className={`p-3.5 rounded border cursor-pointer select-none transition-all ${
                    isSelected ? 'ring-2 ring-[#102A43] shadow-md' : 'hover:shadow-xs'
                  }`}
                  style={{ backgroundColor: fillCol, color: isDark ? '#FFFFFF' : '#172033', borderColor: '#CBD5E1' }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold truncate">{st.state}</span>
                    <span className="text-[10px] font-mono opacity-80">{st.code}</span>
                  </div>
                  <div className="text-[11px] opacity-90 space-y-0.5">
                    <div className="flex justify-between">
                      <span>Works:</span>
                      <strong className="font-mono">{formatNumber(st.projectCount)}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Sanctioned:</span>
                      <strong className="font-medium">{formatCurrency(st.sanctionedAmount)}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Signals:</span>
                      <strong className="font-mono">{st.riskSignals}</strong>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Interactive Hover Tooltip with Live Backend Values (Section 12) */}
        {hoveredData && (
          <div
            className="absolute z-[500] gov-card p-3 bg-white/95 backdrop-blur-xs border border-[#E5E7EB] shadow-dropdown text-xs space-y-1.5 pointer-events-none animate-fadeIn"
            style={{
              left: `${Math.min(window.innerWidth - 300, hoveredData.x + 15)}px`,
              top: `${Math.max(10, hoveredData.y - 40)}px`,
            }}
          >
            <div className="flex items-center justify-between gap-3 pb-1 border-b border-[#E5E7EB]">
              <div>
                <span className="font-bold text-sm text-[#172033] font-display">{hoveredData.name}</span>
                {hoveredData.parentState && (
                  <span className="text-[10px] text-[#667085] block">{hoveredData.parentState}</span>
                )}
              </div>
              {hoveredData.code && (
                <span className="font-mono text-[10px] font-bold text-[#102A43] px-1.5 py-0.5 bg-[#F0F4F8] rounded">
                  {hoveredData.code}
                </span>
              )}
            </div>

            {hoveredStats ? (
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
                <div>
                  <span className="text-[#667085]">Projects: </span>
                  <strong className="text-[#172033] font-mono">{formatNumber(hoveredStats.projectCount)}</strong>
                </div>
                <div>
                  <span className="text-[#667085]">Completion: </span>
                  <strong className="text-[#14804A] font-mono">{hoveredStats.completionRate}%</strong>
                </div>
                <div>
                  <span className="text-[#667085]">Sanctioned: </span>
                  <strong className="text-[#102A43] font-semibold">{formatCurrency(hoveredStats.sanctionedAmount)}</strong>
                </div>
                <div>
                  <span className="text-[#667085]">Utilized: </span>
                  <strong className="text-[#147A73] font-semibold">{formatCurrency(hoveredStats.utilizedAmount)}</strong>
                </div>
              </div>
            ) : (
              <div className="text-[11px] text-[#667085]">Data unavailable</div>
            )}

            <div className="pt-1 border-t border-[#E5E7EB] flex items-center justify-between text-[10px]">
              <span className="text-[#667085]">Analytical signals:</span>
              <strong className="font-mono text-[#C2413B] font-bold">
                {hoveredStats?.riskSignals || 0}
                {hoveredStats?.signalDensity !== undefined && ` (${hoveredStats.signalDensity}%)`}
              </strong>
            </div>
          </div>
        )}

        {/* Dynamic Map Legend (Section 20) */}
        <div className="absolute bottom-4 left-4 z-[400] gov-card p-3 bg-white/95 backdrop-blur-xs border border-[#E5E7EB] shadow-xs space-y-1 text-[11px] pointer-events-auto">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085] block">
            {metric === 'project_count' && 'PROJECT ACTIVITY'}
            {metric === 'sanctioned_funds' && 'SANCTIONED FUNDS'}
            {metric === 'utilization' && 'UTILIZATION RATE'}
            {metric === 'completion_rate' && 'COMPLETION RATE'}
            {metric === 'risk_signals' && 'RISK SIGNALS'}
            {metric === 'signal_density' && 'SIGNAL DENSITY'}
          </span>
          <div className="flex items-center gap-2 pt-0.5">
            <span className="text-[10px] text-[#667085]">Low</span>
            <div
              className="h-2.5 w-32 rounded-xs border border-black/10"
              style={{
                background:
                  metric === 'risk_signals' || metric === 'signal_density'
                    ? 'linear-gradient(to right, #EDF7F1, #EAB308, #C27A00, #C2413B, #8F1D1D)'
                    : metric === 'project_count' || metric === 'sanctioned_funds'
                    ? 'linear-gradient(to right, #D9E2EC, #829AB1, #486581, #102A43)'
                    : 'linear-gradient(to right, #C2413B, #C27A00, #27AB64, #14804A)',
              }}
            />
            <span className="text-[10px] text-[#667085]">High</span>
          </div>
        </div>

        {/* Official Data Source Attribution Footer (Section 30) */}
        <div className="absolute bottom-4 right-4 z-[400] text-[10px] font-mono text-[#64748B] bg-white/95 backdrop-blur-xs px-3 py-1 rounded border border-[#E5E7EB] shadow-xs pointer-events-auto flex items-center gap-1.5">
          <span>Boundary data: Survey of India / DataMeet Dataset (ODbL)</span>
          <span>•</span>
          <span>MPLADS analytics: Official MoSPI Records</span>
        </div>

        {/* Right-Side State Information & Drill-Down Drawer (Section 13 & 14) */}
        {selectedStateName && stateMapDict[selectedStateName] && (
          <div className="absolute top-0 right-0 bottom-0 w-80 sm:w-96 bg-white border-l border-[#E5E7EB] shadow-dropdown z-[450] p-5 overflow-y-auto space-y-5 animate-fadeIn flex flex-col justify-between pointer-events-auto">
            <div className="space-y-4">
              {/* Drawer Header */}
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
                <div>
                  <h4 className="text-base font-bold text-[#172033] font-display">{selectedStateName}</h4>
                  <span className="text-[11px] text-[#147A73] font-medium">State Development Overview</span>
                </div>
                <button
                  onClick={() => setSelectedStateName(null)}
                  className="p-1 text-[#98A2B3] hover:text-[#172033] rounded hover:bg-[#F7F8F6]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* State Metrics Grid */}
              <div className="grid grid-cols-2 gap-2.5 text-xs">
                <div className="p-2.5 bg-[#F8FAFC] rounded border border-[#E5E7EB]">
                  <span className="text-[#667085] text-[10px] uppercase font-bold block">Projects</span>
                  <span className="text-base font-bold text-[#172033] font-mono">
                    {formatNumber(stateMapDict[selectedStateName].projectCount)}
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded border border-[#E5E7EB]">
                  <span className="text-[#667085] text-[10px] uppercase font-bold block">Completion</span>
                  <span className="text-base font-bold text-[#14804A] font-mono">
                    {stateMapDict[selectedStateName].completionRate}%
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded border border-[#E5E7EB]">
                  <span className="text-[#667085] text-[10px] uppercase font-bold block">Sanctioned</span>
                  <span className="text-xs font-bold text-[#102A43] block truncate font-semibold">
                    {formatCurrency(stateMapDict[selectedStateName].sanctionedAmount)}
                  </span>
                </div>
                <div className="p-2.5 bg-[#F8FAFC] rounded border border-[#E5E7EB]">
                  <span className="text-[#667085] text-[10px] uppercase font-bold block">Utilized</span>
                  <span className="text-xs font-bold text-[#147A73] block truncate font-semibold">
                    {formatCurrency(stateMapDict[selectedStateName].utilizedAmount)}
                  </span>
                </div>
              </div>

              {/* Analytical Signals Badge */}
              <div className="p-3 bg-[#FDF2F2] rounded border border-[#F9DFDF] flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-[#C2413B]">
                  <ShieldAlert className="w-4 h-4" />
                  <span className="font-semibold">Analytical Signals:</span>
                </div>
                <strong className="font-mono text-[#C2413B] text-sm">
                  {stateMapDict[selectedStateName].riskSignals}
                </strong>
              </div>

              {/* Top Project Categories (Section 13) */}
              {stateDetailData?.categories && stateDetailData.categories.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-[#E5E7EB]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085] block">
                    Top Project Categories
                  </span>
                  <div className="space-y-1.5 text-xs">
                    {stateDetailData.categories.map((c: any, i: number) => (
                      <div key={i} className="flex items-center justify-between text-[11px]">
                        <span className="text-[#172033] truncate max-w-[180px]">{c.category || 'Infrastructure'}</span>
                        <strong className="text-[#102A43] font-mono">{formatNumber(c.count)}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Top Districts (Section 13) */}
              {stateDetailData?.districts && stateDetailData.districts.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-[#E5E7EB]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085] block">
                    Top Districts
                  </span>
                  <div className="space-y-1.5 text-xs">
                    {stateDetailData.districts.slice(0, 5).map((d: any, i: number) => (
                      <div
                        key={i}
                        onClick={() => {
                          setSelectedDistrictName(d.district);
                          setIsDistrictView(true);
                        }}
                        className="flex items-center justify-between p-1.5 rounded hover:bg-[#F0F4F8] cursor-pointer text-[11px] transition-colors"
                      >
                        <span className="text-[#172033] font-medium truncate">{d.district}</span>
                        <span className="font-mono text-[#667085]">{formatNumber(d.projectCount)} works</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons: Explore State / District Drill-Down (Section 13 & 14) */}
            <div className="space-y-2 pt-4 border-t border-[#E5E7EB]">
              {!isDistrictView ? (
                <button
                  onClick={() => setIsDistrictView(true)}
                  disabled={loadingDistrictGeo}
                  className="w-full py-2.5 bg-[#102A43] hover:bg-[#193354] text-white text-xs font-semibold rounded shadow-xs inline-flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <span>{loadingDistrictGeo ? 'Loading Boundaries...' : 'Explore State Districts →'}</span>
                </button>
              ) : (
                <button
                  onClick={() => setIsDistrictView(false)}
                  className="w-full py-2 bg-white text-[#102A43] border border-[#102A43] hover:bg-[#F0F4F8] text-xs font-semibold rounded shadow-xs inline-flex items-center justify-center gap-1.5 transition-colors"
                >
                  <span>← Return to National Map</span>
                </button>
              )}

              <button
                onClick={() => navigate(`/analytics/states/${encodeURIComponent(selectedStateName)}`)}
                className="w-full py-2 bg-[#F0F4F8] hover:bg-[#D9E2EC] text-[#102A43] text-xs font-semibold rounded inline-flex items-center justify-center gap-1 transition-colors"
              >
                <span>View Full State Analytics</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
