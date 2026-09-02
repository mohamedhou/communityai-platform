import { getPosts, schedulePost } from '../../posts/services/postApi'
import type { Post } from '../../posts/types/post'

export async function fetchCalendarPosts(token: string): Promise<Post[]> {
  return getPosts(token)
}

export async function rescheduleCalendarPost(
  token: string,
  postId: number,
  scheduledAtIso: string
): Promise<Post> {
  return schedulePost(token, postId, scheduledAtIso)
}
