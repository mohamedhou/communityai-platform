# Media Library

## Architecture

CommunityAI stores one optional `MediaAsset` reference per post through `posts.media_asset_id`. The existing `posts.media_url` field remains supported for backward compatibility with existing external URLs.

Each asset is scoped to a workspace and records its uploader, original filename, generated storage key, MIME type, extension, size, SHA-256 checksum, and media kind.

## Supported formats and limits

Supported MVP formats:

- Images: JPEG, PNG, WebP, GIF
- Videos: MP4, WebM

The default maximum upload size is 100 MiB and is configured with `MEDIA_MAX_UPLOAD_BYTES`.

The server validates both extension and declared MIME type, and checks file signatures for the supported formats.

## API

- `POST /api/v1/media`: upload a multipart file
- `GET /api/v1/media`: list assets in the active workspace
- `GET /api/v1/media/{media_id}`: retrieve asset metadata
- `GET /api/v1/media/{media_id}/content`: authenticated content response
- `DELETE /api/v1/media/{media_id}`: delete an asset

Post creation and update accept the optional `media_asset_id` field. Sending `media_asset_id: null` removes the attachment.

## Storage and Docker persistence

The MVP uses local storage through the storage service abstraction. Files are stored below `MEDIA_ROOT`, which defaults to `/app/media`.

Docker Compose mounts the named `media_data` volume at `/app/media`. Files therefore survive backend restarts and container recreation while the named volume is retained.

The storage service deliberately exposes storage operations behind an abstraction so it can later be replaced with S3, Azure Blob Storage, or another object store without changing post-domain logic.

## Workspace isolation and authorization

The workspace is resolved from `WorkspaceContext`; clients cannot choose a workspace ID for an upload. Metadata, content, deletion, and post attachment queries require the asset to belong to the active workspace.

The original filename is never used as a physical path. Storage keys are generated server-side and path traversal is rejected.

Workspace editors can upload and delete media. Workspace members can list and read only assets from their active workspace.

## Post attachment and approval

A post supports one asset in this MVP. Replacing or removing the asset is a material post modification.

If an approved draft is modified, its approval is invalidated. If an approved scheduled post is modified, it becomes `DRAFT`, becomes `REJECTED`, and its `scheduled_at` value is cleared. The existing approval and resubmission workflow remains authoritative.

## Provider limitation

Local authenticated media URLs are not automatically publishable by Meta or LinkedIn. External providers may require a publicly reachable URL, signed URL, or provider-specific upload flow. This MVP keeps the domain model ready for that future strategy but does not claim that local private files can be published directly.

## Future object storage strategy

A future object-storage adapter can implement the same save, open, and delete contract. The database should continue storing a provider-neutral storage key and metadata while the API generates an appropriate secured content URL for the active storage provider.
