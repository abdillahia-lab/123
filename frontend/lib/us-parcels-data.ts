// Comprehensive US Parcel Data for All 50 States
// Realistic coordinates, acreage, and renewable energy potential

export interface USParcel {
  id: string;
  apn: string;
  state: string;
  state_code: string;
  county: string;
  municipality: string;
  address: string;
  acreage: number;
  latitude: number;
  longitude: number;
  zoning_type: string;
  land_use: string;
  solar_permission: 'By-right' | 'Conditional Use' | 'Special Exception' | 'Prohibited';
  owner_name: string;
  owner_type: 'Private' | 'Corporate' | 'Government' | 'Trust';
  // Solar metrics (kWh/m²/day)
  solar_ghi: number;
  solar_dni: number;
  // Wind metrics (m/s at 100m hub height)
  wind_speed: number;
  // Grid proximity
  nearest_substation_mi: number;
  transmission_voltage_kv: number;
  // Pre-calculated scores
  solar_score: number;
  wind_score: number;
  overall_score: number;
  viability: 'excellent' | 'good' | 'moderate' | 'challenging' | 'poor';
  // Capacity estimates
  solar_capacity_mw: number;
  wind_capacity_mw: number;
  // Financial estimates
  estimated_land_cost_per_acre: number;
  estimated_development_cost: number;
  // Timestamps
  created_at: string;
  updated_at: string;
}

