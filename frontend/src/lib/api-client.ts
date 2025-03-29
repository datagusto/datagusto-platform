import { getToken, clearToken, redirectToLogin } from "@/utils/auth";

// Types for API requests
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

interface RequestOptions extends Omit<RequestInit, 'method' | 'body'> {
  params?: Record<string, string | number | boolean | undefined>;
  data?: Record<string, any> | FormData;
}

interface ApiResponse<T = any> {
  data: T;
  error?: string;
  status: number;
}

// Utility to build URL with query parameters
const buildUrl = (endpoint: string, params?: Record<string, string | number | boolean | undefined>): string => {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    throw new Error('API URL not configured');
  }

  // Build the base URL
  let url = `${apiUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  // Add query parameters if they exist
  if (params && Object.keys(params).length > 0) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    
    const queryString = queryParams.toString();
    if (queryString) {
      url += `${url.includes('?') ? '&' : '?'}${queryString}`;
    }
  }
  
  return url;
};

// Core request function
async function request<T = any>(
  method: HttpMethod,
  endpoint: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const { params, data, headers: customHeaders = {}, ...restOptions } = options;
  const url = buildUrl(endpoint, params);
  
  // Prepare headers
  const headers = new Headers(customHeaders);
  const token = getToken();
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  // If we have data and it's not already FormData, set Content-Type and stringify
  let body: string | FormData | undefined = undefined;
  if (data) {
    if (data instanceof FormData) {
      body = data;
    } else {
      headers.set('Content-Type', 'application/json');
      body = JSON.stringify(data);
    }
  }
  
  try {
    const response = await fetch(url, {
      method,
      headers,
      body,
      credentials: 'include',
      ...restOptions,
    });
    
    // Handle 401 unauthorized
    if (response.status === 401) {
      // Clear the token and redirect to login page
      clearToken();
      redirectToLogin(window.location.pathname);
      throw new Error('Authentication required');
    }
    
    // Try to parse JSON response
    let responseData: T;
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      responseData = await response.json();
    } else {
      // For non-JSON responses
      const text = await response.text();
      responseData = text as unknown as T;
    }
    
    // Return standardized response
    return {
      data: responseData,
      status: response.status,
    };
  } catch (error) {
    // Handle errors
    console.error(`API request failed: ${url}`, error);
    
    return {
      data: null as unknown as T,
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 500,
    };
  }
}

// API client with convenience methods
export const apiClient = {
  // GET request
  get: <T = any>(endpoint: string, options?: RequestOptions) => 
    request<T>('GET', endpoint, options),
  
  // POST request
  post: <T = any>(endpoint: string, data?: Record<string, any> | FormData, options?: Omit<RequestOptions, 'data'>) => 
    request<T>('POST', endpoint, { ...options, data }),
  
  // PUT request
  put: <T = any>(endpoint: string, data?: Record<string, any> | FormData, options?: Omit<RequestOptions, 'data'>) => 
    request<T>('PUT', endpoint, { ...options, data }),
  
  // PATCH request
  patch: <T = any>(endpoint: string, data?: Record<string, any> | FormData, options?: Omit<RequestOptions, 'data'>) => 
    request<T>('PATCH', endpoint, { ...options, data }),
  
  // DELETE request
  delete: <T = any>(endpoint: string, options?: RequestOptions) => 
    request<T>('DELETE', endpoint, options),
};

// Mock data handling
interface MockImplementation<T> {
  getData: () => T;
  find?: (id: string) => any;
  create?: (data: any) => any;
  update?: (id: string, data: any) => any;
  delete?: (id: string) => void;
}

export class MockApiClient<T> {
  private mockData: T;
  private mockImplementation: MockImplementation<T>;
  
  constructor(mockImplementation: MockImplementation<T>) {
    this.mockImplementation = mockImplementation;
    this.mockData = mockImplementation.getData();
  }
  
  async get(id?: string): Promise<T | any> {
    if (id && this.mockImplementation.find) {
      return Promise.resolve(this.mockImplementation.find(id));
    }
    return Promise.resolve(this.mockData);
  }
  
  async create(data: any): Promise<any> {
    if (this.mockImplementation.create) {
      return Promise.resolve(this.mockImplementation.create(data));
    }
    throw new Error('Create not implemented for this mock');
  }
  
  async update(id: string, data: any): Promise<any> {
    if (this.mockImplementation.update) {
      return Promise.resolve(this.mockImplementation.update(id, data));
    }
    throw new Error('Update not implemented for this mock');
  }
  
  async delete(id: string): Promise<void> {
    if (this.mockImplementation.delete) {
      this.mockImplementation.delete(id);
      return Promise.resolve();
    }
    throw new Error('Delete not implemented for this mock');
  }
}

export default apiClient; 