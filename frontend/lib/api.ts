/**
 * TerraJinki API Client
 *
 * TypeScript client for interacting with the TerraJinki backend API.
 */

// Use local API routes when no external API is configured (demo mode)
const API_URL = process.env.NEXT_PUBLIC_API_URL || '';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || '';

// =============================================================================
// TYPES
// =============================================================================

export interface Parcel {
  id: string;
  apn: string;
  state: string;
  county: string;
  municipality: string;
  address: string;
  acreage: number;
  zoning_type: string;
  solar_permission: string;
  owner_name: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  project_type: string;
  stage: string;
  parcel_ids: string[];
  total_acreage: number;
  capacity_mw: number;
  created_at: string;
}

export interface Analysis {
  id: string;
  parcel_id: string;
  status: string;
  overall_score: number;
  permitting_score: number;
  grid_score: number;
  environmental_score: number;
  land_score: number;
  viability: string;
  fatal_flaws: string[];
  recommendations: string[];
  duration_seconds: number;
}

export interface SearchResult {
  total_matches: number;
  returned_count: number;
  parcels: Parcel[];
  interpreted_query: string;
  search_duration_ms: number;
}

export interface AnalysisProgress {
  type: string;
  analysis_id: string;
  status: string;
  progress: number;
  current_step: string;
  elapsed_seconds: number;
  estimated_remaining: number;
  partial_results?: Record<string, unknown>;
}

// =============================================================================
// API CLIENT
// =============================================================================

class TerraJinkiClient {
  private baseUrl: string;
  private wsUrl: string;

  constructor() {
    this.baseUrl = API_URL;
    this.wsUrl = WS_URL;
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Health
  async health() {
    return this.fetch<{ status: string; version: string; timestamp: string }>('/api/health');
  }

  async stats() {
    return this.fetch<{
      parcels_count: number;
      projects_count: number;
      analyses_count: number;
      high_value_sites?: number;
      config: Record<string, unknown>;
    }>('/api/stats');
  }

  // Parcels
  async createParcel(data: {
    state: string;
    county: string;
    acreage: number;
    municipality?: string;
    address?: string;
    latitude?: number;
    longitude?: number;
    zoning_type?: string;
    solar_permission?: string;
    owner_name?: string;
    nearest_substation_mi?: number;
  }): Promise<Parcel> {
    return this.fetch<Parcel>('/api/parcels', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getParcel(id: string): Promise<Parcel> {
    return this.fetch<Parcel>(`/api/parcels/${id}`);
  }

  async searchParcels(query: {
    query?: string;
    states?: string[];
    counties?: string[];
    min_acreage?: number;
    max_acreage?: number;
    limit?: number;
    offset?: number;
  }): Promise<SearchResult> {
    return this.fetch<SearchResult>('/api/parcels/search', {
      method: 'POST',
      body: JSON.stringify(query),
    });
  }

  async naturalLanguageSearch(query: string): Promise<SearchResult> {
    return this.fetch<SearchResult>(`/api/parcels/search/natural?query=${encodeURIComponent(query)}`);
  }

  // Analysis
  async analyzeSite(parcelId: string, options?: {
    project_type?: string;
    target_capacity_mw?: number;
    include_financial?: boolean;
  }): Promise<Analysis> {
    return this.fetch<Analysis>('/api/analysis', {
      method: 'POST',
      body: JSON.stringify({
        parcel_id: parcelId,
        ...options,
      }),
    });
  }

  async quickScore(parcelId: string): Promise<{
    quick_score: number;
    confidence: number;
    key_factors: string[];
    recommendation: string;
  }> {
    return this.fetch('/api/analyze/quick', {
      method: 'POST',
      body: JSON.stringify({ parcel_id: parcelId }),
    });
  }

  // Projects
  async createProject(data: {
    name: string;
    project_type?: string;
    state?: string;
    county?: string;
    capacity_mw?: number;
  }): Promise<Project> {
    return this.fetch<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getProject(id: string): Promise<Project> {
    return this.fetch<Project>(`/projects/${id}`);
  }

  async listProjects(stage?: string): Promise<Project[]> {
    const url = stage ? `/api/projects?stage=${stage}` : '/api/projects';
    return this.fetch<Project[]>(url);
  }

  async addParcelToProject(projectId: string, parcelId: string): Promise<void> {
    await this.fetch(`/projects/${projectId}/parcels/${parcelId}`, {
      method: 'POST',
    });
  }

  // WebSocket for real-time analysis
  analyzeRealtime(
    parcelId: string,
    onProgress: (progress: AnalysisProgress) => void,
    onError: (error: Error) => void,
    onComplete: () => void,
  ): () => void {
    const ws = new WebSocket(`${this.wsUrl}/ws/analyze/${parcelId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.error) {
        onError(new Error(data.error));
      } else {
        onProgress(data);
        if (data.status === 'completed' || data.status === 'failed') {
          onComplete();
        }
      }
    };

    ws.onerror = () => {
      onError(new Error('WebSocket connection failed'));
    };

    ws.onclose = () => {
      onComplete();
    };

    // Return cleanup function
    return () => {
      ws.close();
    };
  }

  // WebSocket for AI copilot
  connectCopilot(
    onMessage: (message: { type: string; message: string; suggestions?: string[] }) => void,
    onError: (error: Error) => void,
  ): {
    send: (message: string) => void;
    close: () => void;
  } {
    const ws = new WebSocket(`${this.wsUrl}/ws/copilot`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onerror = () => {
      onError(new Error('Copilot WebSocket connection failed'));
    };

    return {
      send: (message: string) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ message }));
        }
      },
      close: () => {
        ws.close();
      },
    };
  }
}

// Export singleton instance
export const api = new TerraJinkiClient();

// Export class for custom instances
export { TerraJinkiClient };