// State metadata for solar/wind potential
const stateMetadata: Record<string, {
  solar_avg: number;
  wind_avg: number;
  land_cost_avg: number;
  counties: string[];
  coords: { lat: number; lng: number };
}> = {
  AL: { solar_avg: 4.8, wind_avg: 5.2, land_cost_avg: 3500, coords: { lat: 32.806671, lng: -86.791130 }, counties: ['Madison', 'Jefferson', 'Mobile', 'Montgomery', 'Tuscaloosa', 'Baldwin', 'Lee', 'Morgan', 'Calhoun', 'Etowah'] },
  AK: { solar_avg: 2.8, wind_avg: 7.5, land_cost_avg: 1500, coords: { lat: 61.370716, lng: -152.404419 }, counties: ['Anchorage', 'Fairbanks North Star', 'Matanuska-Susitna', 'Kenai Peninsula', 'Juneau'] },
  AZ: { solar_avg: 6.5, wind_avg: 5.8, land_cost_avg: 4000, coords: { lat: 33.729759, lng: -111.431221 }, counties: ['Maricopa', 'Pima', 'Pinal', 'Yavapai', 'Mohave', 'Yuma', 'Cochise', 'Coconino', 'Navajo', 'Apache'] },
  AR: { solar_avg: 4.6, wind_avg: 5.5, land_cost_avg: 2800, coords: { lat: 34.969704, lng: -92.373123 }, counties: ['Pulaski', 'Benton', 'Washington', 'Sebastian', 'Faulkner', 'Saline', 'Craighead', 'Garland', 'Jefferson', 'White'] },
  CA: { solar_avg: 5.8, wind_avg: 6.2, land_cost_avg: 12000, coords: { lat: 36.116203, lng: -119.681564 }, counties: ['Los Angeles', 'San Diego', 'Orange', 'Riverside', 'San Bernardino', 'Santa Clara', 'Alameda', 'Sacramento', 'Fresno', 'Kern', 'Imperial', 'San Joaquin', 'Tulare', 'Kings'] },
  CO: { solar_avg: 5.5, wind_avg: 7.2, land_cost_avg: 5500, coords: { lat: 39.059811, lng: -105.311104 }, counties: ['Denver', 'El Paso', 'Arapahoe', 'Jefferson', 'Adams', 'Larimer', 'Douglas', 'Boulder', 'Weld', 'Pueblo', 'Mesa', 'Garfield'] },
  CT: { solar_avg: 4.2, wind_avg: 5.0, land_cost_avg: 18000, coords: { lat: 41.597782, lng: -72.755371 }, counties: ['Fairfield', 'Hartford', 'New Haven', 'New London', 'Litchfield', 'Middlesex', 'Tolland', 'Windham'] },
  DE: { solar_avg: 4.5, wind_avg: 5.5, land_cost_avg: 12000, coords: { lat: 39.318523, lng: -75.507141 }, counties: ['New Castle', 'Kent', 'Sussex'] },
  FL: { solar_avg: 5.4, wind_avg: 4.8, land_cost_avg: 8000, coords: { lat: 27.766279, lng: -81.686783 }, counties: ['Miami-Dade', 'Broward', 'Palm Beach', 'Hillsborough', 'Orange', 'Pinellas', 'Duval', 'Lee', 'Polk', 'Brevard', 'Volusia', 'Pasco', 'Seminole', 'Sarasota'] },
  GA: { solar_avg: 5.0, wind_avg: 4.5, land_cost_avg: 4500, coords: { lat: 33.040619, lng: -83.643074 }, counties: ['Fulton', 'Gwinnett', 'Cobb', 'DeKalb', 'Clayton', 'Cherokee', 'Forsyth', 'Henry', 'Richmond', 'Chatham', 'Houston', 'Columbia'] },
  HI: { solar_avg: 5.2, wind_avg: 7.0, land_cost_avg: 25000, coords: { lat: 21.094318, lng: -157.498337 }, counties: ['Honolulu', 'Hawaii', 'Maui', 'Kauai'] },
  ID: { solar_avg: 4.8, wind_avg: 6.5, land_cost_avg: 3000, coords: { lat: 44.240459, lng: -114.478828 }, counties: ['Ada', 'Canyon', 'Kootenai', 'Bonneville', 'Twin Falls', 'Bannock', 'Bingham', 'Elmore', 'Jerome', 'Power'] },
  IL: { solar_avg: 4.2, wind_avg: 7.0, land_cost_avg: 8500, coords: { lat: 40.349457, lng: -88.986137 }, counties: ['Cook', 'DuPage', 'Lake', 'Will', 'Kane', 'McHenry', 'Winnebago', 'Madison', 'St. Clair', 'Champaign', 'Sangamon', 'Peoria', 'McLean', 'DeKalb', 'LaSalle'] },
  IN: { solar_avg: 4.1, wind_avg: 6.5, land_cost_avg: 7000, coords: { lat: 39.849426, lng: -86.258278 }, counties: ['Marion', 'Lake', 'Allen', 'Hamilton', 'St. Joseph', 'Elkhart', 'Tippecanoe', 'Vanderburgh', 'Porter', 'Hendricks', 'Johnson', 'Monroe', 'Madison', 'Delaware', 'Vigo'] },
  IA: { solar_avg: 4.3, wind_avg: 8.0, land_cost_avg: 9000, coords: { lat: 42.011539, lng: -93.210526 }, counties: ['Polk', 'Linn', 'Scott', 'Johnson', 'Black Hawk', 'Woodbury', 'Dubuque', 'Story', 'Pottawattamie', 'Dallas', 'Warren', 'Cerro Gordo', 'Clinton', 'Marshall'] },
  KS: { solar_avg: 5.0, wind_avg: 8.5, land_cost_avg: 3500, coords: { lat: 38.526600, lng: -96.726486 }, counties: ['Johnson', 'Sedgwick', 'Shawnee', 'Wyandotte', 'Douglas', 'Leavenworth', 'Riley', 'Butler', 'Reno', 'Saline', 'Ford', 'Finney', 'Gray', 'Clark'] },
  KY: { solar_avg: 4.3, wind_avg: 5.0, land_cost_avg: 4000, coords: { lat: 37.668140, lng: -84.670067 }, counties: ['Jefferson', 'Fayette', 'Kenton', 'Boone', 'Warren', 'Hardin', 'Daviess', 'Campbell', 'Madison', 'Bullitt', 'Oldham', 'McCracken'] },
  LA: { solar_avg: 4.9, wind_avg: 5.8, land_cost_avg: 3200, coords: { lat: 31.169546, lng: -91.867805 }, counties: ['Orleans', 'Jefferson', 'East Baton Rouge', 'St. Tammany', 'Caddo', 'Calcasieu', 'Lafayette', 'Ouachita', 'Livingston', 'Tangipahoa', 'Rapides', 'Bossier'] },
  ME: { solar_avg: 3.8, wind_avg: 6.5, land_cost_avg: 3500, coords: { lat: 45.253783, lng: -69.445469 }, counties: ['Cumberland', 'York', 'Penobscot', 'Kennebec', 'Androscoggin', 'Aroostook', 'Oxford', 'Somerset', 'Hancock', 'Sagadahoc'] },
  MD: { solar_avg: 4.5, wind_avg: 5.2, land_cost_avg: 15000, coords: { lat: 39.045755, lng: -76.641271 }, counties: ['Montgomery', 'Prince Georges', 'Baltimore', 'Anne Arundel', 'Howard', 'Harford', 'Frederick', 'Charles', 'Carroll', 'Washington', 'Calvert', 'St. Marys', 'Cecil', 'Wicomico'] },
  MA: { solar_avg: 4.0, wind_avg: 5.8, land_cost_avg: 22000, coords: { lat: 42.230171, lng: -71.530106 }, counties: ['Middlesex', 'Worcester', 'Essex', 'Suffolk', 'Norfolk', 'Bristol', 'Plymouth', 'Hampden', 'Barnstable', 'Hampshire', 'Berkshire', 'Franklin'] },
  MI: { solar_avg: 3.9, wind_avg: 6.8, land_cost_avg: 5500, coords: { lat: 43.326618, lng: -84.536095 }, counties: ['Wayne', 'Oakland', 'Macomb', 'Kent', 'Genesee', 'Washtenaw', 'Ingham', 'Ottawa', 'Kalamazoo', 'Saginaw', 'Muskegon', 'St. Clair', 'Berrien', 'Jackson', 'Livingston'] },
  MN: { solar_avg: 4.0, wind_avg: 7.5, land_cost_avg: 6500, coords: { lat: 45.694454, lng: -93.900192 }, counties: ['Hennepin', 'Ramsey', 'Dakota', 'Anoka', 'Washington', 'Scott', 'St. Louis', 'Olmsted', 'Stearns', 'Wright', 'Carver', 'Blue Earth', 'Rice', 'Freeborn', 'Murray', 'Lincoln'] },
  MS: { solar_avg: 4.8, wind_avg: 5.0, land_cost_avg: 2500, coords: { lat: 32.741646, lng: -89.678696 }, counties: ['Hinds', 'Harrison', 'DeSoto', 'Rankin', 'Jackson', 'Madison', 'Lee', 'Forrest', 'Lauderdale', 'Lowndes', 'Jones', 'Warren'] },
  MO: { solar_avg: 4.5, wind_avg: 6.8, land_cost_avg: 4500, coords: { lat: 38.456085, lng: -92.288368 }, counties: ['St. Louis', 'Jackson', 'St. Charles', 'Greene', 'Clay', 'Jefferson', 'Boone', 'Jasper', 'Franklin', 'Cass', 'Platte', 'Christian', 'Buchanan', 'Cole', 'Cape Girardeau'] },
  MT: { solar_avg: 4.5, wind_avg: 7.8, land_cost_avg: 2000, coords: { lat: 46.921925, lng: -110.454353 }, counties: ['Yellowstone', 'Missoula', 'Gallatin', 'Flathead', 'Cascade', 'Lewis and Clark', 'Ravalli', 'Silver Bow', 'Lake', 'Lincoln', 'Hill', 'Chouteau', 'Teton'] },
  NE: { solar_avg: 4.8, wind_avg: 8.2, land_cost_avg: 4000, coords: { lat: 41.125370, lng: -98.268082 }, counties: ['Douglas', 'Lancaster', 'Sarpy', 'Hall', 'Buffalo', 'Scotts Bluff', 'Lincoln', 'Madison', 'Dodge', 'Platte', 'Adams', 'Dawson', 'Gage', 'Custer', 'Keith'] },
  NV: { solar_avg: 6.2, wind_avg: 6.0, land_cost_avg: 3500, coords: { lat: 38.313515, lng: -117.055374 }, counties: ['Clark', 'Washoe', 'Carson City', 'Douglas', 'Elko', 'Lyon', 'Nye', 'Churchill', 'Humboldt', 'White Pine', 'Pershing', 'Lander', 'Lincoln'] },
  NH: { solar_avg: 3.9, wind_avg: 5.5, land_cost_avg: 8000, coords: { lat: 43.452492, lng: -71.563896 }, counties: ['Hillsborough', 'Rockingham', 'Merrimack', 'Strafford', 'Grafton', 'Cheshire', 'Belknap', 'Carroll', 'Sullivan', 'Coos'] },
  NJ: { solar_avg: 4.3, wind_avg: 5.2, land_cost_avg: 25000, coords: { lat: 40.298904, lng: -74.521011 }, counties: ['Bergen', 'Middlesex', 'Essex', 'Hudson', 'Monmouth', 'Ocean', 'Union', 'Passaic', 'Camden', 'Morris', 'Burlington', 'Mercer', 'Somerset', 'Gloucester', 'Atlantic', 'Cumberland', 'Salem'] },
  NM: { solar_avg: 6.3, wind_avg: 7.0, land_cost_avg: 2500, coords: { lat: 34.840515, lng: -106.248482 }, counties: ['Bernalillo', 'Dona Ana', 'Santa Fe', 'Sandoval', 'San Juan', 'Valencia', 'McKinley', 'Lea', 'Chaves', 'Eddy', 'Otero', 'Curry', 'Roosevelt', 'Quay', 'Guadalupe', 'Torrance'] },
  NY: { solar_avg: 3.8, wind_avg: 5.8, land_cost_avg: 12000, coords: { lat: 42.165726, lng: -74.948051 }, counties: ['Kings', 'Queens', 'New York', 'Suffolk', 'Bronx', 'Nassau', 'Westchester', 'Erie', 'Monroe', 'Richmond', 'Onondaga', 'Orange', 'Albany', 'Dutchess', 'Saratoga', 'Oneida', 'Niagara', 'St. Lawrence', 'Jefferson', 'Clinton'] },
  NC: { solar_avg: 4.9, wind_avg: 5.0, land_cost_avg: 6000, coords: { lat: 35.630066, lng: -79.806419 }, counties: ['Mecklenburg', 'Wake', 'Guilford', 'Forsyth', 'Cumberland', 'Durham', 'Buncombe', 'Gaston', 'New Hanover', 'Union', 'Cabarrus', 'Iredell', 'Johnston', 'Pitt', 'Davidson', 'Rowan', 'Randolph', 'Alamance', 'Robeson', 'Wayne'] },
  ND: { solar_avg: 4.2, wind_avg: 8.5, land_cost_avg: 2500, coords: { lat: 47.528912, lng: -99.784012 }, counties: ['Cass', 'Burleigh', 'Grand Forks', 'Ward', 'Williams', 'Stark', 'Morton', 'Stutsman', 'Richland', 'Ramsey', 'McKenzie', 'Mountrail', 'McHenry', 'McLean'] },
  OH: { solar_avg: 4.0, wind_avg: 6.2, land_cost_avg: 7500, coords: { lat: 40.388783, lng: -82.764915 }, counties: ['Cuyahoga', 'Franklin', 'Hamilton', 'Summit', 'Montgomery', 'Lucas', 'Butler', 'Stark', 'Lorain', 'Mahoning', 'Lake', 'Trumbull', 'Medina', 'Warren', 'Clermont', 'Delaware', 'Fairfield', 'Licking', 'Wood', 'Portage'] },
  OK: { solar_avg: 5.2, wind_avg: 8.0, land_cost_avg: 3000, coords: { lat: 35.565342, lng: -96.928917 }, counties: ['Oklahoma', 'Tulsa', 'Cleveland', 'Canadian', 'Comanche', 'Rogers', 'Payne', 'Wagoner', 'Garfield', 'Grady', 'Kay', 'Texas', 'Cimarron', 'Beaver', 'Harper', 'Woods', 'Alfalfa', 'Grant', 'Major', 'Dewey'] },
  OR: { solar_avg: 4.2, wind_avg: 6.8, land_cost_avg: 5000, coords: { lat: 43.804133, lng: -120.554201 }, counties: ['Multnomah', 'Washington', 'Clackamas', 'Lane', 'Marion', 'Jackson', 'Deschutes', 'Linn', 'Douglas', 'Yamhill', 'Benton', 'Umatilla', 'Morrow', 'Gilliam', 'Sherman', 'Wasco'] },
  PA: { solar_avg: 4.0, wind_avg: 5.8, land_cost_avg: 8000, coords: { lat: 40.590752, lng: -77.209755 }, counties: ['Philadelphia', 'Allegheny', 'Montgomery', 'Bucks', 'Delaware', 'Lancaster', 'Chester', 'York', 'Berks', 'Lehigh', 'Luzerne', 'Northampton', 'Dauphin', 'Erie', 'Westmoreland', 'Cumberland', 'Lackawanna', 'Washington', 'Butler', 'Cambria', 'Centre', 'Clearfield', 'Somerset'] },
  RI: { solar_avg: 4.1, wind_avg: 5.5, land_cost_avg: 20000, coords: { lat: 41.680893, lng: -71.511780 }, counties: ['Providence', 'Kent', 'Washington', 'Newport', 'Bristol'] },
  SC: { solar_avg: 5.0, wind_avg: 4.8, land_cost_avg: 4500, coords: { lat: 33.856892, lng: -80.945007 }, counties: ['Greenville', 'Richland', 'Charleston', 'Horry', 'Spartanburg', 'Lexington', 'York', 'Berkeley', 'Anderson', 'Beaufort', 'Dorchester', 'Aiken', 'Florence', 'Orangeburg', 'Sumter'] },
  SD: { solar_avg: 4.5, wind_avg: 8.0, land_cost_avg: 2800, coords: { lat: 44.299782, lng: -99.438828 }, counties: ['Minnehaha', 'Pennington', 'Lincoln', 'Brown', 'Brookings', 'Codington', 'Meade', 'Lawrence', 'Davison', 'Yankton', 'Hughes', 'Beadle', 'Clay', 'Union', 'Grant', 'Roberts', 'Day', 'Marshall', 'Spink', 'Faulk', 'Hand'] },
  TN: { solar_avg: 4.6, wind_avg: 5.0, land_cost_avg: 5000, coords: { lat: 35.747845, lng: -86.692345 }, counties: ['Shelby', 'Davidson', 'Knox', 'Hamilton', 'Rutherford', 'Williamson', 'Sumner', 'Montgomery', 'Wilson', 'Blount', 'Washington', 'Maury', 'Sevier', 'Sullivan', 'Bradley', 'Madison'] },
  TX: { solar_avg: 5.5, wind_avg: 7.8, land_cost_avg: 4000, coords: { lat: 31.054487, lng: -97.563461 }, counties: ['Harris', 'Dallas', 'Tarrant', 'Bexar', 'Travis', 'Collin', 'Hidalgo', 'El Paso', 'Denton', 'Fort Bend', 'Williamson', 'Montgomery', 'Cameron', 'Nueces', 'Brazoria', 'Bell', 'Galveston', 'Lubbock', 'Webb', 'McLennan', 'Jefferson', 'Smith', 'Brazos', 'Hays', 'Midland', 'Ector', 'Taylor', 'Randall', 'Potter', 'Carson', 'Hutchinson', 'Moore', 'Sherman', 'Dallam', 'Hartley', 'Oldham', 'Deaf Smith', 'Parmer', 'Castro', 'Swisher', 'Briscoe', 'Floyd', 'Hale', 'Lamb', 'Bailey', 'Cochran', 'Hockley', 'Terry', 'Lynn', 'Garza', 'Crosby', 'Dickens', 'King', 'Stonewall', 'Kent', 'Scurry', 'Borden', 'Dawson', 'Gaines', 'Andrews', 'Martin', 'Howard', 'Mitchell', 'Nolan', 'Fisher', 'Jones', 'Shackelford', 'Callahan', 'Eastland', 'Brown', 'Coleman', 'Runnels', 'Coke', 'Sterling', 'Glasscock', 'Reagan', 'Irion', 'Tom Green', 'Concho', 'McCulloch', 'San Saba', 'Mason', 'Llano', 'Gillespie', 'Kerr', 'Kendall', 'Comal', 'Guadalupe', 'Gonzales', 'DeWitt', 'Lavaca', 'Jackson', 'Victoria', 'Calhoun', 'Refugio', 'San Patricio', 'Aransas', 'Bee', 'Live Oak', 'McMullen', 'La Salle', 'Dimmit', 'Zavala', 'Frio', 'Atascosa', 'Wilson', 'Karnes', 'Goliad', 'Kleberg', 'Kenedy', 'Brooks', 'Jim Wells', 'Duval', 'Jim Hogg', 'Zapata', 'Starr', 'Willacy'] },
  UT: { solar_avg: 5.5, wind_avg: 6.0, land_cost_avg: 3500, coords: { lat: 39.320980, lng: -111.093731 }, counties: ['Salt Lake', 'Utah', 'Davis', 'Weber', 'Washington', 'Cache', 'Box Elder', 'Tooele', 'Iron', 'Summit', 'Uintah', 'Duchesne', 'Emery', 'Millard', 'Beaver', 'Juab'] },
  VT: { solar_avg: 3.7, wind_avg: 5.8, land_cost_avg: 6000, coords: { lat: 44.045876, lng: -72.710686 }, counties: ['Chittenden', 'Rutland', 'Washington', 'Windsor', 'Franklin', 'Addison', 'Bennington', 'Orange', 'Windham', 'Caledonia', 'Orleans', 'Lamoille', 'Grand Isle', 'Essex'] },
  VA: { solar_avg: 4.7, wind_avg: 5.3, land_cost_avg: 7500, coords: { lat: 37.769337, lng: -78.169968 }, counties: ['Fairfax', 'Prince William', 'Loudoun', 'Virginia Beach', 'Chesterfield', 'Henrico', 'Arlington', 'Stafford', 'Spotsylvania', 'Norfolk', 'Richmond', 'Chesapeake', 'Newport News', 'Hampton', 'Alexandria', 'Fauquier', 'Culpeper', 'Orange', 'Albemarle', 'Augusta', 'Rockingham', 'Frederick', 'Shenandoah', 'Warren', 'Clarke', 'Page', 'Rappahannock', 'Madison', 'Greene', 'Fluvanna', 'Louisa', 'Goochland', 'Hanover', 'Caroline', 'King George', 'Westmoreland', 'Northumberland', 'Lancaster', 'Richmond County', 'Essex', 'King William', 'King and Queen', 'Middlesex', 'Mathews', 'Gloucester', 'York', 'James City', 'New Kent', 'Charles City', 'Prince George', 'Dinwiddie', 'Sussex', 'Surry', 'Isle of Wight', 'Southampton', 'Suffolk', 'Franklin', 'Greensville', 'Brunswick', 'Mecklenburg', 'Lunenburg', 'Nottoway', 'Amelia', 'Powhatan', 'Cumberland', 'Buckingham', 'Appomattox', 'Prince Edward', 'Charlotte', 'Halifax', 'Pittsylvania', 'Campbell', 'Bedford', 'Amherst', 'Nelson', 'Rockbridge', 'Bath', 'Highland', 'Alleghany', 'Botetourt', 'Craig', 'Roanoke', 'Montgomery', 'Floyd', 'Pulaski', 'Giles', 'Bland', 'Wythe', 'Smyth', 'Washington', 'Russell', 'Tazewell', 'Buchanan', 'Dickenson', 'Wise', 'Lee', 'Scott'] },
  WA: { solar_avg: 3.8, wind_avg: 6.5, land_cost_avg: 6500, coords: { lat: 47.400902, lng: -121.490494 }, counties: ['King', 'Pierce', 'Snohomish', 'Spokane', 'Clark', 'Thurston', 'Kitsap', 'Yakima', 'Whatcom', 'Benton', 'Skagit', 'Cowlitz', 'Grant', 'Franklin', 'Lewis', 'Chelan', 'Douglas', 'Kittitas', 'Klickitat', 'Walla Walla', 'Adams', 'Lincoln', 'Whitman'] },
  WV: { solar_avg: 4.0, wind_avg: 5.5, land_cost_avg: 2500, coords: { lat: 38.491226, lng: -80.954453 }, counties: ['Kanawha', 'Berkeley', 'Cabell', 'Wood', 'Monongalia', 'Raleigh', 'Putnam', 'Harrison', 'Marion', 'Mercer', 'Jefferson', 'Ohio', 'Fayette', 'Wayne', 'Logan', 'Greenbrier', 'Preston', 'Tucker', 'Grant', 'Hardy', 'Pendleton', 'Pocahontas', 'Randolph'] },
  WI: { solar_avg: 3.9, wind_avg: 6.8, land_cost_avg: 5500, coords: { lat: 44.268543, lng: -89.616508 }, counties: ['Milwaukee', 'Dane', 'Waukesha', 'Brown', 'Racine', 'Outagamie', 'Winnebago', 'Kenosha', 'Rock', 'Marathon', 'Washington', 'La Crosse', 'Sheboygan', 'Walworth', 'Fond du Lac', 'Eau Claire', 'Jefferson', 'Ozaukee', 'St. Croix', 'Dodge', 'Portage', 'Wood', 'Columbia', 'Grant', 'Iowa', 'Lafayette', 'Green', 'Crawford', 'Vernon', 'Richland', 'Sauk', 'Juneau', 'Adams', 'Marquette', 'Waushara', 'Green Lake'] },
  WY: { solar_avg: 5.0, wind_avg: 8.5, land_cost_avg: 1800, coords: { lat: 42.755966, lng: -107.302490 }, counties: ['Laramie', 'Natrona', 'Campbell', 'Sweetwater', 'Fremont', 'Albany', 'Sheridan', 'Teton', 'Park', 'Uinta', 'Lincoln', 'Carbon', 'Converse', 'Goshen', 'Platte', 'Niobrara', 'Weston', 'Crook', 'Johnson', 'Washakie', 'Big Horn', 'Hot Springs', 'Sublette'] }
};

