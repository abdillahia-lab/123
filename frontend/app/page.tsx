'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Dashboard } from '@/components/Dashboard';
import { MapView } from '@/components/MapView';
import { AnalysisPanel } from '@/components/AnalysisPanel';

export default function Home() {
  const [selectedParcelId, setSelectedParcelId] = useState<string | null>(null);
  const [view, setView] = useState<'dashboard' | 'map'>('dashboard');

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.stats(),
  });

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              TerraJinki
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              AI-Powered Renewable Energy Site Intelligence
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* View toggle */}
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setView('dashboard')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  view === 'dashboard'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setView('map')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  view === 'map'
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                Map
              </button>
            </div>

            {/* Stats */}
            {stats && (
              <div className="flex gap-4 text-sm">
                <div className="px-3 py-1 bg-terra-100 text-terra-700 rounded-full">
                  {stats.parcels_count} Parcels
                </div>
                <div className="px-3 py-1 bg-jinki-100 text-jinki-700 rounded-full">
                  {stats.projects_count} Projects
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {view === 'dashboard' ? (
          <div className="h-full flex">
            <div className="flex-1 overflow-hidden">
              <Dashboard onSelectParcel={setSelectedParcelId} />
            </div>
            {selectedParcelId && (
              <div className="w-96 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                <AnalysisPanel
                  parcelId={selectedParcelId}
                  onClose={() => setSelectedParcelId(null)}
                />
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex">
            <div className="flex-1">
              <MapView onSelectParcel={setSelectedParcelId} />
            </div>
            {selectedParcelId && (
              <div className="w-96 border-l border-gray-200 dark:border-gray-700">
                <AnalysisPanel
                  parcelId={selectedParcelId}
                  onClose={() => setSelectedParcelId(null)}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
