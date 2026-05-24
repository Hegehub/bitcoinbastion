import React from 'react'
import { render } from '@testing-library/react'
import DashboardPage from '../app/dashboard/page'
import PlatformPage from '../app/dashboard/platform/page'
import CitadelPage from '../app/dashboard/citadel/page'
import OpsPage from '../app/dashboard/operations/page'
import EventsPage from '../app/dashboard/runtime-events/page'
import StatusPage from '../app/dashboard/status/page'

test('dashboard renders',()=>{const {getByText}=render(<DashboardPage/>);expect(getByText(/Bitcoin Bastion Dashboard/i)).toBeTruthy()})
test('module status grid renders',()=>{const {getByText}=render(<PlatformPage/>);expect(getByText(/Module Status/i)).toBeTruthy()})
test('citadel overview renders',()=>{const {getByText}=render(<CitadelPage/>);expect(getByText(/Citadel outputs are advisory-only/i)).toBeTruthy()})
test('operations dashboard renders',()=>{const {getByText}=render(<OpsPage/>);expect(getByText(/Operations UI does not manage infrastructure directly/i)).toBeTruthy()})
test('runtime events feed and severity render',()=>{const {getByText}=render(<EventsPage/>);expect(getByText(/INFO/i)).toBeTruthy();expect(getByText(/HIGH/i)).toBeTruthy()})
test('status/readiness panels render',()=>{const {getByText}=render(<StatusPage/>);expect(getByText(/Platform Readiness/i)).toBeTruthy()})
test('forbidden wording absent',()=>{render(<DashboardPage/>);const txt=(document.body.textContent||'').toLowerCase();for(const bad of ['fully secure','guaranteed safe','production-certified','legally verified','ai verified','clean address','dirty address']) expect(txt.includes(bad)).toBe(false)})