// Zoning types by land use
const zoningTypes = [
  'Agricultural',
  'Rural Agricultural',
  'Agricultural-Residential',
  'Commercial',
  'Industrial',
  'Light Industrial',
  'Mixed Use',
  'Planned Development',
  'Open Space',
  'Conservation'
];

const landUseTypes = [
  'Agricultural',
  'Vacant Land',
  'Pasture',
  'Cropland',
  'Rangeland',
  'Forest',
  'Industrial',
  'Commercial',
  'Mixed Agricultural'
];

const ownerTypes: Array<'Private' | 'Corporate' | 'Government' | 'Trust'> = ['Private', 'Corporate', 'Government', 'Trust'];
const permissionTypes: Array<'By-right' | 'Conditional Use' | 'Special Exception' | 'Prohibited'> = ['By-right', 'Conditional Use', 'Special Exception', 'Prohibited'];

// Deterministic random number generator for consistent data
function seededRandom(seed: number): () => number {
  return function() {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
}

// Generate parcels for a state
function generateParcelsForState(stateCode: string, count: number): USParcel[] {
  const meta = stateMetadata[stateCode];
  if (!meta) return [];

  const parcels: USParcel[] = [];
  const rng = seededRandom(stateCode.charCodeAt(0) * 1000 + stateCode.charCodeAt(1));

  for (let i = 0; i < count; i++) {
    const county = meta.counties[Math.floor(rng() * meta.counties.length)];
    const latOffset = (rng() - 0.5) * 4;
    const lngOffset = (rng() - 0.5) * 6;
    const lat = meta.coords.lat + latOffset;
    const lng = meta.coords.lng + lngOffset;

    const acreage = Math.round(50 + rng() * 950);
    const solarGhi = meta.solar_avg + (rng() - 0.5) * 1.5;
    const windSpeed = meta.wind_avg + (rng() - 0.5) * 2;
    const substationDist = 0.5 + rng() * 12;
    const transmissionVoltage = [69, 115, 138, 230, 345, 500][Math.floor(rng() * 6)];

    // Calculate scores
    const solarScore = Math.min(100, Math.round((solarGhi / 6.5) * 85 + rng() * 15));
    const windScore = Math.min(100, Math.round((windSpeed / 8.5) * 85 + rng() * 15));

    // Grid score based on distance and voltage
    let gridScore = 100 - (substationDist * 6);
    gridScore += transmissionVoltage >= 230 ? 15 : transmissionVoltage >= 138 ? 10 : 5;
    gridScore = Math.min(100, Math.max(0, Math.round(gridScore)));

    // Permission affects permitting score
    const permission = permissionTypes[Math.floor(rng() * permissionTypes.length)];
    let permittingScore = permission === 'By-right' ? 95 : permission === 'Conditional Use' ? 75 : permission === 'Special Exception' ? 55 : 20;
    permittingScore += Math.round((rng() - 0.5) * 10);

    // Land score
    const landScore = Math.round(70 + rng() * 30);

    // Environmental score
    const envScore = Math.round(60 + rng() * 40);

    // Overall score (weighted)
    const overallScore = Math.round(
      permittingScore * 0.25 +
      gridScore * 0.30 +
      envScore * 0.20 +
      landScore * 0.15 +
      Math.max(solarScore, windScore) * 0.10
    );

    let viability: USParcel['viability'];
    if (overallScore >= 85) viability = 'excellent';
    else if (overallScore >= 70) viability = 'good';
    else if (overallScore >= 55) viability = 'moderate';
    else if (overallScore >= 40) viability = 'challenging';
    else viability = 'poor';

    // Capacity estimates (5 acres per MW for solar, 50 acres per MW for wind)
    const solarCapacity = Math.round(acreage / 5);
    const windCapacity = Math.round(acreage / 50);

    // Cost estimates
    const landCostPerAcre = Math.round(meta.land_cost_avg * (0.7 + rng() * 0.6));
    const developmentCost = Math.round(solarCapacity * 1000000 * (0.8 + rng() * 0.4));

    const stateNames: Record<string, string> = {
      AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California',
      CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia',
      HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa',
      KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
      MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri',
      MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey',
      NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio',
      OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina',
      SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont',
      VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming'
    };

    parcels.push({
      id: `${stateCode.toLowerCase()}-${String(i + 1).padStart(4, '0')}`,
      apn: `${stateCode}-${county.substring(0, 4).toUpperCase()}-${String(Math.floor(rng() * 900000) + 100000)}`,
      state: stateNames[stateCode] || stateCode,
      state_code: stateCode,
      county,
      municipality: county,
      address: `${Math.floor(rng() * 99000) + 1000} ${['Solar', 'Wind', 'Energy', 'Green', 'Renewable', 'Power', 'Farm', 'Prairie', 'Valley', 'Ridge'][Math.floor(rng() * 10)]} ${['Road', 'Highway', 'Lane', 'Drive', 'Way', 'Boulevard', 'Avenue', 'Route'][Math.floor(rng() * 8)]}`,
      acreage,
      latitude: Math.round(lat * 10000) / 10000,
      longitude: Math.round(lng * 10000) / 10000,
      zoning_type: zoningTypes[Math.floor(rng() * zoningTypes.length)],
      land_use: landUseTypes[Math.floor(rng() * landUseTypes.length)],
      solar_permission: permission,
      owner_name: `${['Blue Ridge', 'Golden Valley', 'Prairie Wind', 'Mountain View', 'River Valley', 'Sunny Acres', 'Green Meadows', 'Oak Grove', 'Pine Ridge', 'Cedar Creek'][Math.floor(rng() * 10)]} ${['Farms', 'Holdings', 'Land LLC', 'Properties', 'Investments', 'Trust', 'Partners', 'Estates', 'Development', 'Energy'][Math.floor(rng() * 10)]}`,
      owner_type: ownerTypes[Math.floor(rng() * ownerTypes.length)],
      solar_ghi: Math.round(solarGhi * 100) / 100,
      solar_dni: Math.round((solarGhi * 0.85 + rng() * 0.5) * 100) / 100,
      wind_speed: Math.round(windSpeed * 10) / 10,
      nearest_substation_mi: Math.round(substationDist * 10) / 10,
      transmission_voltage_kv: transmissionVoltage,
      solar_score: solarScore,
      wind_score: windScore,
      overall_score: overallScore,
      viability,
      solar_capacity_mw: solarCapacity,
      wind_capacity_mw: windCapacity,
      estimated_land_cost_per_acre: landCostPerAcre,
      estimated_development_cost: developmentCost,
      created_at: new Date(Date.now() - Math.floor(rng() * 90 * 24 * 60 * 60 * 1000)).toISOString(),
      updated_at: new Date().toISOString()
    });
  }

  return parcels;
}

// Define parcel counts per state (more for high-potential states)
const parcelCountsByState: Record<string, number> = {
  TX: 150, CA: 120, AZ: 100, NM: 90, NV: 80, CO: 80, FL: 80, NC: 70,
  VA: 60, GA: 60, OK: 60, KS: 60, IA: 60, MN: 55, NE: 55, SD: 50,
  ND: 50, WY: 50, MT: 50, OR: 50, WA: 50, ID: 45, UT: 45, IL: 45,
  IN: 40, OH: 40, MI: 40, WI: 40, MO: 40, AR: 35, LA: 35, MS: 35,
  AL: 35, SC: 35, TN: 35, KY: 30, WV: 30, PA: 30, NY: 30, ME: 25,
  NH: 20, VT: 20, MA: 20, CT: 15, RI: 10, NJ: 20, DE: 10, MD: 25,
  HI: 15, AK: 10
};

// Generate all US parcels
export function generateAllUSParcels(): USParcel[] {
  const allParcels: USParcel[] = [];

  for (const [stateCode, count] of Object.entries(parcelCountsByState)) {
    allParcels.push(...generateParcelsForState(stateCode, count));
  }

  return allParcels;
}

// Export pre-generated parcels for faster loading
export const US_PARCELS = generateAllUSParcels();

// Helper functions
export function getParcelsByState(stateCode: string): USParcel[] {
  return US_PARCELS.filter(p => p.state_code === stateCode);
}

export function getParcelById(id: string): USParcel | undefined {
  return US_PARCELS.find(p => p.id === id);
}

export function searchParcels(query: {
  states?: string[];
  minAcreage?: number;
  maxAcreage?: number;
  minScore?: number;
  maxScore?: number;
  viability?: string[];
  permission?: string[];
  minSolarGhi?: number;
  minWindSpeed?: number;
  text?: string;
}): USParcel[] {
  return US_PARCELS.filter(p => {
    if (query.states?.length && !query.states.includes(p.state_code)) return false;
    if (query.minAcreage && p.acreage < query.minAcreage) return false;
    if (query.maxAcreage && p.acreage > query.maxAcreage) return false;
    if (query.minScore && p.overall_score < query.minScore) return false;
    if (query.maxScore && p.overall_score > query.maxScore) return false;
    if (query.viability?.length && !query.viability.includes(p.viability)) return false;
    if (query.permission?.length && !query.permission.includes(p.solar_permission)) return false;
    if (query.minSolarGhi && p.solar_ghi < query.minSolarGhi) return false;
    if (query.minWindSpeed && p.wind_speed < query.minWindSpeed) return false;
    if (query.text) {
      const searchText = query.text.toLowerCase();
      const matchFields = [p.county, p.state, p.owner_name, p.address, p.apn].join(' ').toLowerCase();
      if (!matchFields.includes(searchText)) return false;
    }
    return true;
  });
}

// State statistics
export function getStateStatistics() {
  const stats: Record<string, {
    count: number;
    avgScore: number;
    totalAcreage: number;
    totalCapacity: number;
    excellentCount: number;
  }> = {};

  for (const parcel of US_PARCELS) {
    if (!stats[parcel.state_code]) {
      stats[parcel.state_code] = {
        count: 0,
        avgScore: 0,
        totalAcreage: 0,
        totalCapacity: 0,
        excellentCount: 0
      };
    }
    const s = stats[parcel.state_code];
    s.count++;
    s.avgScore += parcel.overall_score;
    s.totalAcreage += parcel.acreage;
    s.totalCapacity += parcel.solar_capacity_mw;
    if (parcel.viability === 'excellent') s.excellentCount++;
  }

  // Calculate averages
  for (const stateCode of Object.keys(stats)) {
    stats[stateCode].avgScore = Math.round(stats[stateCode].avgScore / stats[stateCode].count);
  }

  return stats;
}

// Total statistics
export function getTotalStatistics() {
  const total = {
    parcelCount: US_PARCELS.length,
    stateCount: Object.keys(parcelCountsByState).length,
    totalAcreage: 0,
    totalSolarCapacity: 0,
    totalWindCapacity: 0,
    avgScore: 0,
    excellentCount: 0,
    goodCount: 0,
    moderateCount: 0
  };

  for (const p of US_PARCELS) {
    total.totalAcreage += p.acreage;
    total.totalSolarCapacity += p.solar_capacity_mw;
    total.totalWindCapacity += p.wind_capacity_mw;
    total.avgScore += p.overall_score;
    if (p.viability === 'excellent') total.excellentCount++;
    else if (p.viability === 'good') total.goodCount++;
    else if (p.viability === 'moderate') total.moderateCount++;
  }

  total.avgScore = Math.round(total.avgScore / total.parcelCount);

  return total;
}

export { stateMetadata };
