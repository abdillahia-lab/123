// Enterprise-Grade State Management with Zustand
// Features: Persistence, devtools, middleware, selectors

import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type {
  Parcel,
  Project,
  User,
  UserPreferences,
  Alert,
  ParcelSearchQuery,
} from '../core/types';

// ============================================================================
// STORE TYPES
// ============================================================================

interface AppState {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  preferences: UserPreferences;

  // UI state
  sidebarCollapsed: boolean;
  currentView: 'dashboard' | 'scout' | 'map' | 'market' | 'financial' | 'pipeline' | 'settings';
  selectedParcelId: string | null;
  selectedProjectId: string | null;
  isLoading: boolean;
  loadingMessage: string | null;

  // Search state
  searchQuery: ParcelSearchQuery;
  searchHistory: ParcelSearchQuery[];
  savedSearches: Array<{ name: string; query: ParcelSearchQuery }>;

  // Data state
  parcels: Map<string, Parcel>;
  projects: Map<string, Project>;
  favorites: Set<string>;

  // Notifications
  alerts: Alert[];
  unreadCount: number;

  // Filters
  activeFilters: {
    states: string[];
    viability: string[];
    minScore: number | null;
    minAcreage: number | null;
  };

  // Compare mode
  compareMode: boolean;
  compareParcels: string[];
}

interface AppActions {
  // Auth actions
  setUser: (user: User | null) => void;
  logout: () => void;

  // UI actions
  setSidebarCollapsed: (collapsed: boolean) => void;
  setCurrentView: (view: AppState['currentView']) => void;
  selectParcel: (id: string | null) => void;
  selectProject: (id: string | null) => void;
  setLoading: (loading: boolean, message?: string | null) => void;

  // Preferences
  setPreferences: (prefs: Partial<UserPreferences>) => void;
  setTheme: (theme: UserPreferences['theme']) => void;

  // Search actions
  setSearchQuery: (query: ParcelSearchQuery) => void;
  clearSearch: () => void;
  addToSearchHistory: (query: ParcelSearchQuery) => void;
  saveSearch: (name: string, query: ParcelSearchQuery) => void;
  deleteSavedSearch: (name: string) => void;

  // Data actions
  setParcel: (parcel: Parcel) => void;
  setParcels: (parcels: Parcel[]) => void;
  setProject: (project: Project) => void;
  setProjects: (projects: Project[]) => void;

  // Favorites
  toggleFavorite: (parcelId: string) => void;
  clearFavorites: () => void;

  // Alerts
  addAlert: (alert: Alert) => void;
  dismissAlert: (alertId: string) => void;
  clearAlerts: () => void;
  markAlertsAsRead: () => void;

  // Filters
  setActiveFilters: (filters: Partial<AppState['activeFilters']>) => void;
  clearFilters: () => void;

  // Compare mode
  toggleCompareMode: () => void;
  addToCompare: (parcelId: string) => void;
  removeFromCompare: (parcelId: string) => void;
  clearCompare: () => void;

  // Reset
  reset: () => void;
}

// ============================================================================
// INITIAL STATE
// ============================================================================

const initialState: AppState = {
  user: null,
  isAuthenticated: false,
  preferences: {
    theme: 'system',
    notifications: {
      email: true,
      push: true,
      alerts: true,
    },
    defaultView: 'scout',
    favoriteStates: [],
  },

  sidebarCollapsed: false,
  currentView: 'scout',
  selectedParcelId: null,
  selectedProjectId: null,
  isLoading: false,
  loadingMessage: null,

  searchQuery: {},
  searchHistory: [],
  savedSearches: [],

  parcels: new Map(),
  projects: new Map(),
  favorites: new Set(),

  alerts: [],
  unreadCount: 0,

  activeFilters: {
    states: [],
    viability: [],
    minScore: null,
    minAcreage: null,
  },

  compareMode: false,
  compareParcels: [],
};

// ============================================================================
// STORE CREATION
// ============================================================================

