// Real-time market data simulation with realistic values
// In production, these would connect to actual APIs (EIA, NREL, ISO RTOs)

export interface ElectricityPrice {
  region: string;
  iso: string;
  lmp: number; // Locational Marginal Price $/MWh
  change24h: number;
  timestamp: string;
}

export interface PPARate {
  region: string;
  technology: 'solar' | 'wind' | 'storage';
  rate: number; // $/MWh
  termYears: number;
  trend: 'up' | 'down' | 'stable';
}

export interface IncentiveProgram {
  name: string;
  type: 'ITC' | 'PTC' | 'State' | 'Utility';
  value: string;
  expires: string;
  eligible: string[];
  details: string;
}

export interface InterconnectionQueue {
  iso: string;
  totalMW: number;
  solarMW: number;
  windMW: number;
  storageMW: number;
  avgWaitMonths: number;
  withdrawalRate: number;
}

export interface CommodityPrice {
  name: string;
  price: number;
  unit: string;
  change24h: number;
  change7d: number;
}

// Simulated real-time electricity prices by ISO region
export function getElectricityPrices(): ElectricityPrice[] {
  const baseTime = new Date().toISOString();
  const randomVariation = () => (Math.random() - 0.5) * 10;

  return [
    { region: 'ERCOT (Texas)', iso: 'ERCOT', lmp: 32.50 + randomVariation(), change24h: 2.3, timestamp: baseTime },
    { region: 'CAISO (California)', iso: 'CAISO', lmp: 45.20 + randomVariation(), change24h: -1.8, timestamp: baseTime },
    { region: 'PJM (Mid-Atlantic)', iso: 'PJM', lmp: 38.75 + randomVariation(), change24h: 0.5, timestamp: baseTime },
    { region: 'MISO (Midwest)', iso: 'MISO', lmp: 28.30 + randomVariation(), change24h: 3.1, timestamp: baseTime },
    { region: 'SPP (Southwest)', iso: 'SPP', lmp: 25.80 + randomVariation(), change24h: -0.9, timestamp: baseTime },
    { region: 'NYISO (New York)', iso: 'NYISO', lmp: 42.60 + randomVariation(), change24h: 1.2, timestamp: baseTime },
    { region: 'ISO-NE (New England)', iso: 'ISONE', lmp: 48.90 + randomVariation(), change24h: -2.4, timestamp: baseTime },
  ];
}

// Current PPA rates by region and technology
export function getPPARates(): PPARate[] {
  return [
    { region: 'Texas', technology: 'solar', rate: 24.50, termYears: 15, trend: 'down' },
    { region: 'Texas', technology: 'wind', rate: 22.00, termYears: 15, trend: 'stable' },
    { region: 'California', technology: 'solar', rate: 35.00, termYears: 20, trend: 'up' },
    { region: 'California', technology: 'storage', rate: 45.00, termYears: 15, trend: 'up' },
    { region: 'Southeast', technology: 'solar', rate: 28.00, termYears: 20, trend: 'stable' },
    { region: 'Midwest', technology: 'wind', rate: 20.00, termYears: 15, trend: 'down' },
    { region: 'Northeast', technology: 'solar', rate: 38.00, termYears: 20, trend: 'up' },
    { region: 'Southwest', technology: 'solar', rate: 26.00, termYears: 15, trend: 'stable' },
  ];
}

// Federal and state incentives
export function getIncentivePrograms(): IncentiveProgram[] {
  return [
    {
      name: 'Investment Tax Credit (ITC)',
      type: 'ITC',
      value: '30%',
      expires: '2032 (steps down after)',
      eligible: ['Solar', 'Storage', 'Geothermal'],
      details: 'Base 30% credit, +10% domestic content, +10% energy community, +10-20% low-income'
    },
    {
      name: 'Production Tax Credit (PTC)',
      type: 'PTC',
      value: '$0.0275/kWh',
      expires: '2032 (inflation adjusted)',
      eligible: ['Wind', 'Solar', 'Geothermal', 'Hydro'],
      details: 'Per-kWh credit for 10 years, inflation adjusted annually'
    },
    {
      name: 'Texas Property Tax Exemption',
      type: 'State',
      value: '100%',
      expires: 'Ongoing',
      eligible: ['Solar', 'Wind', 'Storage'],
      details: 'Full property tax exemption for renewable energy equipment'
    },
    {
      name: 'California SGIP',
      type: 'State',
      value: '$150-850/kWh',
      expires: '2025',
      eligible: ['Storage'],
      details: 'Self-Generation Incentive Program for energy storage'
    },
    {
      name: 'New York VDER',
      type: 'State',
      value: 'Variable $/kWh',
      expires: 'Ongoing',
      eligible: ['Solar', 'Storage'],
      details: 'Value of Distributed Energy Resources tariff'
    },
    {
      name: 'North Carolina REPS',
      type: 'State',
      value: 'REC value',
      expires: '2025',
      eligible: ['Solar'],
      details: 'Renewable Energy Portfolio Standard compliance market'
    },
  ];
}

