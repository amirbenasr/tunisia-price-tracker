import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add API key to requests if available
apiClient.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('api_key')
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

// Types for API responses
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Website {
  id: string
  name: string
  base_url: string
  logo_url?: string
  description?: string
  scraper_type: string
  is_active: boolean
  rate_limit_ms: number
  last_scraped_at?: string
  total_products: number
  created_at: string
  updated_at: string
}

export interface Product {
  id: string
  website_id: string
  website_name: string
  external_id: string
  name: string
  description?: string
  brand?: string
  product_url: string
  image_url?: string
  current_price?: number
  original_price?: number
  currency: string
  in_stock: boolean
}

export interface SearchResult {
  product_id: string
  product_name: string
  brand?: string
  website: string
  website_id: string
  website_logo?: string
  price: number
  original_price?: number
  currency: string
  in_stock: boolean
  product_url: string
  image_url?: string
  last_updated: string
  match_score: number
}

export interface SearchResponse {
  query: string
  results: SearchResult[]
  total_results: number
  websites_searched: number
  search_time_ms: number
}

export interface SitemapConfig {
  sitemap_url: string
  child_sitemap_pattern?: string
  url_include_pattern?: string
  url_exclude_pattern?: string
  use_lastmod?: boolean
}

export interface ScraperConfig {
  id: string
  website_id: string
  config_type: string
  selectors: Record<string, string>
  pagination_config?: Record<string, unknown>
  sitemap_config?: SitemapConfig
  version: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ScrapeLog {
  id: string
  website_id: string
  started_at: string
  completed_at?: string
  status: string
  products_found: number
  products_created: number
  products_updated: number
  prices_recorded: number
  pages_scraped: number
  errors?: Array<Record<string, unknown>>
  triggered_by?: string
  duration_seconds?: number
}

export interface DashboardStats {
  total_websites: number
  active_websites: number
  total_products: number
  total_price_records: number
  scrapes_today: number
  scrapes_success_rate: number
  products_added_today: number
  price_changes_today: number
}

// API functions
export const api = {
  // Health
  health: () => apiClient.get('/health'),

  // Stats
  getDashboardStats: () =>
    apiClient.get<DashboardStats>('/stats/dashboard'),

  // Search
  searchPrices: (query: string, params?: Record<string, unknown>) =>
    apiClient.get<SearchResponse>('/search/prices', { params: { q: query, ...params } }),

  // Websites
  getWebsites: (page = 1, pageSize = 20) =>
    apiClient.get<PaginatedResponse<Website>>('/websites', { params: { page, page_size: pageSize } }),

  getWebsite: (id: string) =>
    apiClient.get<Website>(`/websites/${id}`),

  createWebsite: (data: Partial<Website>) =>
    apiClient.post<Website>('/websites', data),

  updateWebsite: (id: string, data: Partial<Website>) =>
    apiClient.put<Website>(`/websites/${id}`, data),

  deleteWebsite: (id: string) =>
    apiClient.delete(`/websites/${id}`),

  getWebsiteStats: (id: string) =>
    apiClient.get(`/websites/${id}/stats`),

  // Products
  getProducts: (params?: { website_id?: string; page?: number; page_size?: number }) =>
    apiClient.get<PaginatedResponse<Product>>('/products', { params }),

  getProduct: (id: string) =>
    apiClient.get<Product>(`/products/${id}`),

  // Prices
  getPriceHistory: (productId: string, days = 30) =>
    apiClient.get(`/prices/history/${productId}`, { params: { days } }),

  getPriceDrops: (hours = 24, limit = 50) =>
    apiClient.get('/prices/drops', { params: { hours, limit } }),

  // Scrapers
  getScraperConfigs: (websiteId: string) =>
    apiClient.get<ScraperConfig[]>(`/scrapers/${websiteId}/config`),

  updateScraperConfig: (websiteId: string, configId: string, data: Partial<ScraperConfig>) =>
    apiClient.put<ScraperConfig>(`/scrapers/${websiteId}/config/${configId}`, data),

  createScraperConfig: (websiteId: string, data: Partial<ScraperConfig>) =>
    apiClient.post<ScraperConfig>(`/scrapers/${websiteId}/config`, data),

  triggerScrape: (websiteId: string, options?: { full_scrape?: boolean; max_pages?: number }) =>
    apiClient.post(`/scrapers/${websiteId}/run`, options || {}),

  getScrapeLogs: (websiteId: string, page = 1, pageSize = 20) =>
    apiClient.get<PaginatedResponse<ScrapeLog>>(`/scrapers/${websiteId}/logs`, { params: { page, page_size: pageSize } }),
}

export default api
