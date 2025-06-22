import { cookies } from 'next/headers';
import type { UserProjectInfo } from '@/types/project';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getServerAuthHeaders(): Promise<Record<string, string>> {
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value;
  
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

export async function getServerUserProjects(): Promise<UserProjectInfo[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/projects/`, {
      method: 'GET',
      headers: await getServerAuthHeaders(),
      cache: 'no-store', // Always fetch fresh data
    });

    if (!response.ok) {
      console.error('Failed to fetch server projects:', response.status);
      return [];
    }

    return response.json();
  } catch (error) {
    console.error('Server projects fetch error:', error);
    return [];
  }
}