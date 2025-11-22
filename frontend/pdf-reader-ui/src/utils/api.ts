// API configuration utility for DocaCast

/**
 * Get the API base URL based on environment
 * In Vercel, this will automatically use the same domain for API calls
 */
export const getApiBaseUrl = (): string => {
  // Check if we have a custom API base URL
  const customUrl = import.meta.env.VITE_API_BASE_URL;
  
  if (customUrl) {
    return customUrl.replace(/\/$/, '');
  }
  
  // In production (Vercel), use relative URLs for API calls
  if (import.meta.env.PROD) {
    return window.location.origin;
  }
  
  // Default for local development
  return 'http://127.0.0.1:8001';
};

/**
 * Make API calls with proper error handling
 */
export const apiCall = async (endpoint: string, options: RequestInit = {}): Promise<any> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  
  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };
  
  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: `HTTP ${response.status}`,
        message: response.statusText
      }));
      throw new Error(errorData.message || errorData.error || 'API request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error);
    throw error;
  }
};

/**
 * Upload file with progress tracking
 */
export const uploadFile = async (
  file: File, 
  onProgress?: (progress: number) => void
): Promise<any> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/upload`;
  
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = (event.loaded / event.total) * 100;
        onProgress(progress);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (error) {
          reject(new Error('Invalid JSON response'));
        }
      } else {
        reject(new Error(`Upload failed: ${xhr.statusText}`));
      }
    });
    
    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed'));
    });
    
    xhr.open('POST', url);
    xhr.send(formData);
  });
};

/**
 * Generate audio podcast
 */
export const generateAudio = async (config: {
  filename: string;
  podcast?: boolean;
  two_speakers?: boolean;
  content_style?: string;
  tts_engine?: string;
}): Promise<any> => {
  return apiCall('/generate-audio', {
    method: 'POST',
    body: JSON.stringify(config),
  });
};

/**
 * Search documents
 */
export const searchDocuments = async (query: string, filename?: string, top_k: number = 5): Promise<any> => {
  return apiCall('/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      filename,
      top_k,
    }),
  });
};

/**
 * Health check
 */
export const healthCheck = async (): Promise<any> => {
  return apiCall('/health', {
    method: 'GET',
  });
};
