import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { DeploymentEvidenceCard, GitOpsStatusPanel, KubernetesStatusPanel, OperationsStatusBoard, StatusTimeline } from '@/components/operations/PlatformOpsComponents'
export default function Page(){return <PublicLayout><OperationsStatusBoard/><KubernetesStatusPanel/><GitOpsStatusPanel/><StatusTimeline/><DeploymentEvidenceCard title='Deployment evidence'/></PublicLayout>}
