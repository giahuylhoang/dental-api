import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetcher } from '../../api/client';
import ToothChart from '../patients/ToothChart';
import { nextActions } from './statusFlow';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

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
      fetcher<TreatmentPlan>(`/api/v2/treatment-plans`, {
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

  const transitionMutation = useMutation({
    mutationFn: (endpoint: string) =>
      fetcher<TreatmentPlan>(`/api/v2/treatment-plans/${planId}/${endpoint}`, {
        method: 'POST',
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

  // Group items by tooth for tooltip
  const toothItemsMap: Record<number, PlanItem[]> = {};
  items.forEach((item) => {
    if (item.tooth_number != null) {
      if (!toothItemsMap[item.tooth_number]) toothItemsMap[item.tooth_number] = [];
      toothItemsMap[item.tooth_number].push(item);
    }
  });

  const { subtotal, insuranceEst, gst, patientEst } = computeTotals(items);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Treatment Plan</h3>
        <Badge variant="secondary">{status}</Badge>
      </div>

      <Tabs defaultValue="items">
        <TabsList>
          <TabsTrigger value="items">Items</TabsTrigger>
          <TabsTrigger value="tooth-chart">Tooth Chart</TabsTrigger>
          <TabsTrigger value="care-notes">Care Notes</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        {/* Items tab */}
        <TabsContent value="items">
          <ScrollArea className="max-h-[60vh]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-200 text-left text-zinc-500">
                  <th className="pb-2 pr-2 font-medium">Tooth</th>
                  <th className="pb-2 pr-2 font-medium">Code</th>
                  <th className="pb-2 pr-2 font-medium">Description</th>
                  <th className="pb-2 pr-2 font-medium">Fee</th>
                  <th className="pb-2 pr-2 font-medium">Ins %</th>
                  <th className="pb-2 font-medium" />
                </tr>
              </thead>
              <tbody>
                {items.map((item, idx) => (
                  <tr key={idx} className="border-b border-zinc-100">
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
                    <td className="py-1.5">
                      <button onClick={() => removeItem(idx)} className="text-zinc-400 hover:text-red-500">✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollArea>

          {/* Add procedure form */}
          <div className="mt-3 space-y-2">
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
          <Card className="mt-4">
            <CardContent className="p-4 text-sm">
              <h4 className="mb-2 font-medium">Estimate Breakdown</h4>
              <div className="space-y-1 text-zinc-600">
                <div className="flex justify-between"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
                <div className="flex justify-between"><span>GST (5%)</span><span>${gst.toFixed(2)}</span></div>
                <div className="flex justify-between"><span>Insurance estimate</span><span>-${insuranceEst.toFixed(2)}</span></div>
                <div className="flex justify-between border-t border-zinc-200 pt-1 font-medium text-zinc-900">
                  <span>Patient estimate</span><span>${patientEst.toFixed(2)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tooth Chart tab */}
        <TabsContent value="tooth-chart">
          <Card>
            <CardContent className="p-4">
              <TooltipProvider>
                <ToothChart
                  patientId={patientId}
                  onToothClick={(num) => {
                    handleToothClick(num);
                  }}
                  highlightedTeeth={highlightedTeeth}
                />
                {/* Tooltip hint for highlighted teeth */}
                {highlightedTeeth.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {highlightedTeeth.map((toothNum) => {
                      const toothItems = toothNum != null ? toothItemsMap[toothNum] : undefined;
                      if (!toothItems?.length) return null;
                      return (
                        <Tooltip key={toothNum}>
                          <TooltipTrigger asChild>
                            <span className="cursor-pointer rounded bg-orange-100 px-2 py-0.5 text-xs text-orange-700">
                              Tooth {toothNum}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            <ul className="text-xs space-y-0.5">
                              {toothItems.map((item, i) => (
                                <li key={i}>{item.procedure_code} — {item.description}</li>
                              ))}
                            </ul>
                          </TooltipContent>
                        </Tooltip>
                      );
                    })}
                  </div>
                )}
              </TooltipProvider>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Care Notes tab */}
        <TabsContent value="care-notes">
          <ScrollArea className="max-h-[60vh]">
            <div className="space-y-3 pt-2">
              {items.map((item, idx) => (
                <div key={idx} className="space-y-1">
                  <p className="text-xs font-medium text-zinc-500">
                    {item.procedure_code} — {item.description}
                  </p>
                  <textarea
                    aria-label="care notes"
                    value={item.care_notes ?? ''}
                    maxLength={1000}
                    rows={2}
                    onChange={(e) => updateItem(idx, 'care_notes', e.target.value || null)}
                    className="w-full rounded border border-zinc-200 px-2 py-1 text-sm focus:outline-none resize-y"
                    placeholder="Care notes…"
                  />
                </div>
              ))}
              {items.length === 0 && (
                <p className="text-sm text-zinc-400">No items yet.</p>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* History tab */}
        <TabsContent value="history">
          <p className="pt-2 text-sm text-zinc-400">No history recorded.</p>
        </TabsContent>
      </Tabs>

      {/* Status transition footer */}
      <div className="flex flex-wrap gap-2 border-t border-zinc-200 pt-4">
        <Button onClick={handleSave} variant="default">
          Save Draft
        </Button>
        {planId && nextActions(status).map((action) => (
          <Button
            key={action.endpoint}
            onClick={() => transitionMutation.mutate(action.endpoint)}
            variant={
              action.variant === 'green'
                ? 'outline'
                : action.variant === 'red'
                ? 'destructive'
                : 'outline'
            }
            className={
              action.variant === 'green'
                ? 'border-green-300 text-green-700 hover:bg-green-50'
                : ''
            }
          >
            {action.label}
          </Button>
        ))}
        {planId && status === 'accepted' && (
          <Button
            variant="outline"
            className="border-blue-300 text-blue-700 hover:bg-blue-50"
            onClick={() => generateInvoiceMutation.mutate()}
          >
            Generate invoice from plan
          </Button>
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
