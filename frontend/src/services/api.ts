const baseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'
export async function api<T>(path: string): Promise<T> { const response = await fetch(`${baseUrl}${path}`); if (!response.ok) throw new Error(`API error ${response.status}`); return response.json() }

