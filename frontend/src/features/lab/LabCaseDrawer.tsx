import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import ImplantForm from './ImplantForm';
import MaterialConsumptionForm from './MaterialConsumptionForm';
import DentureCaseDrawer from './DentureCaseDrawer';
import { PatientChip } from '../patients/PatientChip';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface LabCase {
  id: string;
  case_number?: string;
  denture_case_id: string;
  vendor_id: string;
  status: string;
  sent_at: string | null;
  due_back_at: string | null;
  returned_at: string | null;
  remake_of_id: string | null;
  remake_reason: string | null;
  lab_fee: number | null;
  courier_tracking: string | null;
  treatment_plan_id?: string | null;
  patient_id?: string | null;
}

interface Vendor {
  id: string;
  name: string;
}

interface TreatmentPlan {
  id: string;
  status: string;
  patient_id: string;
}

interface Implant {
  id: string;
  tooth_position: number;
  vendor: string;
  lot_number: string;
  surface_treatment: string;
  abutment_type: string;
  placed_date: string | null;
}

interface Props {
  caseId: string | null;
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
}

export default function LabCaseDrawer({ caseId, open, onClose, onChanged }: Props) {
  const qc = useQueryClient();
  const [tab, setTab] = useState('detail');
  const [showRemake, setShowRemake] = useState(false);
  const [remakeReason, setRemakeReason] = useState('');
  const [dentureCaseOpen, setDentureCaseOpen] = useState(false);

  const { data: cases = [] } = useQuery<LabCase[]>({
    queryKey: ['lab-cases'],
    queryFn: () => fetcher<LabCase[]>('/api/v2/lab/cases'),
    enabled: open && !!caseId,
  });
  const labCase = cases.find((c) => c.id === caseId) ?? null;

  const { data: vendors = [] } = useQuery<Vendor[]>({
    queryKey: ['lab-vendors'],
    queryFn: () => fetcher<Vendor[]>('/api/v2/lab/vendors'),
    enabled: open,
  });
  const vendor = vendors.find((v) => v.id === labCase?.vendor_id);

  const { data: linkedPlan } = useQuery<TreatmentPlan>({
    queryKey: ['treatment-plan', labCase?.treatment_plan_id],
    queryFn: () => fetcher<TreatmentPlan>(`/api/v2/treatment-plans/${labCase!.treatment_plan_id}`),
    enabled: open && !!labCase?.treatment_plan_id,
  });

  const { data: implants = [], refetch: refetchImplants } = useQuery<Implant[]>({
    queryKey: ['denture-implants', labCase?.denture_case_id],
    queryFn: () =>
      fetcher<Implant[]>(`/api/v2/clinical/denture-cases/${labCase!.denture_case_id}/implants`),
    enabled: open && !!labCase?.denture_case_id && tab === 'implants',
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['lab-cases'] });
    onChanged();
  };

  const sendMut = useMutation({
    mutationFn: () => fetcher(`/api/v2/lab/cases/${caseId}/send`, { method: 'POST' }),
    onSuccess: invalidate,
  });

  const returnMut = useMutation({
    mutationFn: () => fetcher(`/api/v2/lab/cases/${caseId}/return`, { method: 'POST' }),
    onSuccess: invalidate,
  });

  const remakeMut = useMutation({
    mutationFn: (reason: string) =>
      fetcher(`/api/v2/lab/cases/${caseId}/remake`, {
        method: 'POST',
        body: JSON.stringify({ remake_reason: reason }),
      }),
    onSuccess: () => {
      setShowRemake(false);
      setRemakeReason('');
      invalidate();
    },
  });

  return (
    <>
      <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
        <SheetContent side="right" className="w-full sm:max-w-lg flex flex-col">
          <SheetHeader>
            <SheetTitle>
              <div className="flex flex-col gap-1">
                {labCase?.patient_id && (
                  <PatientChip patientId={labCase.patient_id} variant="card" />
                )}
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono text-sm text-zinc-600">
                    {labCase?.case_number ?? `#${caseId}`}
                  </span>
                  {vendor && <span className="text-sm text-zinc-500">{vendor.name}</span>}
                  {labCase && (
                    <Badge variant="secondary">{labCase.status}</Badge>
                  )}
                </div>
              </div>
            </SheetTitle>
          </SheetHeader>

          {!labCase ? (
            <p className="text-sm text-zinc-500 mt-4">Loading…</p>
          ) : (
            <Tabs value={tab} onValueChange={setTab} className="flex-1 flex flex-col mt-4">
              <TabsList>
                <TabsTrigger value="detail">Detail</TabsTrigger>
                <TabsTrigger value="implants">Implants</TabsTrigger>
                <TabsTrigger value="materials">Materials</TabsTrigger>
                <TabsTrigger value="events">Events</TabsTrigger>
              </TabsList>

              <TabsContent value="detail" className="flex-1">
                <ScrollArea className="h-full">
                  <div className="space-y-2 text-sm pt-2">
                    <div><span className="text-zinc-500">Vendor: </span>{vendor?.name ?? labCase.vendor_id}</div>
                    <div><span className="text-zinc-500">Status: </span>{labCase.status}</div>
                    {labCase.due_back_at && (
                      <div><span className="text-zinc-500">Due back: </span>{new Date(labCase.due_back_at).toLocaleDateString()}</div>
                    )}
                    {labCase.lab_fee != null && (
                      <div><span className="text-zinc-500">Lab fee: </span>${labCase.lab_fee}</div>
                    )}
                    {labCase.courier_tracking && (
                      <div><span className="text-zinc-500">Tracking: </span>{labCase.courier_tracking}</div>
                    )}
                    {labCase.denture_case_id && (
                      <div>
                        <span className="text-zinc-500">Denture case: </span>
                        <button
                          onClick={() => setDentureCaseOpen(true)}
                          className="text-blue-600 hover:underline"
                        >
                          Open denture case
                        </button>
                      </div>
                    )}
                    {labCase.treatment_plan_id && (
                      <div>
                        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-zinc-500">Linked Treatment Plan</p>
                        {linkedPlan && (
                          <span className="mr-2 inline-block rounded bg-zinc-100 px-1.5 py-0.5 text-xs capitalize text-zinc-700">
                            {linkedPlan.status}
                          </span>
                        )}
                        <a
                          href={`/plans?focus=${labCase.treatment_plan_id}`}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          Open plan →
                        </a>
                      </div>
                    )}
                    <div className="flex gap-2 border-t border-zinc-100 pt-3">
                      <Button size="sm" onClick={() => sendMut.mutate()} disabled={sendMut.isPending}>
                        Send
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => returnMut.mutate()} disabled={returnMut.isPending}>
                        Return
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setShowRemake(true)}>
                        Remake
                      </Button>
                    </div>
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="implants" className="flex-1">
                <ScrollArea className="h-full">
                  {labCase.denture_case_id && (
                    <div className="space-y-4 pt-2">
                      <ImplantForm
                        dentureCaseId={labCase.denture_case_id}
                        onSaved={() => void refetchImplants()}
                      />
                      {implants.length > 0 && (
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-zinc-200 text-left text-zinc-500">
                              <th className="pb-1">Tooth</th>
                              <th className="pb-1">Vendor</th>
                              <th className="pb-1">Lot #</th>
                              <th className="pb-1">Surface</th>
                              <th className="pb-1">Abutment</th>
                            </tr>
                          </thead>
                          <tbody>
                            {implants.map((imp) => (
                              <tr key={imp.id} className="border-b border-zinc-100">
                                <td className="py-1">{imp.tooth_position}</td>
                                <td className="py-1">{imp.vendor}</td>
                                <td className="py-1">{imp.lot_number}</td>
                                <td className="py-1">{imp.surface_treatment}</td>
                                <td className="py-1">{imp.abutment_type}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  )}
                </ScrollArea>
              </TabsContent>

              <TabsContent value="materials" className="flex-1">
                <ScrollArea className="h-full">
                  <div className="pt-2">
                    <MaterialConsumptionForm labCaseId={caseId!} onSaved={invalidate} />
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="events" className="flex-1">
                <ScrollArea className="h-full">
                  <p className="pt-2 text-sm text-zinc-400">No events recorded.</p>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          )}
        </SheetContent>
      </Sheet>

      {/* Remake reason dialog */}
      {showRemake && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg">
            <h4 className="mb-3 font-medium">Remake Reason</h4>
            <textarea
              value={remakeReason}
              onChange={(e) => setRemakeReason(e.target.value)}
              placeholder="Describe the reason…"
              rows={3}
              className="mb-4 w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowRemake(false)}>Cancel</Button>
              <Button onClick={() => remakeMut.mutate(remakeReason)} disabled={remakeMut.isPending}>
                Confirm Remake
              </Button>
            </div>
          </div>
        </div>
      )}

      <DentureCaseDrawer
        caseId={labCase?.denture_case_id ?? null}
        open={dentureCaseOpen}
        onClose={() => setDentureCaseOpen(false)}
        onChanged={onChanged}
      />
    </>
  );
}
