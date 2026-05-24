import React from 'react'
import { PublicLayout } from '@/components/layout/PublicLayout'
import { BusinessProofPacketActions, OperatorNotesPanel, ReviewDeskTable, ReviewItemPanel } from '@/components/business/BusinessComponents'

export default function Page(){return <PublicLayout><ReviewDeskTable/><ReviewItemPanel/><OperatorNotesPanel/><BusinessProofPacketActions/></PublicLayout>}
