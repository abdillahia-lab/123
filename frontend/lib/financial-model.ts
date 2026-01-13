// Advanced Financial Modeling Engine for Renewable Energy Projects
// Includes IRR, NPV, LCOE, and sensitivity analysis

export interface ProjectAssumptions {
  // Project parameters
  capacityMW: number;
  capacityFactorPct: number;
  projectLifeYears: number;
  degradationPctPerYear: number;

  // Capital costs
  capexPerWatt: number;
  interconnectionCost: number;
  landCostTotal: number;
  developmentCost: number;

  // Operating costs
  opexPerKwYear: number;
  opexEscalationPct: number;
  insurancePctOfCapex: number;
  propertyTaxPctOfCapex: number;
  landLeasePctOfRevenue: number;

  // Revenue
  ppaRatePerMwh: number;
  ppaEscalationPct: number;
  merchantYears: number;
  merchantPricePerMwh: number;

  // Financing
  debtPct: number;
  debtInterestRate: number;
  debtTermYears: number;
  targetEquityIRR: number;

  // Tax
  federalTaxRate: number;
  stateTaxRate: number;
  itcPct: number;
  ptcPerMwh: number;
  usePTC: boolean;
  depreciationYears: number;

  // Adders
  domesticContentBonus: boolean;
  energyCommunityBonus: boolean;
  lowIncomeBonus: boolean;
}

export interface FinancialResults {
  // Summary metrics
  projectIRR: number;
  equityIRR: number;
  npv: number;
  lcoe: number;
  paybackYears: number;
  debtServiceCoverageRatio: number;

  // Totals
  totalCapex: number;
  totalRevenue: number;
  totalOpex: number;
  totalDebtService: number;
  totalTaxBenefit: number;
  netCashFlow: number;

  // Annual cash flows
  annualCashFlows: AnnualCashFlow[];

  // Sensitivity
  sensitivityResults?: SensitivityResult[];
}

export interface AnnualCashFlow {
  year: number;
  generation: number;
  revenue: number;
  opex: number;
  ebitda: number;
  debtService: number;
  taxBenefit: number;
  netCashFlow: number;
  cumulativeCashFlow: number;
}

export interface SensitivityResult {
  variable: string;
  baseCase: number;
  lowCase: number;
  highCase: number;
  irrLow: number;
  irrBase: number;
  irrHigh: number;
}

// Default assumptions for utility-scale solar
export function getDefaultSolarAssumptions(capacityMW: number = 100): ProjectAssumptions {
  return {
    capacityMW,
    capacityFactorPct: 26,
    projectLifeYears: 35,
    degradationPctPerYear: 0.5,

    capexPerWatt: 0.95,
    interconnectionCost: capacityMW * 50000,
    landCostTotal: capacityMW * 5 * 3000, // 5 acres/MW at $3000/acre
    developmentCost: capacityMW * 25000,

    opexPerKwYear: 8.50,
    opexEscalationPct: 2.0,
    insurancePctOfCapex: 0.25,
    propertyTaxPctOfCapex: 0,
    landLeasePctOfRevenue: 0,

    ppaRatePerMwh: 28,
    ppaEscalationPct: 1.5,
    merchantYears: 15,
    merchantPricePerMwh: 35,

    debtPct: 70,
    debtInterestRate: 6.5,
    debtTermYears: 18,
    targetEquityIRR: 12,

    federalTaxRate: 21,
    stateTaxRate: 5,
    itcPct: 30,
    ptcPerMwh: 27.5,
    usePTC: false,
    depreciationYears: 5,

    domesticContentBonus: false,
    energyCommunityBonus: false,
    lowIncomeBonus: false,
  };
}

// Default assumptions for utility-scale wind
export function getDefaultWindAssumptions(capacityMW: number = 200): ProjectAssumptions {
  return {
    capacityMW,
    capacityFactorPct: 38,
    projectLifeYears: 30,
    degradationPctPerYear: 0.3,

    capexPerWatt: 1.35,
    interconnectionCost: capacityMW * 60000,
    landCostTotal: capacityMW * 50 * 500, // 50 acres/MW at $500/acre (lease equivalent)
    developmentCost: capacityMW * 35000,

    opexPerKwYear: 12.00,
    opexEscalationPct: 2.0,
    insurancePctOfCapex: 0.30,
    propertyTaxPctOfCapex: 0,
    landLeasePctOfRevenue: 3,

    ppaRatePerMwh: 22,
    ppaEscalationPct: 1.0,
    merchantYears: 10,
    merchantPricePerMwh: 30,

    debtPct: 65,
    debtInterestRate: 6.0,
    debtTermYears: 15,
    targetEquityIRR: 10,

    federalTaxRate: 21,
    stateTaxRate: 5,
    itcPct: 30,
    ptcPerMwh: 27.5,
    usePTC: true, // Wind typically uses PTC
    depreciationYears: 5,

    domesticContentBonus: true,
    energyCommunityBonus: false,
    lowIncomeBonus: false,
  };
}

