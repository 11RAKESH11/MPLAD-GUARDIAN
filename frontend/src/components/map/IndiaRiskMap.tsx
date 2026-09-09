import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
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
  Info,
  ExternalLink,
  AlertTriangle,
  FileText,
  Activity,
  BarChart3,
  Calendar,
  CheckCircle2,
  Clock,
  Database,
  HelpCircle,
  TrendingUp,
  Search,
  Filter
} from 'lucide-react';

export type MapMetric = 
  | 'risk_concentration'
  | 'project_count'
  | 'sanctioned_funds'
  | 'utilization'
  | 'completion_rate'
  | 'anomalies';

export type MapTheme = 'light' | 'dark';

interface IndiaRiskMapProps {
  statesData?: any[];
  onSelectState?: (state: string) => void;
  showFilters?: boolean;
}

export const IndiaRiskMap: React.FC<IndiaRiskMapProps> = ({
  onSelectState,
  showFilters = true,
}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // URL state synchronization
  const initialMetric = (searchParams.get('metric') as MapMetric) || 'risk_concentration';
  const initialState = searchParams.get('state') || null;
  const initialDistrict = searchParams.get('district') || null;
  const initialYear = searchParams.get('fy') || '';
  const initialCategory = searchParams.get('category') || '';
  const initialStatus = searchParams.get('status') || '';
  const initialRiskLevel = searchParams.get('risk') || '';

  const [metric, setMetric] = useState<MapMetric>(initialMetric);
  const [mapTheme, setMapTheme] = useState<MapTheme>('light');
  const [selectedStateName, setSelectedStateName] = useState<string | null>(initialState);
  const [selectedDistrictName, setSelectedDistrictName] = useState<string | null>(initialDistrict);
  
  const [stateDetailData, setStateDetailData] = useState<any | null>(null);
  const [districtIntelligence, setDistrictIntelligence] = useState<any | null>(null);
  const [isDistrictView, setIsDistrictView] = useState<boolean>(!!initialState);
  const [districtGeoJson, setDistrictGeoJson] = useState<any | null>(null);
  const [loadingDistrictGeo, setLoadingDistrictGeo] = useState<boolean>(false);
  const [loadingDistrictIntel, setLoadingDistrictIntel] = useState<boolean>(false);

  // Hover state (State or District)
  const [hoveredData, setHoveredData] = useState<{
    type: 'state' | 'district';
    name: string;
    code?: string;
    parentState?: string;
    metrics: any;
    x: number;
    y: number;
  } | null>(null);

  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [mapApiData, setMapApiData] = useState<{ states: any[]; count: number } | null>(null);
  const [nationalSummary, setNationalSummary] = useState<any | null>(null);
  const [showExplainer, setShowExplainer] = useState<boolean>(false);

  // Filters State
  const [filterYear, setFilterYear] = useState<string>(initialYear);
  const [filterCategory, setFilterCategory] = useState<string>(initialCategory);
  const [filterStatus, setFilterStatus] = useState<string>(initialStatus);
  const [filterRiskLevel, setFilterRiskLevel] = useState<string>(initialRiskLevel);

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<L.Map | null>(null);
  const geoJsonLayerRef = useRef<L.GeoJSON | null>(null);
  const districtLayerRef = useRef<L.GeoJSON | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Sync state to URL search parameters
  useEffect(() => {
    const params = new URLSearchParams();
    if (metric) params.set('metric', metric);
    if (selectedStateName) params.set('state', selectedStateName);
    if (selectedDistrictName) params.set('district', selectedDistrictName);
    if (filterYear) params.set('fy', filterYear);
    if (filterCategory) params.set('category', filterCategory);
    if (filterStatus) params.set('status', filterStatus);
    if (filterRiskLevel) params.set('risk', filterRiskLevel);

    setSearchParams(params, { replace: true });
  }, [metric, selectedStateName, selectedDistrictName, filterYear, filterCategory, filterStatus, filterRiskLevel]);

  // Load summary KPIs
  useEffect(() => {
    api.getMapSummary().then((res) => {
      setNationalSummary(res);
    }).catch((err) => console.warn('Could not load map summary', err));
  }, []);

  // Load backend map data with filters
  const loadMapData = async () => {
    setLoading(true);
    try {
      const res = await api.getMapStates({
        year: filterYear,
        category: filterCategory,
        status: filterStatus,
        riskLevel: filterRiskLevel,
      });
      setMapApiData(res);
    } catch (err) {
      console.error('Failed to load map states data', err);
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
      api.getStateIntelligence(selectedStateName).then((res) => {
        setStateDetailData(res);
      }).catch((err) => {
        console.warn('Failed to load state intelligence', err);
        setStateDetailData(null);
      });
    } else {
      setStateDetailData(null);
      setSelectedDistrictName(null);
      setDistrictIntelligence(null);
      setIsDistrictView(false);
      setDistrictGeoJson(null);
    }
  }, [selectedStateName]);

  // Load district intelligence when district is selected
  useEffect(() => {
    if (selectedStateName && selectedDistrictName) {
      setLoadingDistrictIntel(true);
      api.getDistrictIntelligence(selectedStateName, selectedDistrictName).then((res) => {
        setDistrictIntelligence(res);
        setLoadingDistrictIntel(false);
      }).catch((err) => {
        console.warn('Failed to load district intelligence', err);
        setDistrictIntelligence(null);
        setLoadingDistrictIntel(false);
      });
    } else {
      setDistrictIntelligence(null);
    }
  }, [selectedStateName, selectedDistrictName]);

  // Load district boundaries when entering district view
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

  // Data-Driven Choropleth Color calculation
  const getChoroplethColor = (itemData: any) => {
    if (!itemData) return mapTheme === 'dark' ? '#1E293B' : '#E2E8F0';

    if (metric === 'risk_concentration') {
      const score = itemData.avgRiskScore !== undefined ? itemData.avgRiskScore : (itemData.riskSignals ? itemData.riskSignals * 2 : 0);
      if (score >= 50) return '#991B1B'; // Critical Red
      if (score >= 25) return '#D97706'; // High Amber
      if (score >= 10) return '#2563EB'; // Medium Blue
      return '#059669';                   // Low Emerald
    }
    if (metric === 'project_count') {
      const count = itemData.projectCount || 0;
      if (count > 8000) return '#0F172A'; // Deep Slate
      if (count > 4000) return '#1E293B';
      if (count > 1500) return '#334155';
      if (count > 500) return '#64748B';
      if (count > 50) return '#94A3B8';
      return '#CBD5E1';
    }
    if (metric === 'sanctioned_funds') {
      const sanc = itemData.sanctionedAmount || 0;
      if (sanc > 30000000000) return '#1E1B4B'; // Midnight Indigo
      if (sanc > 15000000000) return '#312E81';
      if (sanc > 5000000000) return '#4338CA';
      if (sanc > 1000000000) return '#6366F1';
      return '#C7D2FE';
    }
    if (metric === 'utilization') {
      const util = itemData.utilizationPct !== undefined ? itemData.utilizationPct : (itemData.utilizationRate || 0);
      if (util >= 75) return '#047857'; // Strong Green
      if (util >= 60) return '#059669';
      if (util >= 45) return '#D97706'; // Amber
      return '#DC2626';                 // Red
    }
    if (metric === 'completion_rate') {
      const comp = itemData.completionPct !== undefined ? itemData.completionPct : (itemData.completionRate || 0);
      if (comp >= 50) return '#047857'; // Strong Green
      if (comp >= 35) return '#059669';
      if (comp >= 20) return '#D97706'; // Amber
      return '#DC2626';                 // Red
    }
    if (metric === 'anomalies') {
      const signals = itemData.riskSignals || itemData.highSignals || 0;
      if (signals >= 30) return '#7F1D1D'; // Critical Burgundy
      if (signals >= 12) return '#B91C1C'; // High Red
      if (signals >= 4) return '#D97706';  // Amber
      return '#10B981';                   // Low Clean Green
    }
    return '#64748B';
  };

  // Initialize and update Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!leafletMapRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [22.5937, 78.9629],
        zoom: 4.6,
        minZoom: 3.8,
        maxZoom: 10,
        zoomControl: false,
        attributionControl: false,
      });

      leafletMapRef.current = map;
    }

    const map = leafletMapRef.current;

    // Render State Polygons (National Overview)
    if (!isDistrictView && indiaGeoJson) {
      if (districtLayerRef.current) {
        map.removeLayer(districtLayerRef.current);
        districtLayerRef.current = null;
      }
      if (geoJsonLayerRef.current) {
        map.removeLayer(geoJsonLayerRef.current);
      }

      const layer = L.geoJSON(indiaGeoJson as any, {
        style: (feature) => {
          const stateName = feature?.properties?.ST_NM || feature?.properties?.NAME_1 || feature?.properties?.name || '';
          const data = stateMapDict[stateName];
          const fillColor = getChoroplethColor(data);

          return {
            fillColor,
            weight: 1.2,
            opacity: 1,
            color: mapTheme === 'dark' ? '#0F172A' : '#FFFFFF',
            dashArray: '',
            fillOpacity: 0.88,
          };
        },
        onEachFeature: (feature, featureLayer) => {
          const stateName = feature?.properties?.ST_NM || feature?.properties?.NAME_1 || feature?.properties?.name || '';
          const data = stateMapDict[stateName];

          featureLayer.on({
            mouseover: (e) => {
              const layer = e.target;
              layer.setStyle({
                weight: 2.5,
                color: mapTheme === 'dark' ? '#38BDF8' : '#0284C7',
                fillOpacity: 0.98,
              });
              layer.bringToFront();

              const containerRect = mapContainerRef.current?.getBoundingClientRect();
              if (containerRect) {
                setHoveredData({
                  type: 'state',
                  name: stateName,
                  code: data?.code,
                  metrics: data,
                  x: e.originalEvent.clientX - containerRect.left,
                  y: e.originalEvent.clientY - containerRect.top,
                });
              }
            },
            mouseout: (e) => {
              geoJsonLayerRef.current?.resetStyle(e.target);
              setHoveredData(null);
            },
            mousemove: (e) => {
              const containerRect = mapContainerRef.current?.getBoundingClientRect();
              if (containerRect) {
                setHoveredData((prev) =>
                  prev ? {
                    ...prev,
                    x: e.originalEvent.clientX - containerRect.left,
                    y: e.originalEvent.clientY - containerRect.top,
                  } : null
                );
              }
            },
            click: (e) => {
              setSelectedStateName(stateName);
              setIsDistrictView(true);
              map.fitBounds(e.target.getBounds(), { padding: [30, 30], maxZoom: 7 });
              if (onSelectState) onSelectState(stateName);
            },
          });
        },
      });

      layer.addTo(map);
      geoJsonLayerRef.current = layer;
    }

    // Render District Polygons (State Drill-down)
    if (isDistrictView && districtGeoJson) {
      if (geoJsonLayerRef.current) {
        map.removeLayer(geoJsonLayerRef.current);
        geoJsonLayerRef.current = null;
      }
      if (districtLayerRef.current) {
        map.removeLayer(districtLayerRef.current);
      }

      const dLayer = L.geoJSON(districtGeoJson, {
        style: (feature) => {
          const dName = (feature?.properties?.district || feature?.properties?.dtname || feature?.properties?.DISTRICT || '').toUpperCase().trim();
          const dData = districtMapDict[dName];
          const fillColor = getChoroplethColor(dData);

          return {
            fillColor,
            weight: 1.0,
            opacity: 1,
            color: mapTheme === 'dark' ? '#0F172A' : '#FFFFFF',
            dashArray: '',
            fillOpacity: 0.85,
          };
        },
        onEachFeature: (feature, featureLayer) => {
          const dName = (feature?.properties?.district || feature?.properties?.dtname || feature?.properties?.DISTRICT || '').trim();
          const dKey = dName.toUpperCase();
          const dData = districtMapDict[dKey];

          featureLayer.on({
            mouseover: (e) => {
              const layer = e.target;
              layer.setStyle({
                weight: 2.5,
                color: mapTheme === 'dark' ? '#F59E0B' : '#D97706',
                fillOpacity: 0.98,
              });
              layer.bringToFront();

              const containerRect = mapContainerRef.current?.getBoundingClientRect();
              if (containerRect) {
                setHoveredData({
                  type: 'district',
                  name: dName,
                  parentState: selectedStateName || '',
                  metrics: dData,
                  x: e.originalEvent.clientX - containerRect.left,
                  y: e.originalEvent.clientY - containerRect.top,
                });
              }
            },
            mouseout: (e) => {
              districtLayerRef.current?.resetStyle(e.target);
              setHoveredData(null);
            },
            mousemove: (e) => {
              const containerRect = mapContainerRef.current?.getBoundingClientRect();
              if (containerRect) {
                setHoveredData((prev) =>
                  prev ? {
                    ...prev,
                    x: e.originalEvent.clientX - containerRect.left,
                    y: e.originalEvent.clientY - containerRect.top,
                  } : null
                );
              }
            },
            click: (e) => {
              setSelectedDistrictName(dName);
              map.fitBounds(e.target.getBounds(), { padding: [40, 40], maxZoom: 8 });
            },
          });
        },
      });

      dLayer.addTo(map);
      districtLayerRef.current = dLayer;
      map.fitBounds(dLayer.getBounds(), { padding: [25, 25] });
    }
  }, [metric, mapTheme, isDistrictView, districtGeoJson, stateMapDict, districtMapDict]);

  const handleResetNationalView = () => {
    setSelectedStateName(null);
    setSelectedDistrictName(null);
    setIsDistrictView(false);
    setDistrictGeoJson(null);
    setDistrictIntelligence(null);
    if (leafletMapRef.current) {
      leafletMapRef.current.setView([22.5937, 78.9629], 4.6);
    }
  };

  const metricDescriptions: Record<MapMetric, { title: string; desc: string }> = {
    risk_concentration: {
      title: 'Risk Concentration',
      desc: 'Average analytical risk score calculated from verified project attributes.'
    },
    project_count: {
      title: 'Project Density',
      desc: 'Total canonical MPLADS works registered in this administrative boundary (not population adjusted).'
    },
    sanctioned_funds: {
      title: 'Sanctioned Funds',
      desc: 'Total cumulative funds sanctioned for development works.'
    },
    utilization: {
      title: 'Fund Utilization',
      desc: 'Percentage of sanctioned funds recorded as utilized in expenditure vouchers.'
    },
    completion_rate: {
      title: 'Completion Rate',
      desc: 'Percentage of works marked as Completed vs In-Progress/Sanctioned.'
    },
    anomalies: {
      title: 'Anomalies & Signals',
      desc: 'Concentration of High and Critical analytical signals requiring desk review.'
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none border-0' : 'h-[780px]'
      }`}
    >
      {/* Top Intelligence Control Bar */}
      <div className="bg-slate-50/90 dark:bg-slate-800/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-700 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 z-10 relative">
        {/* Left: Breadcrumbs & Mode Indicator */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleResetNationalView}
            className={`flex items-center text-xs font-semibold px-2.5 py-1 rounded transition-colors ${
              !selectedStateName
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300'
                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            <Compass className="w-3.5 h-3.5 mr-1" />
            INDIA
          </button>

          {selectedStateName && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide">
                {selectedStateName}
              </span>
            </>
          )}

          {selectedDistrictName && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wide bg-amber-50 dark:bg-amber-950/50 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                {selectedDistrictName}
              </span>
            </>
          )}
        </div>

        {/* Center: Metric Mode Selector */}
        <div className="flex items-center space-x-1 bg-slate-200/70 dark:bg-slate-900/70 p-1 rounded-lg border border-slate-300/60 dark:border-slate-700">
          {(
            [
              ['risk_concentration', 'Risk'],
              ['project_count', 'Projects'],
              ['sanctioned_funds', 'Funds'],
              ['utilization', 'Utilization'],
              ['completion_rate', 'Completion'],
              ['anomalies', 'Anomalies'],
            ] as [MapMetric, string][]
          ).map(([mKey, label]) => (
            <button
              key={mKey}
              onClick={() => setMetric(mKey)}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-all ${
                metric === mKey
                  ? 'bg-white dark:bg-slate-800 text-blue-700 dark:text-blue-400 shadow-sm font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Right: Actions & Tools */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowExplainer(!showExplainer)}
            className="flex items-center text-xs text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-2.5 py-1 rounded-md shadow-xs transition-colors"
            title="What am I looking at?"
          >
            <HelpCircle className="w-3.5 h-3.5 mr-1 text-blue-600 dark:text-blue-400" />
            Explainer
          </button>

          {isDistrictView && (
            <button
              onClick={handleResetNationalView}
              className="flex items-center text-xs text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 px-2.5 py-1 rounded-md hover:bg-blue-100 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" />
              National View
            </button>
          )}

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Filter Toolbar (Section 22 & 24) */}
      {showFilters && (
        <div className="bg-white/95 dark:bg-slate-900/95 border-b border-slate-200 dark:border-slate-800 px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs z-10 relative">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-slate-500 flex items-center font-medium">
              <Filter className="w-3 h-3 mr-1" /> Filters:
            </span>

            <select
              value={filterYear}
              onChange={(e) => setFilterYear(e.target.value)}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2 py-1 text-slate-700 dark:text-slate-200 font-medium"
            >
              <option value="">All Financial Years</option>
              <option value="2024-2025">2024–2025</option>
              <option value="2023-2024">2023–2024</option>
              <option value="2022-2023">2022–2023</option>
              <option value="2021-2022">2021–2022</option>
              <option value="2020-2021">2020–2021</option>
              <option value="2019-2020">2019–2020</option>
            </select>

            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2 py-1 text-slate-700 dark:text-slate-200 font-medium"
            >
              <option value="">All Categories</option>
              <option value="Roads, Pathways and Bridges">Roads & Bridges</option>
              <option value="Drinking Water">Drinking Water</option>
              <option value="Education">Education</option>
              <option value="Health and Family Welfare">Health & Welfare</option>
              <option value="Community Centres">Community Centres</option>
              <option value="Sanitation">Sanitation</option>
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2 py-1 text-slate-700 dark:text-slate-200 font-medium"
            >
              <option value="">All Statuses</option>
              <option value="Work Completed">Work Completed</option>
              <option value="In Progress">In Progress</option>
              <option value="Sanctioned">Sanctioned</option>
            </select>

            <select
              value={filterRiskLevel}
              onChange={(e) => setFilterRiskLevel(e.target.value)}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2 py-1 text-slate-700 dark:text-slate-200 font-medium"
            >
              <option value="">All Risk Tiers</option>
              <option value="CRITICAL">Critical Risk</option>
              <option value="HIGH">High Risk</option>
              <option value="MEDIUM">Medium Risk</option>
              <option value="LOW">Low Risk</option>
            </select>

            {(filterYear || filterCategory || filterStatus || filterRiskLevel) && (
              <button
                onClick={() => {
                  setFilterYear('');
                  setFilterCategory('');
                  setFilterStatus('');
                  setFilterRiskLevel('');
                }}
                className="text-red-600 hover:text-red-800 dark:text-red-400 flex items-center font-medium"
              >
                <X className="w-3 h-3 mr-0.5" /> Clear
              </button>
            )}
          </div>

          {/* Provenance & Disclaimer Badges */}
          <div className="flex items-center space-x-2 text-[10px] text-slate-500">
            <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
              Source: Official MoSPI MPLAD
            </span>
            <span className="bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-800 font-medium">
              GPS: 0% Coverage (Polygon Aggregation)
            </span>
          </div>
        </div>
      )}

      {/* Main Map Container */}
      <div className="w-full h-full relative" style={{ minHeight: '620px' }}>
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Loading Indicator */}
        {(loading || loadingDistrictGeo) && (
          <div className="absolute inset-0 bg-white/60 dark:bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-20">
            <div className="bg-white dark:bg-slate-800 px-4 py-2.5 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 flex items-center space-x-2.5 text-xs font-semibold text-slate-700 dark:text-slate-200">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <span>{loadingDistrictGeo ? 'Loading District Boundaries...' : 'Synthesizing Geospatial Layers...'}</span>
            </div>
          </div>
        )}

        {/* Dynamic Cartographic Legend */}
        <div className="absolute bottom-4 left-4 bg-white/95 dark:bg-slate-800/95 backdrop-blur-md p-3 rounded-lg border border-slate-200 dark:border-slate-700 shadow-md z-20 text-xs w-64">
          <div className="font-bold text-slate-800 dark:text-slate-100 mb-1 flex items-center justify-between">
            <span>{metricDescriptions[metric].title}</span>
            <span className="text-[10px] font-normal text-slate-500">Choropleth</span>
          </div>
          <p className="text-[11px] text-slate-500 mb-2 leading-tight">
            {metricDescriptions[metric].desc}
          </p>

          {/* Color Scale Bars */}
          {metric === 'risk_concentration' && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[10px]">
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#059669] mr-1.5" /> Low (0–10)</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#2563EB] mr-1.5" /> Medium (10–25)</span>
              </div>
              <div className="flex items-center justify-between text-[10px]">
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#D97706] mr-1.5" /> High (25–50)</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#991B1B] mr-1.5" /> Critical (&gt;50)</span>
              </div>
            </div>
          )}

          {metric === 'project_count' && (
            <div className="space-y-1 text-[10px]">
              <div className="flex items-center justify-between">
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#CBD5E1] mr-1.5" /> &lt;50</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#94A3B8] mr-1.5" /> 50–500</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#64748B] mr-1.5" /> 500–1.5k</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#334155] mr-1.5" /> 1.5k–4k</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#1E293B] mr-1.5" /> 4k–8k</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#0F172A] mr-1.5" /> &gt;8k</span>
              </div>
            </div>
          )}

          {metric === 'sanctioned_funds' && (
            <div className="space-y-1 text-[10px]">
              <div className="flex items-center justify-between">
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#C7D2FE] mr-1.5" /> &lt;₹100 Cr</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#6366F1] mr-1.5" /> ₹100–500 Cr</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#4338CA] mr-1.5" /> ₹500–1500 Cr</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#1E1B4B] mr-1.5" /> &gt;₹3000 Cr</span>
              </div>
            </div>
          )}

          {metric === 'utilization' && (
            <div className="flex items-center justify-between text-[10px]">
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#DC2626] mr-1" /> &lt;45%</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#D97706] mr-1" /> 45–60%</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#059669] mr-1" /> 60–75%</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#047857] mr-1" /> &gt;75%</span>
            </div>
          )}

          {metric === 'completion_rate' && (
            <div className="flex items-center justify-between text-[10px]">
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#DC2626] mr-1" /> &lt;20%</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#D97706] mr-1" /> 20–35%</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#059669] mr-1" /> 35–50%</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#047857] mr-1" /> &gt;50%</span>
            </div>
          )}

          {metric === 'anomalies' && (
            <div className="flex items-center justify-between text-[10px]">
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#10B981] mr-1" /> &lt;4</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#D97706] mr-1" /> 4–12</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#B91C1C] mr-1" /> 12–30</span>
              <span className="flex items-center"><span className="w-3 h-3 rounded-xs bg-[#7F1D1D] mr-1" /> &gt;30</span>
            </div>
          )}
        </div>

        {/* Hover Tooltip Card */}
        {hoveredData && hoveredData.metrics && (
          <div
            className="absolute z-30 pointer-events-none bg-white/95 dark:bg-slate-800/95 backdrop-blur-md rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 p-3 w-64 transition-all"
            style={{
              left: `${Math.min(hoveredData.x + 15, (containerRef.current?.clientWidth || 800) - 275)}px`,
              top: `${Math.min(hoveredData.y + 15, (containerRef.current?.clientHeight || 600) - 230)}px`,
            }}
          >
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-1.5 mb-2">
              <span className="font-bold text-slate-900 dark:text-white uppercase tracking-wide text-xs">
                {hoveredData.name}
              </span>
              <span className="text-[10px] bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 px-1.5 py-0.5 rounded font-mono">
                {hoveredData.type === 'state' ? hoveredData.code || 'STATE' : 'DISTRICT'}
              </span>
            </div>

            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-500">Total Projects:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  {formatNumber(hoveredData.metrics.projectCount || 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Sanctioned Funds:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  {formatCurrency(hoveredData.metrics.sanctionedAmount || 0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Fund Utilization:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  {hoveredData.metrics.utilizationPct || hoveredData.metrics.utilizationRate || 0}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Work Completion:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  {hoveredData.metrics.completionPct || hoveredData.metrics.completionRate || 0}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Average Risk Score:</span>
                <span className="font-bold text-amber-600 dark:text-amber-400">
                  {hoveredData.metrics.avgRiskScore || 0} / 100
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">High-Risk Signals:</span>
                <span className="font-bold text-red-600 dark:text-red-400">
                  {hoveredData.metrics.riskSignals || hoveredData.metrics.highSignals || 0}
                </span>
              </div>
            </div>

            <div className="mt-2 pt-1.5 border-t border-slate-200 dark:border-slate-700 text-[10px] text-blue-600 dark:text-blue-400 font-medium flex items-center justify-center">
              Click to drill down into {hoveredData.type === 'state' ? 'districts' : 'details'} →
            </div>
          </div>
        )}

        {/* District Intelligence Sliding Drawer (Section 16 & 47) */}
        {selectedDistrictName && (
          <div className="absolute top-0 right-0 bottom-0 w-full sm:w-96 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl z-30 flex flex-col animate-slideLeft overflow-hidden">
            {/* Drawer Header */}
            <div className="bg-slate-900 text-white p-4 flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-1.5 text-xs text-blue-400 font-medium uppercase tracking-wider">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>{selectedStateName}</span>
                </div>
                <h3 className="text-lg font-extrabold tracking-tight mt-0.5">
                  {selectedDistrictName}
                </h3>
              </div>
              <button
                onClick={() => setSelectedDistrictName(null)}
                className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
              {loadingDistrictIntel ? (
                <div className="py-12 text-center text-slate-500">
                  <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  Loading District Intelligence...
                </div>
              ) : districtIntelligence ? (
                <>
                  {/* Overview KPI Grid */}
                  <div className="grid grid-cols-2 gap-2.5">
                    <div className="bg-slate-50 dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700">
                      <span className="text-[10px] text-slate-500 block">Total Works</span>
                      <span className="text-base font-bold text-slate-900 dark:text-white">
                        {formatNumber(districtIntelligence.totalProjects)}
                      </span>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700">
                      <span className="text-[10px] text-slate-500 block">Sanctioned Funds</span>
                      <span className="text-base font-bold text-slate-900 dark:text-white">
                        {formatCurrency(districtIntelligence.totalSanctioned)}
                      </span>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700">
                      <span className="text-[10px] text-slate-500 block">Utilization</span>
                      <span className="text-base font-bold text-emerald-600 dark:text-emerald-400">
                        {districtIntelligence.utilizationPct}%
                      </span>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700">
                      <span className="text-[10px] text-slate-500 block">Completion Rate</span>
                      <span className="text-base font-bold text-blue-600 dark:text-blue-400">
                        {districtIntelligence.completionPct}%
                      </span>
                    </div>
                  </div>

                  {/* Analytical Signals Section */}
                  <div className="bg-amber-50/70 dark:bg-amber-950/30 p-3 rounded-lg border border-amber-200 dark:border-amber-900/50 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-amber-900 dark:text-amber-200 flex items-center">
                        <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />
                        Analytical Signals Breakdown
                      </span>
                      <span className="bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200 text-[10px] font-bold px-1.5 py-0.5 rounded">
                        {districtIntelligence.riskSignals} Signals
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                      <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded border border-amber-100 dark:border-amber-900/30">
                        <span className="text-slate-500 block text-[10px]">Cost Anomalies</span>
                        <span className="font-bold text-slate-800 dark:text-slate-100">
                          {districtIntelligence.signalsBreakdown?.costAnomalies || 0}
                        </span>
                      </div>
                      <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded border border-amber-100 dark:border-amber-900/30">
                        <span className="text-slate-500 block text-[10px]">Progress Gaps</span>
                        <span className="font-bold text-slate-800 dark:text-slate-100">
                          {districtIntelligence.signalsBreakdown?.progressGaps || 0}
                        </span>
                      </div>
                      <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded border border-amber-100 dark:border-amber-900/30">
                        <span className="text-slate-500 block text-[10px]">Potential Duplicates</span>
                        <span className="font-bold text-slate-800 dark:text-slate-100">
                          {districtIntelligence.signalsBreakdown?.potentialDuplicates || 0}
                        </span>
                      </div>
                      <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded border border-amber-100 dark:border-amber-900/30">
                        <span className="text-slate-500 block text-[10px]">Evidence Coverage</span>
                        <span className="font-bold text-slate-800 dark:text-slate-100">
                          {districtIntelligence.avgEvidenceCoverage}%
                        </span>
                      </div>
                    </div>

                    <p className="text-[10px] text-amber-800/80 dark:text-amber-300/80 italic pt-1">
                      * {districtIntelligence.signalsOverlapNote}
                    </p>
                  </div>

                  {/* Top Work Categories */}
                  {districtIntelligence.categories && districtIntelligence.categories.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="font-semibold text-slate-700 dark:text-slate-300 block text-[11px]">
                        Dominant Project Sectors
                      </span>
                      <div className="space-y-1">
                        {districtIntelligence.categories.map((c: any, idx: number) => (
                          <div key={idx} className="flex justify-between items-center bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded">
                            <span className="text-slate-600 dark:text-slate-300 truncate max-w-[180px]">{c.category}</span>
                            <span className="font-medium text-slate-800 dark:text-slate-200">{c.count} works</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Top High-Risk Projects */}
                  {districtIntelligence.topProjects && districtIntelligence.topProjects.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="font-semibold text-slate-700 dark:text-slate-300 block text-[11px]">
                        High-Risk Works Requiring Review
                      </span>
                      <div className="space-y-1.5">
                        {districtIntelligence.topProjects.map((p: any) => (
                          <div
                            key={p.work_code}
                            onClick={() => navigate(`/projects/${encodeURIComponent(p.work_code)}`)}
                            className="bg-white dark:bg-slate-800 p-2 rounded border border-slate-200 dark:border-slate-700 hover:border-blue-400 cursor-pointer transition-all space-y-1"
                          >
                            <div className="flex justify-between items-center">
                              <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{p.work_code}</span>
                              <span className="bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300 text-[9px] font-bold px-1.5 py-0.5 rounded">
                                Score: {p.overall_risk_score}
                              </span>
                            </div>
                            <p className="text-slate-600 dark:text-slate-300 truncate">{p.work_type || p.category}</p>
                            <div className="flex justify-between text-[10px] text-slate-400">
                              <span>{formatCurrency(p.sanctioned_amount)}</span>
                              <span>{p.status}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons: Navigate to Project Explorer & Alerts */}
                  <div className="pt-2 space-y-2">
                    <button
                      onClick={() => navigate(`/projects?state=${encodeURIComponent(selectedStateName || '')}&district=${encodeURIComponent(selectedDistrictName)}`)}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-3 rounded-lg flex items-center justify-center space-x-1.5 shadow-xs transition-colors"
                    >
                      <span>Explore District Projects</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={() => navigate(`/alerts?state=${encodeURIComponent(selectedStateName || '')}&district=${encodeURIComponent(selectedDistrictName)}`)}
                      className="w-full bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-medium py-2 px-3 rounded-lg flex items-center justify-center space-x-1.5 border border-slate-300 dark:border-slate-600 transition-colors"
                    >
                      <ShieldAlert className="w-3.5 h-3.5 mr-1 text-amber-600" />
                      <span>View District Risk Alerts</span>
                    </button>
                  </div>
                </>
              ) : (
                <div className="py-8 text-center text-slate-400">
                  No detailed analytical records for this district.
                </div>
              )}
            </div>
          </div>
        )}

        {/* "What am I looking at?" Explainer Modal (Section 26) */}
        {showExplainer && (
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-40">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 max-w-md w-full p-5 space-y-3.5">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center text-sm">
                  <Info className="w-4 h-4 text-blue-600 mr-1.5" />
                  What am I looking at?
                </h4>
                <button onClick={() => setShowExplainer(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                <p>
                  <strong>Administrative Geographic Aggregation:</strong> Every polygon represents a verified Indian State or District boundary. Colors reflect aggregate metrics computed across canonical MPLADS projects.
                </p>
                <p>
                  <strong>Zero Coordinate Fabrication:</strong> Project-level GPS coordinates are unavailable in the source dataset. The platform strictly aggregates data at district and state boundaries to maintain scientific and legal integrity.
                </p>
                <p>
                  <strong>Decision Support Tool:</strong> Analytical risk scores and anomaly highlights prioritize records for desk audit and physical verification. They do not constitute legal conclusions.
                </p>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => setShowExplainer(false)}
                  className="bg-blue-600 text-white text-xs font-semibold px-4 py-1.5 rounded-lg hover:bg-blue-700"
                >
                  Got It
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
