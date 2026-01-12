'use client';

import { useRef, useCallback, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Map, { Marker, Popup, NavigationControl } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Zap, Search } from 'lucide-react';

interface MapViewProps {
  onSelectParcel: (id: string) => void;
}

interface Parcel {
  id: string;
  county: string;
  state: string;
  acreage: number;
  latitude: number;
  longitude: number;
  score?: number;
  viability?: string;
  zoning_type?: string;
  owner_name?: string;
}

export function MapView({ onSelectParcel }: MapViewProps) {
  const mapRef = useRef<any>(null);
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch parcels from API
  const { data: parcels = [] } = useQuery<Parcel[]>({
    queryKey: ['parcels'],
    queryFn: async () => {
      const res = await fetch('/api/parcels');
      return res.json();
    },
  });

  const getMarkerColor = (score?: number) => {
    if (!score) return '#6b7280'; // Gray for no score
    if (score >= 80) return '#22c55e'; // Green
    if (score >= 60) return '#eab308'; // Yellow
    if (score >= 40) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  const handleMarkerClick = useCallback((parcel: Parcel) => {
    setSelectedParcel(parcel);
  }, []);

  // Filter parcels by search
  const filteredParcels = parcels.filter((p) =>
    !searchQuery ||
    p.county.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.state.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.owner_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full relative">
      {/* Search overlay */}
      <div className="absolute top-4 left-4 right-4 z-10 flex gap-4">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search parcels by county, owner..."
              className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg text-gray-900 dark:text-white placeholder-gray-500"
            />
          </div>
        </div>

        <div className="flex gap-2">
          <button className="px-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
            Filters
          </button>
          <button className="px-4 py-2.5 bg-terra-600 text-white rounded-lg shadow-lg text-sm font-medium hover:bg-terra-700">
            Draw Area
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3 border border-gray-200 dark:border-gray-700">
        <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
          Site Score
        </h4>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Excellent (80+)</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Good (60-79)</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Fair (40-59)</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-gray-700 dark:text-gray-300">Poor (&lt;40)</span>
          </div>
        </div>
      </div>

      {/* Parcel count badge */}
      <div className="absolute top-4 right-4 z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg px-3 py-2 border border-gray-200 dark:border-gray-700">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {filteredParcels.length} parcels in Virginia
        </span>
      </div>

      {/* Map - centered on Virginia */}
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: -78.5,
          latitude: 38.5,
          zoom: 7,
        }}
        style={{ width: '100%', height: '100%' }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
      >
        <NavigationControl position="bottom-right" />

        {/* Parcel markers */}
        {filteredParcels.map((parcel) => (
          <Marker
            key={parcel.id}
            longitude={parcel.longitude}
            latitude={parcel.latitude}
            anchor="center"
            onClick={() => handleMarkerClick(parcel)}
          >
            <div
              className="cursor-pointer transform hover:scale-110 transition-transform"
              style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                backgroundColor: getMarkerColor(parcel.score),
                border: '3px solid white',
                boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Zap className="w-3.5 h-3.5 text-white" />
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
          >
            <div className="p-3 min-w-[220px]">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-900">
                  {selectedParcel.county}, {selectedParcel.state}
                </h3>
                {selectedParcel.score && (
                  <span
                    className="px-2 py-0.5 rounded-full text-xs font-bold text-white"
                    style={{ backgroundColor: getMarkerColor(selectedParcel.score) }}
                  >
                    {selectedParcel.score}
                  </span>
                )}
              </div>
              <div className="text-sm text-gray-600 space-y-1.5">
                <p><strong>{selectedParcel.acreage}</strong> acres</p>
                <p>Est. capacity: <strong>{Math.round(selectedParcel.acreage / 5)} MW</strong></p>
                {selectedParcel.zoning_type && (
                  <p>Zoning: {selectedParcel.zoning_type}</p>
                )}
                {selectedParcel.owner_name && (
                  <p className="text-gray-500 text-xs">{selectedParcel.owner_name}</p>
                )}
              </div>
              <button
                onClick={() => onSelectParcel(selectedParcel.id)}
                className="mt-3 w-full px-3 py-2 bg-gradient-to-r from-terra-600 to-jinki-600 text-white text-sm font-medium rounded-lg hover:from-terra-700 hover:to-jinki-700 transition-all"
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