// Main financial model calculation
export function calculateFinancials(assumptions: ProjectAssumptions): FinancialResults {
  const a = assumptions;

  // Calculate total CAPEX
  const totalCapex =
    a.capacityMW * 1000000 * a.capexPerWatt +
    a.interconnectionCost +
    a.landCostTotal +
    a.developmentCost;

  // Calculate ITC with bonuses
  let effectiveITC = a.itcPct;
  if (a.domesticContentBonus) effectiveITC += 10;
  if (a.energyCommunityBonus) effectiveITC += 10;
  if (a.lowIncomeBonus) effectiveITC += 10;
  effectiveITC = Math.min(effectiveITC, 70); // Cap at 70%

  // Debt/Equity split
  const debtAmount = totalCapex * (a.debtPct / 100);
  const equityAmount = totalCapex - debtAmount;

  // Annual debt service (constant payment)
  const monthlyRate = a.debtInterestRate / 100 / 12;
  const numPayments = a.debtTermYears * 12;
  const monthlyPayment = debtAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / (Math.pow(1 + monthlyRate, numPayments) - 1);
  const annualDebtService = monthlyPayment * 12;

  // Generate annual cash flows
  const annualCashFlows: AnnualCashFlow[] = [];
  let cumulativeCashFlow = -equityAmount;
  let totalRevenue = 0;
  let totalOpex = 0;
  let totalDebtServiceSum = 0;
  let totalTaxBenefit = 0;
  let paybackYears = 0;
  let paybackFound = false;

  // MACRS 5-year depreciation schedule
  const macrsSchedule = [0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576];

  for (let year = 1; year <= a.projectLifeYears; year++) {
    // Generation with degradation
    const degradationFactor = Math.pow(1 - a.degradationPctPerYear / 100, year - 1);
    const generation = a.capacityMW * 1000 * 8760 * (a.capacityFactorPct / 100) * degradationFactor;

    // Revenue
    let revenue: number;
    const ppaYears = a.projectLifeYears - a.merchantYears;
    if (year <= ppaYears) {
      const escalatedPPA = a.ppaRatePerMwh * Math.pow(1 + a.ppaEscalationPct / 100, year - 1);
      revenue = generation * escalatedPPA / 1000;
    } else {
      revenue = generation * a.merchantPricePerMwh / 1000;
    }

    // PTC revenue (first 10 years)
    let ptcRevenue = 0;
    if (a.usePTC && year <= 10) {
      ptcRevenue = generation * a.ptcPerMwh / 1000;
    }

    // Operating expenses
    const baseOpex = a.capacityMW * 1000 * a.opexPerKwYear;
    const escalatedOpex = baseOpex * Math.pow(1 + a.opexEscalationPct / 100, year - 1);
    const insurance = totalCapex * (a.insurancePctOfCapex / 100);
    const propertyTax = totalCapex * (a.propertyTaxPctOfCapex / 100);
    const landLease = revenue * (a.landLeasePctOfRevenue / 100);
    const opex = escalatedOpex + insurance + propertyTax + landLease;

    // EBITDA
    const ebitda = revenue - opex;

    // Debt service (only during debt term)
    const debtService = year <= a.debtTermYears ? annualDebtService : 0;

    // Tax benefits
    let taxBenefit = 0;

    // ITC in year 1 (if not using PTC)
    if (year === 1 && !a.usePTC) {
      taxBenefit += totalCapex * (effectiveITC / 100);
    }

    // Depreciation tax shield
    if (year <= a.depreciationYears) {
      const depreciation = totalCapex * macrsSchedule[year - 1];
      const combinedTaxRate = (a.federalTaxRate + a.stateTaxRate) / 100;
      taxBenefit += depreciation * combinedTaxRate;
    }

    // PTC benefit
    if (a.usePTC && year <= 10) {
      taxBenefit += ptcRevenue;
    }

    // Net cash flow
    const netCashFlow = ebitda - debtService + taxBenefit;
    cumulativeCashFlow += netCashFlow;

    // Track payback
    if (!paybackFound && cumulativeCashFlow >= 0) {
      paybackYears = year;
      paybackFound = true;
    }

    // Accumulate totals
    totalRevenue += revenue;
    totalOpex += opex;
    totalDebtServiceSum += debtService;
    totalTaxBenefit += taxBenefit;

    annualCashFlows.push({
      year,
      generation,
      revenue,
      opex,
      ebitda,
      debtService,
      taxBenefit,
      netCashFlow,
      cumulativeCashFlow,
    });
  }

  // Calculate IRR
  const cashFlowsForIRR = [-equityAmount, ...annualCashFlows.map(cf => cf.netCashFlow)];
  const equityIRR = calculateIRR(cashFlowsForIRR) * 100;

  // Project-level IRR (unlevered)
  const unleveredCashFlows = [-totalCapex];
  for (const cf of annualCashFlows) {
    unleveredCashFlows.push(cf.ebitda + cf.taxBenefit);
  }
  const projectIRR = calculateIRR(unleveredCashFlows) * 100;

  // NPV at target equity IRR
  const discountRate = a.targetEquityIRR / 100;
  let npv = -equityAmount;
  for (let i = 0; i < annualCashFlows.length; i++) {
    npv += annualCashFlows[i].netCashFlow / Math.pow(1 + discountRate, i + 1);
  }

  // LCOE calculation
  let totalDiscountedGeneration = 0;
  let totalDiscountedCosts = totalCapex;
  const waccRate = 0.07; // Weighted average cost of capital

  for (let i = 0; i < annualCashFlows.length; i++) {
    const discountFactor = Math.pow(1 + waccRate, i + 1);
    totalDiscountedGeneration += annualCashFlows[i].generation / discountFactor;
    totalDiscountedCosts += annualCashFlows[i].opex / discountFactor;
  }
  const lcoe = (totalDiscountedCosts / totalDiscountedGeneration) * 1000; // $/MWh

  // DSCR (average over debt term)
  let dscr = 0;
  if (a.debtTermYears > 0) {
    const debtYearCashFlows = annualCashFlows.slice(0, a.debtTermYears);
    const avgEBITDA = debtYearCashFlows.reduce((sum, cf) => sum + cf.ebitda, 0) / a.debtTermYears;
    dscr = avgEBITDA / annualDebtService;
  }

  const netCashFlow = annualCashFlows.reduce((sum, cf) => sum + cf.netCashFlow, 0);

  return {
    projectIRR: Math.round(projectIRR * 100) / 100,
    equityIRR: Math.round(equityIRR * 100) / 100,
    npv: Math.round(npv),
    lcoe: Math.round(lcoe * 100) / 100,
    paybackYears: paybackFound ? paybackYears : a.projectLifeYears,
    debtServiceCoverageRatio: Math.round(dscr * 100) / 100,
    totalCapex: Math.round(totalCapex),
    totalRevenue: Math.round(totalRevenue),
    totalOpex: Math.round(totalOpex),
    totalDebtService: Math.round(totalDebtServiceSum),
    totalTaxBenefit: Math.round(totalTaxBenefit),
    netCashFlow: Math.round(netCashFlow),
    annualCashFlows,
  };
}

