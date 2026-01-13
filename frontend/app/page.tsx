'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Dashboard } from '@/components/Dashboard';
import { MapView } from '@/components/MapView';
import { AnalysisPanel } from '@/components/AnalysisPanel';
import { AISiteScout } from '@/components/AISiteScout';
import { MarketDashboard } from '@/components/MarketDashboard';
import { FinancialModeler } from '@/components/FinancialModeler';
import {
  LayoutDashboard,
  Map,
  Sparkles,
  TrendingUp,
  Calculator,
  FolderKanban,
  Bell,
  Settings,
  Zap,
  Menu,
  X,
} from 'lucide-react';

type ViewType = 'dashboard' | 'scout' | 'map' | 'market' | 'financial' | 'pipeline';

export default function Home() {
  const [selectedParcelId, setSelectedParcelId] = useState<string | null>(null);
  const [view, setView] = useState<ViewType>('scout');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.stats(),
  });

  const navigation = [
    { id: 'scout' as const, name: 'AI Site Scout', icon: Sparkles, badge: 'AI' },
    { id: 'dashboard' as const, name: 'Dashboard', icon: LayoutDashboard },
    { id: 'map' as const, name: 'Site Explorer', icon: Map },
    { id: 'market' as const, name: 'Market Intelligence', icon: TrendingUp, badge: 'LIVE' },
    { id: 'financial' as const, name: 'Financial Modeler', icon: Calculator },
    { id: 'pipeline' as const, name: 'Project Pipeline', icon: FolderKanban },
  ];

  return (
    <div className="h-screen flex bg-gray-100 dark:bg-gray-900">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarCollapsed ? 'w-16' : 'w-64'
        } bg-gray-900 flex flex-col transition-all duration-300 flex-shrink-0`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-terra-500 to-jinki-500 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="font-bold text-lg text-white">TerraJinki</span>
                <span className="text-[10px] ml-1 px-1.5 py-0.5 bg-terra-500 text-white rounded font-medium">v2.0</span>
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1.5 rounded-lg hover:bg-gray-800 transition-colors"
          >
            {sidebarCollapsed ? (
              <Menu className="w-5 h-5 text-gray-400" />
            ) : (
              <X className="w-5 h-5 text-gray-400" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = view === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setView(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-terra-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && (
                  <>
                    <span className="font-medium flex-1 text-left">{item.name}</span>
                    {item.badge && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                        item.badge === 'AI' ? 'bg-purple-500 text-white' :
                        item.badge === 'LIVE' ? 'bg-green-500 text-white' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </button>
            );
          })}
        </nav>

        {/* Stats Footer */}
        {!sidebarCollapsed && stats && (
          <div className="px-4 py-4 border-t border-gray-800">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-2xl font-bold text-white">{stats.parcels_count?.toLocaleString() || '2,000+'}</div>
                <div className="text-xs text-gray-400">Parcels</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-2xl font-bold text-white">50</div>
                <div className="text-xs text-gray-400">States</div>
              </div>
            </div>
          </div>
        )}

        {/* Settings */}
        <div className="px-2 py-4 border-t border-gray-800">
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-colors">
            <Settings className="w-5 h-5 flex-shrink-0" />
            {!sidebarCollapsed && <span className="font-medium">Settings</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 flex items-center justify-between flex-shrink-0">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              {navigation.find(n => n.id === view)?.name}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {view === 'scout' && 'Find optimal sites with natural language search'}
              {view === 'dashboard' && 'Overview of your renewable energy portfolio'}
              {view === 'map' && 'Interactive map with all 50 US states'}
              {view === 'market' && 'Real-time market data and intelligence'}
              {view === 'financial' && 'Project financial modeling and analysis'}
              {view === 'pipeline' && 'Track projects from prospecting to COD'}
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Notifications */}
            <button className="relative p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>

            {/* Stats Badge */}
            {stats && (
              <div className="flex gap-2">
                <span className="px-3 py-1 bg-terra-100 text-terra-700 rounded-full text-sm font-medium">
                  {stats.parcels_count?.toLocaleString() || '2,000+'} Parcels
                </span>
              </div>
            )}
          </div>
        </header>

        {/* View Content */}
        <div className="flex-1 overflow-hidden flex">
          {view === 'scout' && (
            <>
              <div className="flex-1">
                <AISiteScout onSelectParcel={setSelectedParcelId} />
              </div>
              {selectedParcelId && (
                <div className="w-96 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <AnalysisPanel
                    parcelId={selectedParcelId}
                    onClose={() => setSelectedParcelId(null)}
                  />
                </div>
              )}
            </>
          )}

          {view === 'dashboard' && (
            <>
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
            </>
          )}

          {view === 'map' && (
            <>
              <div className="flex-1">
                <MapView onSelectParcel={setSelectedParcelId} />
              </div>
              {selectedParcelId && (
                <div className="w-96 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                  <AnalysisPanel
                    parcelId={selectedParcelId}
                    onClose={() => setSelectedParcelId(null)}
                  />
                </div>
              )}
            </>
          )}

          {view === 'market' && <MarketDashboard />}

          {view === 'financial' && <FinancialModeler />}

          {view === 'pipeline' && (
            <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
              <div className="text-center">
                <FolderKanban className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Project Pipeline Coming Soon
                </h3>
                <p className="text-gray-500 max-w-md">
                  Track projects through the full development lifecycle: Prospecting → Site Control → Permitting → Interconnection → Construction → COD
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
