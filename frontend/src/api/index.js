import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

export async function unwrap(promise) {
  const response = await promise
  if (response.data?.code && response.data.code !== 0) {
    const error = new Error(response.data.message || 'request_failed')
    error.code = response.data.code
    error.responseData = response.data
    throw error
  }
  return response.data?.data
}