// IRR calculation using Newton-Raphson method
function calculateIRR(cashFlows: number[], guess: number = 0.1): number {
  const maxIterations = 100;
  const tolerance = 0.0001;

  let rate = guess;

  for (let i = 0; i < maxIterations; i++) {
    let npv = 0;
    let derivative = 0;

    for (let j = 0; j < cashFlows.length; j++) {
      const discountFactor = Math.pow(1 + rate, j);
      npv += cashFlows[j] / discountFactor;
      if (j > 0) {
        derivative -= j * cashFlows[j] / Math.pow(1 + rate, j + 1);
      }
    }

    if (Math.abs(derivative) < 1e-10) break;

    const newRate = rate - npv / derivative;

    if (Math.abs(newRate - rate) < tolerance) {
      return newRate;
    }

    rate = newRate;

    // Bound the rate to prevent divergence
    if (rate < -0.99) rate = -0.99;
    if (rate > 10) rate = 10;
  }

  return rate;
}

// Sensitivity analysis
export function runSensitivityAnalysis(baseAssumptions: ProjectAssumptions): SensitivityResult[] {
  const results: SensitivityResult[] = [];
  const baseResults = calculateFinancials(baseAssumptions);

  const variables: Array<{
    name: string;
    key: keyof ProjectAssumptions;
    lowMult: number;
    highMult: number;
  }> = [
    { name: 'PPA Rate', key: 'ppaRatePerMwh', lowMult: 0.85, highMult: 1.15 },
    { name: 'CAPEX', key: 'capexPerWatt', lowMult: 0.90, highMult: 1.10 },
    { name: 'Capacity Factor', key: 'capacityFactorPct', lowMult: 0.90, highMult: 1.10 },
    { name: 'Interest Rate', key: 'debtInterestRate', lowMult: 0.80, highMult: 1.20 },
    { name: 'O&M Cost', key: 'opexPerKwYear', lowMult: 0.85, highMult: 1.15 },
  ];

  for (const v of variables) {
    const baseValue = baseAssumptions[v.key] as number;

    const lowAssumptions = { ...baseAssumptions, [v.key]: baseValue * v.lowMult };
    const highAssumptions = { ...baseAssumptions, [v.key]: baseValue * v.highMult };

    const lowResults = calculateFinancials(lowAssumptions);
    const highResults = calculateFinancials(highAssumptions);

    results.push({
      variable: v.name,
      baseCase: baseValue,
      lowCase: baseValue * v.lowMult,
      highCase: baseValue * v.highMult,
      irrLow: v.name === 'CAPEX' || v.name === 'Interest Rate' || v.name === 'O&M Cost'
        ? highResults.equityIRR
        : lowResults.equityIRR,
      irrBase: baseResults.equityIRR,
      irrHigh: v.name === 'CAPEX' || v.name === 'Interest Rate' || v.name === 'O&M Cost'
        ? lowResults.equityIRR
        : highResults.equityIRR,
    });
  }

  return results;
}

