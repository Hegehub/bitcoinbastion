# Rollback policy
Primary rollback is Git revert of the promotion commit (digest change), followed by Argo CD sync.
No mutable latest tags in production.
