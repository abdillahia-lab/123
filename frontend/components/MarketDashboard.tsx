'use client';

import { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Sun,
  Wind,
  Battery,
  AlertCircle,
  Bell,
  DollarSign,
  Clock,
  RefreshCw,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import {
  getElectricityPrices,
  getPPARates,
  getIncentivePrograms,
  getInterconnectionQueues,
  getCommodityPrices,
  getMarketAlerts,
  type ElectricityPrice,
  type PPARate,
  type IncentiveProgram,
  type InterconnectionQueue,
  type CommodityPrice,
  type MarketAlert,
} from '@/lib/market-data';

export function MarketDashboard() {
  const [prices, setPrices] = useState<ElectricityPrice[]>([]);
  const [ppaRates, setPPARates] = useState<PPARate[]>([]);
  const [incentives, setIncentives] = useState<IncentiveProgram[]>([]);
  const [queues, setQueues] = useState<InterconnectionQueue[]>([]);
  const [commodities, setCommodities] = useState<CommodityPrice[]>([]);
  const [alerts, setAlerts] = useState<MarketAlert[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'prices' | 'incentives' | 'queues' | 'commodities'>('prices');

  const refreshData = () => {
    setIsRefreshing(true);
    setPrices(getElectricityPrices());
    setPPARates(getPPARates());
    setIncentives(getIncentivePrograms());
    setQueues(getInterconnectionQueues());
    setCommodities(getCommodityPrices());
    setAlerts(getMarketAlerts());
    setLastUpdate(new Date());
    setTimeout(() => setIsRefreshing(false), 500);
  };

  useEffect(() => {
    refreshData();
    // Simulate real-time updates every 30 seconds
    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Market Intelligence
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Real-time energy market data and insights
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
            <button
              onClick={refreshData}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-3 py-1.5 bg-terra-600 text-white rounded-lg hover:bg-terra-700 disabled:opacity-50 text-sm"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Alerts Banner */}
        {alerts.length > 0 && (
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl p-4 border border-amber-200 dark:border-amber-800">
            <div className="flex items-center gap-2 mb-3">
              <Bell className="w-5 h-5 text-amber-600" />
              <span className="font-semibold text-amber-900 dark:text-amber-100">Latest Market Alerts</span>
            </div>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="flex items-start gap-3 p-2 bg-white/50 dark:bg-gray-800/50 rounded-lg">
                  <div className={`mt-0.5 w-2 h-2 rounded-full ${
                    alert.impact === 'high' ? 'bg-red-500' : alert.impact === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                  }`} />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-white text-sm">{alert.title}</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">{alert.summary}</div>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(alert.timestamp).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-2 bg-white dark:bg-gray-800 p-1 rounded-lg shadow-sm">
          {[
            { id: 'prices' as const, label: 'Electricity Prices', icon: Zap },
            { id: 'incentives' as const, label: 'Incentives', icon: DollarSign },
            { id: 'queues' as const, label: 'Interconnection', icon: Clock },
            { id: 'commodities' as const, label: 'Equipment Costs', icon: TrendingUp },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-terra-600 text-white'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content based on active tab */}
        {activeTab === 'prices' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Real-time LMP */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-white">Real-Time LMP ($/MWh)</h3>
                <p className="text-xs text-gray-500 mt-1">Locational marginal prices by ISO</p>
              </div>
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {prices.map((price) => (
                  <div key={price.iso} className="px-5 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{price.region}</div>
                      <div className="text-xs text-gray-500">{price.iso}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-lg text-gray-900 dark:text-white">
                        ${price.lmp.toFixed(2)}
                      </div>
                      <div className={`flex items-center justify-end gap-1 text-xs ${
                        price.change24h > 0 ? 'text-green-600' : price.change24h < 0 ? 'text-red-600' : 'text-gray-500'
                      }`}>
                        {price.change24h > 0 ? <TrendingUp className="w-3 h-3" /> : price.change24h < 0 ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                        {price.change24h > 0 ? '+' : ''}{price.change24h.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* PPA Rates */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-white">PPA Contract Rates</h3>
                <p className="text-xs text-gray-500 mt-1">Recent utility-scale contract benchmarks</p>
              </div>
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {ppaRates.map((ppa, i) => (
                  <div key={i} className="px-5 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <div className="flex items-center gap-3">
                      <div className={`p-1.5 rounded-lg ${
                        ppa.technology === 'solar' ? 'bg-yellow-100 dark:bg-yellow-900/30' :
                        ppa.technology === 'wind' ? 'bg-blue-100 dark:bg-blue-900/30' :
                        'bg-green-100 dark:bg-green-900/30'
                      }`}>
                        {ppa.technology === 'solar' ? <Sun className="w-4 h-4 text-yellow-600" /> :
                         ppa.technology === 'wind' ? <Wind className="w-4 h-4 text-blue-600" /> :
                         <Battery className="w-4 h-4 text-green-600" />}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">{ppa.region}</div>
                        <div className="text-xs text-gray-500 capitalize">{ppa.technology} • {ppa.termYears}yr</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900 dark:text-white">${ppa.rate}/MWh</div>
                      <div className={`flex items-center justify-end gap-1 text-xs ${
                        ppa.trend === 'up' ? 'text-red-600' : ppa.trend === 'down' ? 'text-green-600' : 'text-gray-500'
                      }`}>
                        {ppa.trend === 'up' ? <TrendingUp className="w-3 h-3" /> : ppa.trend === 'down' ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                        {ppa.trend}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'incentives' && (
          <div className="space-y-4">
            {incentives.map((incentive, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-lg ${
                      incentive.type === 'ITC' || incentive.type === 'PTC' ? 'bg-green-100 dark:bg-green-900/30' :
                      incentive.type === 'State' ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-purple-100 dark:bg-purple-900/30'
                    }`}>
                      <DollarSign className={`w-5 h-5 ${
                        incentive.type === 'ITC' || incentive.type === 'PTC' ? 'text-green-600' :
                        incentive.type === 'State' ? 'text-blue-600' : 'text-purple-600'
                      }`} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{incentive.name}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{incentive.details}</p>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {incentive.eligible.map((tech) => (
                          <span key={tech} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-600 dark:text-gray-300">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-xl text-green-600">{incentive.value}</div>
                    <div className="text-xs text-gray-500 mt-1">Expires: {incentive.expires}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'queues' && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">ISO</th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Total MW</th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Solar</th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Wind</th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Storage</th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Avg Wait</th>
                    <th className="px-5 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Withdrawal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {queues.map((queue) => (
                    <tr key={queue.iso} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-5 py-4 font-medium text-gray-900 dark:text-white">{queue.iso}</td>
                      <td className="px-5 py-4 text-right text-gray-900 dark:text-white">{(queue.totalMW / 1000).toFixed(0)}GW</td>
                      <td className="px-5 py-4 text-right text-yellow-600">{(queue.solarMW / 1000).toFixed(0)}GW</td>
                      <td className="px-5 py-4 text-right text-blue-600">{(queue.windMW / 1000).toFixed(0)}GW</td>
                      <td className="px-5 py-4 text-right text-green-600">{(queue.storageMW / 1000).toFixed(0)}GW</td>
                      <td className="px-5 py-4 text-right text-gray-900 dark:text-white">{queue.avgWaitMonths}mo</td>
                      <td className="px-5 py-4 text-right">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          queue.withdrawalRate > 0.65 ? 'bg-red-100 text-red-700' :
                          queue.withdrawalRate > 0.55 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                        }`}>
                          {(queue.withdrawalRate * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'commodities' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {commodities.map((commodity) => (
              <div key={commodity.name} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
                <div className="text-sm text-gray-500 dark:text-gray-400">{commodity.name}</div>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">
                    {commodity.price < 1 ? `$${commodity.price}` : `$${commodity.price.toLocaleString()}`}
                  </span>
                  <span className="text-sm text-gray-500">{commodity.unit}</span>
                </div>
                <div className="flex items-center gap-4 mt-2">
                  <span className={`flex items-center gap-1 text-xs ${
                    commodity.change24h < 0 ? 'text-green-600' : commodity.change24h > 0 ? 'text-red-600' : 'text-gray-500'
                  }`}>
                    {commodity.change24h < 0 ? <TrendingDown className="w-3 h-3" /> : commodity.change24h > 0 ? <TrendingUp className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                    24h: {commodity.change24h > 0 ? '+' : ''}{commodity.change24h}%
                  </span>
                  <span className={`flex items-center gap-1 text-xs ${
                    commodity.change7d < 0 ? 'text-green-600' : commodity.change7d > 0 ? 'text-red-600' : 'text-gray-500'
                  }`}>
                    7d: {commodity.change7d > 0 ? '+' : ''}{commodity.change7d}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