// Quick valuation for parcel screening
export function quickParcelValuation(parcel: {
  acreage: number;
  solar_ghi: number;
  nearest_substation_mi: number;
  estimated_land_cost_per_acre: number;
}): {
  estimatedCapacityMW: number;
  estimatedCapex: number;
  estimatedAnnualRevenue: number;
  estimatedIRR: number;
  investmentGrade: 'A' | 'B' | 'C' | 'D';
} {
  // Estimate capacity (5 acres per MW for solar)
  const estimatedCapacityMW = Math.floor(parcel.acreage / 5);

  if (estimatedCapacityMW < 1) {
    return {
      estimatedCapacityMW: 0,
      estimatedCapex: 0,
      estimatedAnnualRevenue: 0,
      estimatedIRR: 0,
      investmentGrade: 'D',
    };
  }

  // Capacity factor based on GHI (rough correlation)
  const capacityFactor = Math.min(35, Math.max(18, parcel.solar_ghi * 4.5));

  // Interconnection cost estimate based on distance
  const interconnectionCostPerMW = parcel.nearest_substation_mi <= 2
    ? 40000
    : parcel.nearest_substation_mi <= 5
    ? 65000
    : parcel.nearest_substation_mi <= 10
    ? 100000
    : 150000;

  // Simple CAPEX estimate
  const estimatedCapex =
    estimatedCapacityMW * 1000000 * 0.95 + // Equipment
    estimatedCapacityMW * interconnectionCostPerMW + // Interconnection
    parcel.acreage * parcel.estimated_land_cost_per_acre; // Land

  // Estimated annual generation and revenue
  const annualGeneration = estimatedCapacityMW * 1000 * 8760 * (capacityFactor / 100);
  const estimatedAnnualRevenue = annualGeneration * 28 / 1000; // $28/MWh PPA

  // Rough IRR estimate (simplified)
  const annualCashFlow = estimatedAnnualRevenue * 0.75; // After opex
  const itcBenefit = estimatedCapex * 0.30;
  const payback = (estimatedCapex - itcBenefit) / annualCashFlow;
  const estimatedIRR = payback <= 6 ? 15 : payback <= 8 ? 12 : payback <= 10 ? 9 : payback <= 12 ? 6 : 3;

  // Investment grade
  let investmentGrade: 'A' | 'B' | 'C' | 'D';
  if (estimatedIRR >= 12 && parcel.nearest_substation_mi <= 5) {
    investmentGrade = 'A';
  } else if (estimatedIRR >= 9) {
    investmentGrade = 'B';
  } else if (estimatedIRR >= 6) {
    investmentGrade = 'C';
  } else {
    investmentGrade = 'D';
  }

  return {
    estimatedCapacityMW,
    estimatedCapex: Math.round(estimatedCapex),
    estimatedAnnualRevenue: Math.round(estimatedAnnualRevenue),
    estimatedIRR,
    investmentGrade,
  };
}
