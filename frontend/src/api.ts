import axios from 'axios'
import type { Fortune100Company, JobsResponse, ScrapeResult, Stats } from './types'

const client = axios.create({ baseURL: '/api' })

export async function fetchStats(): Promise<Stats> {
  const { data } = await client.get<Stats>('/stats')
  return data
}

export async function fetchJobs(params?: {
  source?: string
  q?: string
  skill?: string
  fortune100?: boolean
  fortune100_company?: string
  limit?: number
}): Promise<JobsResponse> {
  const { data } = await client.get<JobsResponse>('/jobs', { params })
  return data
}

export async function fetchFortune100Companies(): Promise<Fortune100Company[]> {
  const { data } = await client.get<Fortune100Company[]>('/careers/companies')
  return data
}

export async function triggerScrape(): Promise<ScrapeResult> {
  const { data } = await client.post<ScrapeResult>('/scrape')
  return data
}

export async function triggerCareersScrape(): Promise<ScrapeResult> {
  const { data } = await client.post<ScrapeResult>('/scrape/careers', null, {
    timeout: 300000,
  })
  return data
}
