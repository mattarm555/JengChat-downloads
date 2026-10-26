# Private source builds

JengChat source visibility is unchanged. The draft build uses the read-only deploy key named `Protected friends release builds (read only)` on the source repository. Its private key exists only in the `friends-release` environment secret `JENGCHAT_SOURCE_READ_KEY`; checkout removes credentials after fetching. No personal access token is needed and credentials are never packaged.

Revoke that deploy key and replace the encrypted environment secret together to rotate access. The draft/publish jobs still use this repository's ephemeral GITHUB_TOKEN. Source archives distributed with each release are intentional redistribution artifacts even though the repository itself is private.
