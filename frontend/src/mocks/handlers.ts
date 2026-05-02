import { authHandlers } from './auth';
import { patientHandlers } from './patients';
import { dentureCaseHandlers } from './denture-cases';
import { labCaseHandlers } from './lab-cases';
import { treatmentPlanHandlers } from './treatment-plans';
import {
  schedulingHandlers,
  billingHandlers,
  communicationsHandlers,
  crmHandlers,
  reportingHandlers,
} from './ops';
import { pmsP1Handlers } from './pms-p1';
import { pmsP2Handlers } from './pms-p2';
import { pmsP3Handlers } from './pms-p3';
import { pmsP4Handlers } from './pms-p4';
import { pmsP5Handlers } from './pms-p5';

export const handlers = [
  ...authHandlers,
  // pmsP5 first: overrides /api/v2/billing/invoices/:id and adds insurance/claims
  ...pmsP5Handlers,
  // pmsP4 first: overrides /api/v2/treatment-plans and /api/v2/patients
  ...pmsP4Handlers,
  // pmsP2 must come before patientHandlers to override /api/appointments
  ...pmsP2Handlers,
  ...patientHandlers,
  // pmsP3 before dentureCaseHandlers to add GET /denture-cases/:id
  ...pmsP3Handlers,
  ...dentureCaseHandlers,
  ...labCaseHandlers,
  ...treatmentPlanHandlers,
  ...schedulingHandlers,
  ...billingHandlers,
  ...communicationsHandlers,
  ...crmHandlers,
  ...reportingHandlers,
  ...pmsP1Handlers,
];
