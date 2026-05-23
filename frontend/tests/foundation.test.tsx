import React from 'react'
import { render } from '@testing-library/react'
import { StatusBadge } from '../components/ui/StatusBadge'
import { SafetyWarning } from '../components/public/SafetyWarning'

test('status badge renders',()=>{const {getByText}=render(<StatusBadge label='baseline'/>);expect(getByText('baseline')).toBeTruthy()})
test('safety warnings visible',()=>{const {getByText}=render(<SafetyWarning/>);expect(getByText(/No seed\/private key handling/i)).toBeTruthy()})
