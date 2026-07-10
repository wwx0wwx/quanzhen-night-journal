import axios, { type AxiosInstance, type AxiosResponse } from 'axios'

export type ApiEnvelope<T = unknown> = {
  code?: number
  message?: string
  message_key?: string
  data?: T
}

export class ApiError extends Error {
  code?: number
  responseData?: ApiEnvelope

  constructor(message: string, code?: number, responseData?: ApiEnvelope) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.responseData = responseData
  }
}

export const api: AxiosInstance = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

export async function unwrap<T = unknown>(promise: Promise<AxiosResponse<ApiEnvelope<T>>>): Promise<T> {
  const response = await promise
  if (response.data?.code && response.data.code !== 0) {
    throw new ApiError(response.data.message || 'request_failed', response.data.code, response.data)
  }
  return response.data?.data as T
}