// Interconnection queue data by ISO
export function getInterconnectionQueues(): InterconnectionQueue[] {
  return [
    { iso: 'ERCOT', totalMW: 298000, solarMW: 156000, windMW: 89000, storageMW: 53000, avgWaitMonths: 48, withdrawalRate: 0.72 },
    { iso: 'CAISO', totalMW: 352000, solarMW: 198000, windMW: 42000, storageMW: 112000, avgWaitMonths: 60, withdrawalRate: 0.68 },
    { iso: 'PJM', totalMW: 265000, solarMW: 142000, windMW: 68000, storageMW: 55000, avgWaitMonths: 54, withdrawalRate: 0.65 },
    { iso: 'MISO', totalMW: 189000, solarMW: 78000, windMW: 92000, storageMW: 19000, avgWaitMonths: 42, withdrawalRate: 0.58 },
    { iso: 'SPP', totalMW: 124000, solarMW: 45000, windMW: 72000, storageMW: 7000, avgWaitMonths: 36, withdrawalRate: 0.55 },
    { iso: 'NYISO', totalMW: 98000, solarMW: 52000, windMW: 38000, storageMW: 8000, avgWaitMonths: 48, withdrawalRate: 0.62 },
    { iso: 'ISO-NE', totalMW: 45000, solarMW: 28000, windMW: 12000, storageMW: 5000, avgWaitMonths: 36, withdrawalRate: 0.52 },
  ];
}

// Equipment and commodity prices
export function getCommodityPrices(): CommodityPrice[] {
  return [
    { name: 'Solar Modules (Mono PERC)', price: 0.18, unit: '$/W', change24h: -0.5, change7d: -2.1 },
    { name: 'Solar Modules (TOPCon)', price: 0.21, unit: '$/W', change24h: -0.3, change7d: -1.8 },
    { name: 'Inverters (Utility Scale)', price: 0.04, unit: '$/W', change24h: 0.0, change7d: -0.5 },
    { name: 'Battery Cells (LFP)', price: 85, unit: '$/kWh', change24h: -0.2, change7d: -1.5 },
    { name: 'Battery Cells (NMC)', price: 115, unit: '$/kWh', change24h: 0.1, change7d: -0.8 },
    { name: 'Steel (Structural)', price: 850, unit: '$/ton', change24h: 1.2, change7d: 2.5 },
    { name: 'Copper', price: 8450, unit: '$/ton', change24h: 0.8, change7d: -0.3 },
    { name: 'Polysilicon', price: 7.50, unit: '$/kg', change24h: -1.0, change7d: -3.2 },
  ];
}

// Simulated news/alerts feed
export interface MarketAlert {
  id: string;
  type: 'policy' | 'market' | 'opportunity' | 'warning';
  title: string;
  summary: string;
  timestamp: string;
  region?: string;
  impact: 'high' | 'medium' | 'low';
}

export function getMarketAlerts(): MarketAlert[] {
  const now = new Date();
  return [
    {
      id: 'alert-1',
      type: 'policy',
      title: 'IRS Releases Final ITC Domestic Content Guidance',
      summary: 'Treasury clarifies requirements for 10% domestic content bonus. Steel/iron must be 100% US-melted and poured.',
      timestamp: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
      impact: 'high'
    },
    {
      id: 'alert-2',
      type: 'opportunity',
      title: 'Duke Energy RFP: 500MW Solar + Storage',
      summary: 'Duke Carolinas seeking 500MW solar paired with 250MW/4hr storage. Proposals due March 15.',
      timestamp: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(),
      region: 'North Carolina',
      impact: 'high'
    },
    {
      id: 'alert-3',
      type: 'market',
      title: 'ERCOT Prices Spike 40% on Heat Wave',
      summary: 'Real-time prices hit $125/MWh as temperatures exceed 100°F across Texas.',
      timestamp: new Date(now.getTime() - 8 * 60 * 60 * 1000).toISOString(),
      region: 'Texas',
      impact: 'medium'
    },
    {
      id: 'alert-4',
      type: 'warning',
      title: 'PJM Interconnection Reform Delays Projects',
      summary: 'New cluster study process may add 12-18 months to queue timelines for 2024 applicants.',
      timestamp: new Date(now.getTime() - 12 * 60 * 60 * 1000).toISOString(),
      region: 'PJM',
      impact: 'high'
    },
    {
      id: 'alert-5',
      type: 'opportunity',
      title: 'New Mexico Opens 50,000 Acres for Solar Leasing',
      summary: 'State Land Office announces competitive lease auction for renewable development on state trust lands.',
      timestamp: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString(),
      region: 'New Mexico',
      impact: 'medium'
    },
  ];
}
