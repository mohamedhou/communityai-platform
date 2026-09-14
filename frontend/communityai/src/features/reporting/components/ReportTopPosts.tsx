import { TopPostsTable } from '../../analytics/components/TopPostsTable'
import type { TopPostMetric } from '../../analytics/types/analytics'

export function ReportTopPosts({ posts }: { posts: TopPostMetric[] }) { return <section className="report-section"><TopPostsTable posts={posts} /></section> }