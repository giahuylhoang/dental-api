import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetcher } from '../../api/client';
import ToothChart from '../patients/ToothChart';

interface PlanItem {
  id?: string;
  sequence: number;
  procedure_code: string;
  description: string | null;
  fee: number;
  insurance_coverage_pct: number | null;
  completed_at: string | null;
  tooth_number?: number | null;
  care_notes?: string | null;
}

interface TreatmentPlan {
  id?: string;
  patient_id: string;
  status: string;
  total_estimate: number;
  insurance_estimate: number;
  patient_estimate: number;
  items: PlanItem[];
}

interface Procedure {
  id: string;
  code: string;
  name: string;
  default_fee: number | null;
}

interface TreatmentPlanEditorProps {
  patientId: string;
  planId?: string;
  onSaved?: (plan: TreatmentPlan) => void;
}

const GST_RATE = 0.05;

function computeTotals(items: PlanItem[]) {
  const subtotal = items.reduce((s, i) => s + i.fee, 0);
  const insuranceEst = items.reduce(
    (s, i) => s + i.fee * ((i.insurance_coverage_pct ?? 0) / 100),
    0,
  );
  const gst = subtotal * GST_RATE;
  return { subtotal, insuranceEst, gst, patientEst: subtotal + gst - insuranceEst };
}

