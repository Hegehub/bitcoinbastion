import React from 'react'
import { render } from '@testing-library/react'
import Home from '../app/page'
import Trace from '../app/trace/page'
import Treasury from '../app/treasury/page'
import Register from '../app/register/page'
import Operations from '../app/operations/page'
import { TopNav } from '../components/navigation/TopNav'

test('landing renders',()=>{const {getAllByText}=render(<Home/>);expect(getAllByText(/Bitcoin Bastion/).length).toBeGreaterThan(0)})
test('module pages render',()=>{const a=render(<Trace/>);expect(a.getAllByText(/Trace/i).length).toBeGreaterThan(0);const b=render(<Treasury/>);expect(b.getAllByText(/No custody/i).length).toBeGreaterThan(0)})
test('register no auto accept/reject claim',()=>{const {getByText}=render(<Register/>);expect(getByText(/does not auto-accept or auto-reject/i)).toBeTruthy()})
test('operations mentions evidence jobs',()=>{const {getByText}=render(<Operations/>);expect(getByText(/evidence jobs/i)).toBeTruthy()})
test('navigation contains modules',()=>{const {getByText}=render(<TopNav/>);for(const t of ['Platform','Citadel','Trace','Treasury','Register','Developers','Operations','Security','Status','Docs']) expect(getByText(t)).toBeTruthy()})
test('forbidden wording absent',()=>{render(<Home/>);const txt=document.body.textContent?.toLowerCase()||'';for(const bad of ['clean address','dirty address','guaranteed safe','legally verified','approved payment']) expect(txt.includes(bad)).toBe(false)})
