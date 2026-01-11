'use client';

import { useRef, useCallback, useState } from 'react';
import Map, { Marker, Popup, NavigationControl, Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapPin, Zap, Search } from 'lucide-react';

interface MapViewProps {
  onSelectParcel: (id: string) => void;
}

// Sample data - would come from API in production
const sampleParcels = [
  { id: '1', lat: 29.7604, lng: -95.3698, score: 85, county: 'Harris', state: 'TX', acreage: 75 },
  { id: '2', lat: 30.2672, lng: -97.7431, score: 72, county: 'Travis', state: 'TX', acreage: 120 },
  { id: '3', lat: 32.7767, lng: -96.7970, score: 68, county: 'Dallas', state: 'TX', acreage: 45 },
  { id: '4', lat: 29.4241, lng: -98.4936, score: 91, county: 'Bexar', state: 'TX', acreage: 200 },
];

export function MapView({ onSelectParcel }: MapViewProps) {
  const mapRef = useRef<any>(null);
  const [selectedParcel, setSelectedParcel] = useState<typeof sampleParcels[0] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const getMarkerColor = (score: number) => {
    if (score >= 80) return '#22c55e'; // Green
    if (score >= 60) return '#eab308'; // Yellow
    if (score >= 40) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  const handleMarkerClick = useCallback((parcel: typeof sampleParcels[0]) => {
    setSelectedParcel(parcel);
  }, []);

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
              placeholder="Search parcels by location, owner, or APN..."
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

      {/* Map */}
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: -97.0,
          latitude: 31.0,
          zoom: 5.5,
        }}
        style={{ width: '100%', height: '100%' }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
      >
        <NavigationControl position="bottom-right" />

        {/* Parcel markers */}
        {sampleParcels.map((parcel) => (
          <Marker
            key={parcel.id}
            longitude={parcel.lng}
            latitude={parcel.lat}
            anchor="center"
            onClick={() => handleMarkerClick(parcel)}
          >
            <div
              className="cursor-pointer transform hover:scale-110 transition-transform"
              style={{
                width: 24,
                height: 24,
                borderRadius: '50%',
                backgroundColor: getMarkerColor(parcel.score),
                border: '2px solid white',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Zap className="w-3 h-3 text-white" />
            </div>
          </Marker>
        ))}

        {/* Popup */}
        {selectedParcel && (
          <Popup
            longitude={selectedParcel.lng}
            latitude={selectedParcel.lat}
            anchor="bottom"
            onClose={() => setSelectedParcel(null)}
            closeButton={true}
            closeOnClick={false}
            className="terra-popup"
          >
            <div className="p-2 min-w-[200px]">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-900">
                  {selectedParcel.county}, {selectedParcel.state}
                </h3>
                <span
                  className="px-2 py-0.5 rounded-full text-xs font-medium text-white"
                  style={{ backgroundColor: getMarkerColor(selectedParcel.score) }}
                >
                  {selectedParcel.score}
                </span>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <p>{selectedParcel.acreage} acres</p>
                <p>Est. capacity: {Math.round(selectedParcel.acreage / 6)} MW</p>
              </div>
              <button
                onClick={() => onSelectParcel(selectedParcel.id)}
                className="mt-3 w-full px-3 py-1.5 bg-terra-600 text-white text-sm font-medium rounded-md hover:bg-terra-700"
              >
                Analyze Site
              </button>
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
}