export const useAppStore = create<AppState & AppActions>()(
  devtools(
    subscribeWithSelector(
      persist(
        immer((set, get) => ({
          ...initialState,

          // Auth actions
          setUser: (user) =>
            set((state) => {
              state.user = user;
              state.isAuthenticated = !!user;
            }),

          logout: () =>
            set((state) => {
              state.user = null;
              state.isAuthenticated = false;
            }),

          // UI actions
          setSidebarCollapsed: (collapsed) =>
            set((state) => {
              state.sidebarCollapsed = collapsed;
            }),

          setCurrentView: (view) =>
            set((state) => {
              state.currentView = view;
            }),

          selectParcel: (id) =>
            set((state) => {
              state.selectedParcelId = id;
            }),

          selectProject: (id) =>
            set((state) => {
              state.selectedProjectId = id;
            }),

          setLoading: (loading, message = null) =>
            set((state) => {
              state.isLoading = loading;
              state.loadingMessage = message;
            }),

          // Preferences
          setPreferences: (prefs) =>
            set((state) => {
              state.preferences = { ...state.preferences, ...prefs };
            }),

          setTheme: (theme) =>
            set((state) => {
              state.preferences.theme = theme;
            }),

          // Search actions
          setSearchQuery: (query) =>
            set((state) => {
              state.searchQuery = query;
            }),

          clearSearch: () =>
            set((state) => {
              state.searchQuery = {};
            }),

          addToSearchHistory: (query) =>
            set((state) => {
              // Keep only last 20 searches
              const history = [query, ...state.searchHistory].slice(0, 20);
              state.searchHistory = history;
            }),

          saveSearch: (name, query) =>
            set((state) => {
              // Remove existing with same name
              const filtered = state.savedSearches.filter((s) => s.name !== name);
              state.savedSearches = [...filtered, { name, query }];
            }),

          deleteSavedSearch: (name) =>
            set((state) => {
              state.savedSearches = state.savedSearches.filter((s) => s.name !== name);
            }),

          // Data actions
          setParcel: (parcel) =>
            set((state) => {
              state.parcels.set(parcel.id, parcel);
            }),

          setParcels: (parcels) =>
            set((state) => {
              parcels.forEach((p) => state.parcels.set(p.id, p));
            }),

          setProject: (project) =>
            set((state) => {
              state.projects.set(project.id, project);
            }),

          setProjects: (projects) =>
            set((state) => {
              projects.forEach((p) => state.projects.set(p.id, p));
            }),

          // Favorites
          toggleFavorite: (parcelId) =>
            set((state) => {
              if (state.favorites.has(parcelId)) {
                state.favorites.delete(parcelId);
              } else {
                state.favorites.add(parcelId);
              }
            }),

          clearFavorites: () =>
            set((state) => {
              state.favorites.clear();
            }),

          // Alerts
          addAlert: (alert) =>
            set((state) => {
              state.alerts.unshift(alert);
              state.unreadCount++;
              // Keep only last 100 alerts
              if (state.alerts.length > 100) {
                state.alerts = state.alerts.slice(0, 100);
              }
            }),

          dismissAlert: (alertId) =>
            set((state) => {
              state.alerts = state.alerts.filter((a) => a.id !== alertId);
            }),

          clearAlerts: () =>
            set((state) => {
              state.alerts = [];
              state.unreadCount = 0;
            }),

          markAlertsAsRead: () =>
            set((state) => {
              state.unreadCount = 0;
            }),

          // Filters
          setActiveFilters: (filters) =>
            set((state) => {
              state.activeFilters = { ...state.activeFilters, ...filters };
            }),

          clearFilters: () =>
            set((state) => {
              state.activeFilters = initialState.activeFilters;
            }),

          // Compare mode
          toggleCompareMode: () =>
            set((state) => {
              state.compareMode = !state.compareMode;
              if (!state.compareMode) {
                state.compareParcels = [];
              }
            }),

          addToCompare: (parcelId) =>
            set((state) => {
              if (state.compareParcels.length < 5 && !state.compareParcels.includes(parcelId)) {
                state.compareParcels.push(parcelId);
              }
            }),

          removeFromCompare: (parcelId) =>
            set((state) => {
              state.compareParcels = state.compareParcels.filter((id) => id !== parcelId);
            }),

          clearCompare: () =>
            set((state) => {
              state.compareParcels = [];
            }),

          // Reset
          reset: () => set(initialState),
        })),
        {
          name: 'terrajinki-storage',
          version: 3,
          partialize: (state) => ({
            preferences: state.preferences,
            favorites: Array.from(state.favorites),
            savedSearches: state.savedSearches,
            sidebarCollapsed: state.sidebarCollapsed,
          }),
          // Custom serialization for Set
          storage: {
            getItem: (name) => {
              const str = localStorage.getItem(name);
              if (!str) return null;
              const data = JSON.parse(str);
              if (data.state?.favorites) {
                data.state.favorites = new Set(data.state.favorites);
              }
              return data;
            },
            setItem: (name, value) => {
              const data = { ...value };
              if (data.state?.favorites instanceof Set) {
                data.state.favorites = Array.from(data.state.favorites);
              }
              localStorage.setItem(name, JSON.stringify(data));
            },
            removeItem: (name) => localStorage.removeItem(name),
          },
        }
      )
    ),
    { name: 'TerraJinki Store' }
  )
);

// ============================================================================
// SELECTORS
// ============================================================================

export const selectUser = (state: AppState) => state.user;
export const selectIsAuthenticated = (state: AppState) => state.isAuthenticated;
export const selectPreferences = (state: AppState) => state.preferences;
export const selectTheme = (state: AppState) => state.preferences.theme;
export const selectCurrentView = (state: AppState) => state.currentView;
export const selectSelectedParcel = (state: AppState) =>
  state.selectedParcelId ? state.parcels.get(state.selectedParcelId) : null;
export const selectFavorites = (state: AppState) => state.favorites;
export const selectUnreadCount = (state: AppState) => state.unreadCount;
export const selectCompareMode = (state: AppState) => state.compareMode;
export const selectCompareParcels = (state: AppState) => state.compareParcels;

// Computed selectors
export const selectFavoriteCount = (state: AppState) => state.favorites.size;
export const selectHasActiveFilters = (state: AppState) =>
  state.activeFilters.states.length > 0 ||
  state.activeFilters.viability.length > 0 ||
  state.activeFilters.minScore !== null ||
  state.activeFilters.minAcreage !== null;

// ============================================================================
// HOOKS
// ============================================================================

export function useCurrentView() {
  return useAppStore((state) => state.currentView);
}

export function useSelectedParcel() {
  return useAppStore(selectSelectedParcel);
}

export function useTheme() {
  return useAppStore(selectTheme);
}

export function useFavorites() {
  const favorites = useAppStore(selectFavorites);
  const toggleFavorite = useAppStore((state) => state.toggleFavorite);
  return { favorites, toggleFavorite };
}