export default function TreatmentPlanEditor({ patientId, planId, onSaved }: TreatmentPlanEditorProps) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [localItems, setLocalItems] = useState<PlanItem[]>([]);
  const [codeSearch, setCodeSearch] = useState('');
  const [localStatus] = useState('draft');
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [selectedTooth, setSelectedTooth] = useState<number | null>(null);
  const [addToothNumber, setAddToothNumber] = useState<string>('');
  const [itemsInitialized, setItemsInitialized] = useState(false);

  const { data: existingPlan } = useQuery<TreatmentPlan>({
    queryKey: ['treatment-plan', planId],
    queryFn: () => fetcher<TreatmentPlan>(`/api/v2/treatment-plans/${planId}`),
    enabled: !!planId,
  });

  // Sync server items into local editable state once on load
  if (existingPlan && !itemsInitialized) {
    setLocalItems(existingPlan.items);
    setItemsInitialized(true);
  }

  const items = localItems;
  const status = existingPlan ? existingPlan.status : localStatus;

  const { data: procedures = [] } = useQuery<Procedure[]>({
    queryKey: ['procedures', codeSearch],
    queryFn: () => fetcher<Procedure[]>(`/api/v2/clinical/procedures?q=${encodeURIComponent(codeSearch)}`),
    enabled: codeSearch.length > 0,
  });

  const saveMutation = useMutation({
    mutationFn: (plan: Partial<TreatmentPlan>) =>
      fetcher<TreatmentPlan>(`/api/v2/clinical/patients/${patientId}/treatment-plans`, {
        method: 'POST',
        body: JSON.stringify(plan),
      }),
    onSuccess: (saved) => onSaved?.(saved),
  });

  const patchItemsMutation = useMutation({
    mutationFn: (updatedItems: PlanItem[]) =>
      fetcher<TreatmentPlan>(`/api/v2/treatment-plans/${planId}/items`, {
        method: 'PATCH',
        body: JSON.stringify({ items: updatedItems }),
      }),
    onSuccess: (saved) => {
      qc.setQueryData(['treatment-plan', planId], saved);
      onSaved?.(saved);
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: (newStatus: string) =>
      fetcher<TreatmentPlan>(`/api/v2/treatment-plans/${planId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      }),
    onSuccess: (saved) => {
      qc.setQueryData(['treatment-plan', planId], saved);
      onSaved?.(saved);
    },
  });

  const generateInvoiceMutation = useMutation({
    mutationFn: () =>
      fetcher<{ id: string }>('/api/v2/billing/invoices/from-plan', {
        method: 'POST',
        body: JSON.stringify({ treatment_plan_id: planId, patient_id: patientId }),
      }),
    onSuccess: (inv) => {
      setToastMsg(`Invoice ${inv.id} created`);
      navigate('/billing');
    },
  });

  function handleToothClick(num: number) {
    setSelectedTooth(num);
    setAddToothNumber(String(num));
  }

  function addProcedure(proc: Procedure) {
    const toothNum = addToothNumber ? parseInt(addToothNumber, 10) : null;
    setLocalItems((prev) => [
      ...prev,
      {
        sequence: prev.length + 1,
        procedure_code: proc.code,
        description: proc.name,
        fee: proc.default_fee ?? 0,
        insurance_coverage_pct: null,
        completed_at: null,
        tooth_number: toothNum && !isNaN(toothNum) ? toothNum : null,
        care_notes: null,
      },
    ]);
    setCodeSearch('');
    setSelectedTooth(null);
    setAddToothNumber('');
  }

  function removeItem(idx: number) {
    setLocalItems((prev) => prev.filter((_, i) => i !== idx).map((item, i) => ({ ...item, sequence: i + 1 })));
  }

  function updateItem(idx: number, field: keyof PlanItem, value: string | number | null) {
    setLocalItems((prev) => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  }

  function handleSave() {
    if (planId) {
      patchItemsMutation.mutate(items);
    } else {
      saveMutation.mutate({ patient_id: patientId, status: 'draft', items });
    }
  }

  const highlightedTeeth = items.map((i) => i.tooth_number).filter(Boolean) as number[];

  // Group items by tooth_number for visual row grouping
  const toothGroups: Record<string, string> = {};
  const groupColors = ['#fef9c3', '#dbeafe', '#dcfce7', '#fce7f3', '#ede9fe'];
  let colorIdx = 0;
  items.forEach((item) => {
    const key = item.tooth_number != null ? String(item.tooth_number) : '';
    if (key && !(key in toothGroups)) {
      toothGroups[key] = groupColors[colorIdx++ % groupColors.length];
    }
  });

  const { subtotal, insuranceEst, gst, patientEst } = computeTotals(items);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Treatment Plan</h3>
        <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">{status}</span>
      </div>

      {/* Tooth chart */}
      <ToothChart
        patientId={patientId}
        onToothClick={handleToothClick}
        highlightedTeeth={highlightedTeeth}
      />

      {/* Line items */}
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-200 text-left text-zinc-500">
            <th className="pb-2 pr-2 font-medium">Tooth</th>
            <th className="pb-2 pr-2 font-medium">Code</th>
            <th className="pb-2 pr-2 font-medium">Description</th>
            <th className="pb-2 pr-2 font-medium">Fee</th>
            <th className="pb-2 pr-2 font-medium">Ins %</th>
            <th className="pb-2 pr-2 font-medium">Notes</th>
            <th className="pb-2 font-medium" />
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => {
            const groupKey = item.tooth_number != null ? String(item.tooth_number) : '';
            const rowBg = groupKey ? toothGroups[groupKey] : undefined;
            return (
              <tr key={idx} className="border-b border-zinc-100" style={rowBg ? { backgroundColor: rowBg } : undefined}>
                <td className="py-1.5 pr-2">
                  <input
                    type="number"
                    aria-label="tooth number"
                    value={item.tooth_number ?? ''}
                    onChange={(e) => updateItem(idx, 'tooth_number', e.target.value ? parseInt(e.target.value, 10) : null)}
                    className="w-14 rounded border border-zinc-200 px-2 py-1 text-sm focus:outline-none"
                  />
                </td>
                <td className="py-1.5 pr-2">{item.procedure_code}</td>
                <td className="py-1.5 pr-2">
                  <input
                    value={item.description ?? ''}
                    onChange={(e) => updateItem(idx, 'description', e.target.value)}
                    className="w-full rounded border border-zinc-200 px-2 py-1 text-sm focus:outline-none"
                  />
                </td>
                <td className="py-1.5 pr-2">
                  <input
                    type="number"
                    value={item.fee}
                    onChange={(e) => updateItem(idx, 'fee', parseFloat(e.target.value) || 0)}
                    className="w-24 rounded border border-zinc-200 px-2 py-1 text-sm focus:outline-none"
                  />
                </td>
                <td className="py-1.5 pr-2">
                  <input
                    type="number"
                    value={item.insurance_coverage_pct ?? ''}
                    onChange={(e) => updateItem(idx, 'insurance_coverage_pct', e.target.value ? parseFloat(e.target.value) : null)}
                    placeholder="0"
                    className="w-16 rounded border border-zinc-200 px-2 py-1 text-sm focus:outline-none"
                  />
                </td>
                <td className="py-1.5 pr-2">
                  <textarea
                    aria-label="care notes"
                    value={item.care_notes ?? ''}
                    maxLength={1000}
                    rows={1}
                    onChange={(e) => updateItem(idx, 'care_notes', e.target.value || null)}
                    className="w-full rounded border border-zinc-200 px-2 py-1 text-sm focus:outline-none resize-y"
                  />
                </td>
                <td className="py-1.5">
                  <button onClick={() => removeItem(idx)} className="text-zinc-400 hover:text-red-500">✕</button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Add procedure form */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <label htmlFor="add-tooth-number" className="text-xs text-zinc-500 whitespace-nowrap">Tooth #</label>
          <input
            id="add-tooth-number"
            type="number"
            aria-label="tooth_number"
            value={addToothNumber}
            onChange={(e) => {
              setAddToothNumber(e.target.value);
              setSelectedTooth(e.target.value ? parseInt(e.target.value, 10) : null);
            }}
            placeholder={selectedTooth ? String(selectedTooth) : '—'}
            className="w-16 rounded border border-zinc-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
        </div>
        <div className="relative">
          <input
            value={codeSearch}
            onChange={(e) => setCodeSearch(e.target.value)}
            placeholder="Search procedure code or name…"
            className="w-full max-w-sm rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
          />
          {procedures.length > 0 && codeSearch && (
            <ul className="absolute z-10 mt-1 w-full max-w-sm rounded border border-zinc-200 bg-white shadow-md">
              {procedures.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => addProcedure(p)}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-zinc-50"
                  >
                    <span className="font-mono text-xs text-zinc-500">{p.code}</span> {p.name}
                    {p.default_fee != null && <span className="ml-2 text-zinc-400">${p.default_fee}</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Estimate breakdown */}
      <div className="rounded-lg border border-zinc-200 p-4 text-sm">
        <h4 className="mb-2 font-medium">Estimate Breakdown</h4>
        <div className="space-y-1 text-zinc-600">
          <div className="flex justify-between"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
          <div className="flex justify-between"><span>GST (5%)</span><span>${gst.toFixed(2)}</span></div>
          <div className="flex justify-between"><span>Insurance estimate</span><span>-${insuranceEst.toFixed(2)}</span></div>
          <div className="flex justify-between border-t border-zinc-200 pt-1 font-medium text-zinc-900">
            <span>Patient estimate</span><span>${patientEst.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Workflow buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={handleSave}
          className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-700"
        >
          Save Draft
        </button>
        {planId && status === 'draft' && (
          <button
            onClick={() => updateStatusMutation.mutate('presented')}
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
          >
            Present
          </button>
        )}
        {planId && status === 'presented' && (
          <>
            <button
              onClick={() => updateStatusMutation.mutate('accepted')}
              className="rounded border border-green-300 px-3 py-1.5 text-sm text-green-700 hover:bg-green-50"
            >
              Accept
            </button>
            <button
              onClick={() => updateStatusMutation.mutate('declined')}
              className="rounded border border-red-300 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
            >
              Decline
            </button>
          </>
        )}
        {planId && status === 'accepted' && (
          <>
            <button
              onClick={() => updateStatusMutation.mutate('completed')}
              className="rounded border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-50"
            >
              Complete
            </button>
            <button
              onClick={() => generateInvoiceMutation.mutate()}
              className="rounded border border-blue-300 px-3 py-1.5 text-sm text-blue-700 hover:bg-blue-50"
            >
              Generate invoice from plan
            </button>
          </>
        )}
      </div>
      {toastMsg && (
        <div className="rounded bg-green-50 border border-green-200 px-3 py-2 text-sm text-green-800">
          {toastMsg}
        </div>
      )}
    </div>
  );
}
