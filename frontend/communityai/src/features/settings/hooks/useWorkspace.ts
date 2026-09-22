import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import * as workspaceApi from '../services/workspaceApi'
import type {
  WorkspaceInvitationCreate,
  WorkspaceRole,
  MembershipStatus,
} from '../types/workspace'

export const workspaceMembersQueryKey = ['workspace', 'members'] as const
export const workspaceInvitationsQueryKey = ['workspace', 'invitations'] as const

export function useWorkspaceMembers() {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: workspaceMembersQueryKey,
    queryFn: () => workspaceApi.listMembers(accessToken!),
    enabled: Boolean(accessToken),
  })
}

export function useWorkspaceInvitations() {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: workspaceInvitationsQueryKey,
    queryFn: () => workspaceApi.listInvitations(accessToken!),
    enabled: Boolean(accessToken),
  })
}

export function useCreateInvitation() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: WorkspaceInvitationCreate) =>
      workspaceApi.createInvitation(accessToken!, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceInvitationsQueryKey })
    },
  })
}

export function useRevokeInvitation() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (invitationId: number) =>
      workspaceApi.revokeInvitation(accessToken!, invitationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceInvitationsQueryKey })
    },
  })
}

export function useUpdateMemberRole() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ memberId, role }: { memberId: number; role: WorkspaceRole }) =>
      workspaceApi.updateMemberRole(accessToken!, memberId, role),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceMembersQueryKey })
    },
  })
}

export function useUpdateMemberStatus() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ memberId, status }: { memberId: number; status: MembershipStatus }) =>
      workspaceApi.updateMemberStatus(accessToken!, memberId, status),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceMembersQueryKey })
    },
  })
}

export function useRemoveMember() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (memberId: number) =>
      workspaceApi.removeMember(accessToken!, memberId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceMembersQueryKey })
    },
  })
}

export function useInvitationPreview(token: string) {
  return useQuery({
    queryKey: ['workspace', 'invitation', token],
    queryFn: () => workspaceApi.previewInvitation(token),
    enabled: Boolean(token),
    retry: false,
  })
}

export function useAcceptInvitation() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (token: string) =>
      workspaceApi.acceptInvitation(accessToken!, token),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceMembersQueryKey })
    },
  })
}
