import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Drawer from '../../components/Drawer';
import { fetcher } from '../../api/client';
import ImplantForm from './ImplantForm';
import MaterialConsumptionForm from './MaterialConsumptionForm';
import DentureCaseDrawer from './DentureCaseDrawer';

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

type Tab = 'detail' | 'implants' | 'materials';

interface Props {
  caseId: string | null;
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
}

export default function LabCaseDrawer({ caseId, open, onClose, onChanged }: Props) {
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>('detail');
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
      <Drawer open={open} onClose={onClose} title={`Lab Case #${caseId ?? ''}`} width="lg">
        {!labCase ? (
          <p className="text-sm text-zinc-500">Loading…</p>
        ) : (
          <div className="flex h-full flex-col">
            {/* Tabs */}
            <div className="mb-4 flex gap-1 border-b border-zinc-200">
              {(['detail', 'implants', 'materials'] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-3 py-1.5 text-sm capitalize ${tab === t ? 'border-b-2 border-zinc-900 font-medium' : 'text-zinc-500 hover:text-zinc-900'}`}
                >
                  {t}
                </button>
              ))}
            </div>

            {tab === 'detail' && (
              <div className="space-y-2 text-sm">
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
                  <button
                    onClick={() => sendMut.mutate()}
                    disabled={sendMut.isPending}
                    className="rounded bg-indigo-600 px-3 py-1 text-xs text-white hover:bg-indigo-700 disabled:opacity-40"
                  >
                    Send
                  </button>
                  <button
                    onClick={() => returnMut.mutate()}
                    disabled={returnMut.isPending}
                    className="rounded bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-40"
                  >
                    Return
                  </button>
                  <button
                    onClick={() => setShowRemake(true)}
                    className="rounded border border-zinc-300 px-3 py-1 text-xs hover:bg-zinc-50"
                  >
                    Remake
                  </button>
                </div>
              </div>
            )}

            {tab === 'implants' && labCase.denture_case_id && (
              <div className="space-y-4">
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

            {tab === 'materials' && (
              <MaterialConsumptionForm labCaseId={caseId!} onSaved={invalidate} />
            )}
          </div>
        )}
      </Drawer>

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
              <button onClick={() => setShowRemake(false)} className="rounded border border-zinc-300 px-3 py-1.5 text-sm">
                Cancel
              </button>
              <button
                onClick={() => remakeMut.mutate(remakeReason)}
                disabled={remakeMut.isPending}
                className="rounded bg-zinc-900 px-3 py-1.5 text-sm text-white disabled:opacity-40"
              >
                Confirm Remake
              </button>
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
