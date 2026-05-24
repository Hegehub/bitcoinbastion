import React from 'react'
import { fireEvent, render } from '@testing-library/react'
import BusinessPage from '../app/trace/business/page'
import BatchPage from '../app/trace/business/batch/page'
import ReviewPage from '../app/trace/business/review/page'
import PoliciesPage from '../app/trace/business/policies/page'
import EnterprisePage from '../app/trace/enterprise/page'
import LegalHoldPage from '../app/trace/enterprise/legal-hold/page'
import AuditPage from '../app/trace/enterprise/audit/page'
import SiemPage from '../app/trace/enterprise/siem/page'
import RetentionPage from '../app/trace/enterprise/retention/page'

test('business dashboard renders',()=>{const {getByText}=render(<BusinessPage/>);expect(getByText(/Business UI is baseline/i)).toBeTruthy()})
test('batch screening rejects sensitive input client-side',()=>{const {getByLabelText,getByText}=render(<BatchPage/>);fireEvent.change(getByLabelText('Batch address input'),{target:{value:'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'}});fireEvent.click(getByText(/Validate Batch/i));expect(getByText(/Sensitive wallet material/i)).toBeTruthy()})
test('review desk and operator notes render',()=>{const {getByText}=render(<ReviewPage/>);expect(getByText(/Review Desk/i)).toBeTruthy();expect(getByText(/Operator Notes/i)).toBeTruthy()})
test('policy UI renders',()=>{const {getByText}=render(<PoliciesPage/>);expect(getByText(/Operational recommendations/i)).toBeTruthy()})
test('enterprise surfaces render',()=>{const {getByText}=render(<EnterprisePage/>);expect(getByText(/Enterprise Governance/i)).toBeTruthy()})
test('legal hold disclaimer visible',()=>{const {getByText}=render(<LegalHoldPage/>);expect(getByText(/not legal advice/i)).toBeTruthy()})
test('audit and hash chain status render',()=>{const {getByText}=render(<AuditPage/>);expect(getByText(/append-only audit log/i)).toBeTruthy()})
test('siem placeholder and retention wording render',()=>{const s=render(<SiemPage/>);expect(s.getByText(/not configured/i)).toBeTruthy();const r=render(<RetentionPage/>);expect(r.getByText(/auto-delete disabled by default/i)).toBeTruthy()})
test('no forbidden wording appears',()=>{render(<BusinessPage/>);const txt=(document.body.textContent||'').toLowerCase();for(const bad of ['clean address','dirty address','criminal address','guaranteed safe','approved payment','legal certificate','compliance certified']) expect(txt.includes(bad)).toBe(false)})
