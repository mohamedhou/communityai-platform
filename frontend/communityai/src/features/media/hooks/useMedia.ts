import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import * as mediaApi from '../services/mediaApi'

export function useMediaLibrary() {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['media-library'],
    queryFn: () => mediaApi.listMedia(accessToken!),
    enabled: !!accessToken,
  })
}

export function useUploadMedia(onProgress?: (value: number) => void) {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => mediaApi.uploadMedia(accessToken!, file, onProgress),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['media-library'] }),
  })
}

export function useDeleteMedia() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (mediaId: number) => mediaApi.deleteMedia(accessToken!, mediaId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['media-library'] }),
  })
}
