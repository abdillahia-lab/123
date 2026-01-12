'use client';

import { useRef, useCallback, useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import Map, { Marker, Popup, NavigationControl, Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Zap, Search, Filter, Layers, Sun, Wind, Grid3X3, MapPin, X, ChevronDown } from 'lucide-react';

interface MapViewProps {
  onSelectParcel: (id: string) => void;
}

interface Parcel {
  id: string;
  county: string;
  state: string;
  state_code: string;
  acreage: number;
  latitude: number;
  longitude: number;
  overall_score: number;
  solar_score: number;
  wind_score: number;
  viability: string;
  zoning_type: string;
  owner_name: string;
  solar_ghi: number;
  wind_speed: number;
  solar_capacity_mw: number;
  nearest_substation_mi: number;
}

const US_STATES = [
  { code: 'ALL', name: 'All States' },
  { code: 'AL', name: 'Alabama' }, { code: 'AK', name: 'Alaska' }, { code: 'AZ', name: 'Arizona' },
  { code: 'AR', name: 'Arkansas' }, { code: 'CA', name: 'California' }, { code: 'CO', name: 'Colorado' },
  { code: 'CT', name: 'Connecticut' }, { code: 'DE', name: 'Delaware' }, { code: 'FL', name: 'Florida' },
  { code: 'GA', name: 'Georgia' }, { code: 'HI', name: 'Hawaii' }, { code: 'ID', name: 'Idaho' },
  { code: 'IL', name: 'Illinois' }, { code: 'IN', name: 'Indiana' }, { code: 'IA', name: 'Iowa' },
  { code: 'KS', name: 'Kansas' }, { code: 'KY', name: 'Kentucky' }, { code: 'LA', name: 'Louisiana' },
  { code: 'ME', name: 'Maine' }, { code: 'MD', name: 'Maryland' }, { code: 'MA', name: 'Massachusetts' },
  { code: 'MI', name: 'Michigan' }, { code: 'MN', name: 'Minnesota' }, { code: 'MS', name: 'Mississippi' },
  { code: 'MO', name: 'Missouri' }, { code: 'MT', name: 'Montana' }, { code: 'NE', name: 'Nebraska' },
  { code: 'NV', name: 'Nevada' }, { code: 'NH', name: 'New Hampshire' }, { code: 'NJ', name: 'New Jersey' },
  { code: 'NM', name: 'New Mexico' }, { code: 'NY', name: 'New York' }, { code: 'NC', name: 'North Carolina' },
  { code: 'ND', name: 'North Dakota' }, { code: 'OH', name: 'Ohio' }, { code: 'OK', name: 'Oklahoma' },
  { code: 'OR', name: 'Oregon' }, { code: 'PA', name: 'Pennsylvania' }, { code: 'RI', name: 'Rhode Island' },
  { code: 'SC', name: 'South Carolina' }, { code: 'SD', name: 'South Dakota' }, { code: 'TN', name: 'Tennessee' },
  { code: 'TX', name: 'Texas' }, { code: 'UT', name: 'Utah' }, { code: 'VT', name: 'Vermont' },
  { code: 'VA', name: 'Virginia' }, { code: 'WA', name: 'Washington' }, { code: 'WV', name: 'West Virginia' },
  { code: 'WI', name: 'Wisconsin' }, { code: 'WY', name: 'Wyoming' }
];

export function MapView({ onSelectParcel }: MapViewProps) {
  const mapRef = useRef<any>(null);
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedState, setSelectedState] = useState('ALL');
  const [showFilters, setShowFilters] = useState(false);
  const [minScore, setMinScore] = useState(0);
  const [minAcreage, setMinAcreage] = useState(0);
  const [activeLayer, setActiveLayer] = useState<'score' | 'solar' | 'wind'>('score');
  const [showStateDropdown, setShowStateDropdown] = useState(false);

  // Build query params
  const queryParams = useMemo(() => {
    const params = new URLSearchParams();
    params.set('limit', '500');
    if (selectedState !== 'ALL') params.set('states', selectedState);
    if (minScore > 0) params.set('minScore', String(minScore));
    if (minAcreage > 0) params.set('minAcreage', String(minAcreage));
    if (searchQuery) params.set('q', searchQuery);
    return params.toString();
  }, [selectedState, minScore, minAcreage, searchQuery]);

  // Fetch parcels from API
  const { data, isLoading } = useQuery({
    queryKey: ['parcels', queryParams],
    queryFn: async () => {
      const res = await fetch(`/api/parcels?${queryParams}`);
      return res.json();
    },
  });

  const parcels: Parcel[] = data?.parcels || [];
  const totalCount = data?.meta?.totalParcels || 0;
  const filteredCount = data?.pagination?.total || parcels.length;

  const getMarkerColor = useCallback((parcel: Parcel) => {
    let value: number;
    switch (activeLayer) {
      case 'solar':
        value = parcel.solar_score;
        break;
      case 'wind':
        value = parcel.wind_score;
        break;
      default:
        value = parcel.overall_score;
    }

    if (value >= 85) return '#22c55e'; // Green - Excellent
    if (value >= 70) return '#84cc16'; // Lime - Good
    if (value >= 55) return '#eab308'; // Yellow - Moderate
    if (value >= 40) return '#f97316'; // Orange - Challenging
    return '#ef4444'; // Red - Poor
  }, [activeLayer]);

  const getMarkerSize = useCallback((parcel: Parcel) => {
    if (parcel.acreage >= 500) return 32;
    if (parcel.acreage >= 200) return 28;
    if (parcel.acreage >= 100) return 24;
    return 20;
  }, []);

  const handleMarkerClick = useCallback((parcel: Parcel) => {
    setSelectedParcel(parcel);
  }, []);

  const handleStateSelect = (code: string) => {
    setSelectedState(code);
    setShowStateDropdown(false);

    // Zoom to state if not "ALL"
    if (code !== 'ALL' && mapRef.current) {
      const stateCoords: Record<string, [number, number, number]> = {
        TX: [-99.9, 31.0, 5], CA: [-119.4, 37.2, 5.5], AZ: [-111.4, 34.0, 6],
        FL: [-81.5, 27.6, 6], NY: [-74.0, 42.0, 6], VA: [-78.5, 37.5, 6.5],
        // Add more as needed
      };
      const coords = stateCoords[code] || [-98.5, 39.8, 4];
      mapRef.current.flyTo({
        center: [coords[0], coords[1]],
        zoom: coords[2],
        duration: 1500
      });
    } else if (code === 'ALL' && mapRef.current) {
      mapRef.current.flyTo({
        center: [-98.5, 39.8],
        zoom: 4,
        duration: 1500
      });
    }
  };

  return (
    <div className="h-full relative">
      {/* Top controls */}
      <div className="absolute top-4 left-4 right-4 z-10 flex gap-3 flex-wrap">
        {/* Search */}
        <div className="flex-1 min-w-[200px] max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by county, state, or owner..."
              className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg text-gray-900 dark:text-white placeholder-gray-500 text-sm"
            />
          </div>
        </div>

        {/* State selector */}
        <div className="relative">
          <button
            onClick={() => setShowStateDropdown(!showStateDropdown)}
            className="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <MapPin className="w-4 h-4" />
            {selectedState === 'ALL' ? 'All States' : selectedState}
            <ChevronDown className="w-4 h-4" />
          </button>
          {showStateDropdown && (
            <div className="absolute top-full mt-1 w-48 max-h-64 overflow-y-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50">
              {US_STATES.map(state => (
                <button
                  key={state.code}
                  onClick={() => handleStateSelect(state.code)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                    selectedState === state.code ? 'bg-terra-50 dark:bg-terra-900/30 text-terra-700 dark:text-terra-400' : 'text-gray-700 dark:text-gray-300'
                  }`}
                >
                  {state.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Layer toggle */}
        <div className="flex bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden">
          <button
            onClick={() => setActiveLayer('score')}
            className={`px-3 py-2.5 text-sm font-medium flex items-center gap-1.5 ${
              activeLayer === 'score' ? 'bg-terra-600 text-white' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            <Grid3X3 className="w-4 h-4" />
            Score
          </button>
          <button
            onClick={() => setActiveLayer('solar')}
            className={`px-3 py-2.5 text-sm font-medium flex items-center gap-1.5 border-l border-gray-200 dark:border-gray-700 ${
              activeLayer === 'solar' ? 'bg-amber-500 text-white' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            <Sun className="w-4 h-4" />
            Solar
          </button>
          <button
            onClick={() => setActiveLayer('wind')}
            className={`px-3 py-2.5 text-sm font-medium flex items-center gap-1.5 border-l border-gray-200 dark:border-gray-700 ${
              activeLayer === 'wind' ? 'bg-blue-500 text-white' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            <Wind className="w-4 h-4" />
            Wind
          </button>
        </div>

        {/* Filters toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`px-4 py-2.5 border rounded-lg shadow-lg text-sm font-medium flex items-center gap-2 ${
            showFilters ? 'bg-terra-600 text-white border-terra-600' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
          }`}
        >
          <Filter className="w-4 h-4" />
          Filters
        </button>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="absolute top-20 left-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4 w-72">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Filters</h3>
            <button onClick={() => setShowFilters(false)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Minimum Score: {minScore}
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Minimum Acreage: {minAcreage}
              </label>
              <input
                type="range"
                min="0"
                max="500"
                step="50"
                value={minAcreage}
                onChange={(e) => setMinAcreage(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
            </div>
            <button
              onClick={() => { setMinScore(0); setMinAcreage(0); setSelectedState('ALL'); }}
              className="w-full py-2 text-sm text-terra-600 hover:text-terra-700 font-medium"
            >
              Reset Filters
            </button>
          </div>
        </div>
      )}

      {/* Stats bar */}
      <div className="absolute top-4 right-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg px-4 py-2.5 border border-gray-200 dark:border-gray-700 flex items-center gap-4">
        <div className="text-center">
          <div className="text-lg font-bold text-gray-900 dark:text-white">{filteredCount.toLocaleString()}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Visible</div>
        </div>
        <div className="w-px h-8 bg-gray-200 dark:bg-gray-700"></div>
        <div className="text-center">
          <div className="text-lg font-bold text-terra-600">{totalCount.toLocaleString()}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Total US</div>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 border border-gray-200 dark:border-gray-700">
        <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
          {activeLayer === 'solar' ? 'Solar Potential' : activeLayer === 'wind' ? 'Wind Potential' : 'Site Score'}
        </h4>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Excellent (85+)</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-lime-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Good (70-84)</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Moderate (55-69)</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Challenging (40-54)</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Poor (&lt;40)</span>
          </div>
        </div>
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute inset-0 z-20 bg-white/50 dark:bg-gray-900/50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-terra-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-gray-700 dark:text-gray-300">Loading parcels...</span>
          </div>
        </div>
      )}

      {/* Map - centered on continental US */}
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: -98.5,
          latitude: 39.8,
          zoom: 4,
        }}
        style={{ width: '100%', height: '100%' }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
      >
        <NavigationControl position="bottom-right" />

        {/* Parcel markers */}
        {parcels.map((parcel) => (
          <Marker
            key={parcel.id}
            longitude={parcel.longitude}
            latitude={parcel.latitude}
            anchor="center"
            onClick={() => handleMarkerClick(parcel)}
          >
            <div
              className="cursor-pointer transform hover:scale-125 transition-transform duration-150"
              style={{
                width: getMarkerSize(parcel),
                height: getMarkerSize(parcel),
                borderRadius: '50%',
                backgroundColor: getMarkerColor(parcel),
                border: '3px solid white',
                boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {activeLayer === 'solar' ? (
                <Sun className="w-3 h-3 text-white" />
              ) : activeLayer === 'wind' ? (
                <Wind className="w-3 h-3 text-white" />
              ) : (
                <Zap className="w-3 h-3 text-white" />
              )}
            </div>
          </Marker>
        ))}

        {/* Popup */}
        {selectedParcel && (
          <Popup
            longitude={selectedParcel.longitude}
            latitude={selectedParcel.latitude}
            anchor="bottom"
            onClose={() => setSelectedParcel(null)}
            closeButton={true}
            closeOnClick={false}
            className="terra-popup"
            maxWidth="320px"
          >
            <div className="p-3">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900 text-lg">
                    {selectedParcel.county}
                  </h3>
                  <p className="text-sm text-gray-500">{selectedParcel.state}</p>
                </div>
                <div
                  className="px-2.5 py-1 rounded-full text-sm font-bold text-white"
                  style={{ backgroundColor: getMarkerColor(selectedParcel) }}
                >
                  {selectedParcel.overall_score}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="bg-gray-50 rounded-lg p-2">
                  <div className="text-xs text-gray-500">Acreage</div>
                  <div className="font-semibold text-gray-900">{selectedParcel.acreage.toLocaleString()}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-2">
                  <div className="text-xs text-gray-500">Capacity</div>
                  <div className="font-semibold text-gray-900">{selectedParcel.solar_capacity_mw} MW</div>
                </div>
                <div className="bg-amber-50 rounded-lg p-2">
                  <div className="text-xs text-amber-600 flex items-center gap-1">
                    <Sun className="w-3 h-3" /> Solar GHI
                  </div>
                  <div className="font-semibold text-gray-900">{selectedParcel.solar_ghi} kWh/m²</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-2">
                  <div className="text-xs text-blue-600 flex items-center gap-1">
                    <Wind className="w-3 h-3" /> Wind
                  </div>
                  <div className="font-semibold text-gray-900">{selectedParcel.wind_speed} m/s</div>
                </div>
              </div>

              <div className="text-sm text-gray-600 mb-3 space-y-1">
                <p><span className="text-gray-500">Zoning:</span> {selectedParcel.zoning_type}</p>
                <p><span className="text-gray-500">Grid:</span> {selectedParcel.nearest_substation_mi.toFixed(1)} mi to substation</p>
                <p className="text-xs text-gray-400 truncate">{selectedParcel.owner_name}</p>
              </div>

              <button
                onClick={() => onSelectParcel(selectedParcel.id)}
                className="w-full px-4 py-2.5 bg-gradient-to-r from-terra-600 to-jinki-600 text-white text-sm font-medium rounded-lg hover:from-terra-700 hover:to-jinki-700 transition-all shadow-md"
              >
                Run AI Analysis
              </button>
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
}
