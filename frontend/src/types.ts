export interface Job {
  id: number
  external_id: string
  source: string
  title: string
  company: string
  location: string
  job_type: string
  salary: string
  description: string
  skills: string
  url: string
  posted_at: string
  scraped_at: string
  search_label: string
}

export interface SourceCount {
  source: string
  count: number
}

export interface CompanyCount {
  company: string
  count: number
}

export interface Fortune100Company {
  rank: number
  name: string
  slug: string
  country: string
  career_url: string
  job_count: number
}

export interface SkillCount {
  skill: string
  count: number
}

export interface Stats {
  total_jobs: number
  total_companies: number
  total_sources: number
  last_scrape: string | null
  by_source: SourceCount[]
  top_companies: CompanyCount[]
  top_skills: SkillCount[]
  recent_jobs: Job[]
}

export interface ScrapeResult {
  status: string
  jobs_added: number
  jobs_updated: number
  duration_seconds: number
  by_source: SourceCount[]
  errors: string[]
}

export interface JobsResponse {
  total: number
  jobs: Job[]
}
