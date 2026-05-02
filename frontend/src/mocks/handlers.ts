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

export const handlers = [
  ...authHandlers,
  ...patientHandlers,
  ...dentureCaseHandlers,
  ...labCaseHandlers,
  ...treatmentPlanHandlers,
  ...schedulingHandlers,
  ...billingHandlers,
  ...communicationsHandlers,
  ...crmHandlers,
  ...reportingHandlers,
];
