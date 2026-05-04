"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetcher } from "@/lib/api/client";
import { Drawer } from "@/components/dental/Drawer";
import { FormField } from "@/components/dental/FormField";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect } from "react";

interface PatientInsurance {
  id?: string;
  carrier: string;
  policy_number: string;
  group_number?: string | null;
  holder_name: string;
  holder_relationship?: string | null;
  is_primary: boolean;
  assignment_of_benefits: boolean;
}

const schema = z.object({
  carrier: z.string().min(1, "Required"),
  policy_number: z.string().min(1, "Required"),
  group_number: z.string().optional(),
  holder_name: z.string().min(1, "Required"),
  holder_relationship: z.string().optional(),
  is_primary: z.boolean(),
  assignment_of_benefits: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

function InsuranceDrawer({
  patientId,
  insurance,
  open,
  onClose,
}: {
  patientId: string;
  insurance?: PatientInsurance;
  open: boolean;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const isEdit = !!insurance?.id;

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { carrier: "", policy_number: "", group_number: "", holder_name: "", holder_relationship: "", is_primary: false, assignment_of_benefits: false },
  });

  useEffect(() => {
    if (insurance) {
      reset({
        carrier: insurance.carrier,
        policy_number: insurance.policy_number,
        group_number: insurance.group_number ?? "",
        holder_name: insurance.holder_name,
        holder_relationship: insurance.holder_relationship ?? "",
        is_primary: insurance.is_primary,
        assignment_of_benefits: insurance.assignment_of_benefits,
      });
    } else {
      reset({ carrier: "", policy_number: "", group_number: "", holder_name: "", holder_relationship: "", is_primary: false, assignment_of_benefits: false });
    }
  }, [insurance, reset]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      if (isEdit) {
        return fetcher<PatientInsurance>(`/api/v2/clinical/patients/${patientId}/insurance/${insurance!.id}`, { method: "PUT", body: JSON.stringify(values) });
      }
      return fetcher<PatientInsurance>(`/api/v2/clinical/patients/${patientId}/insurance`, { method: "POST", body: JSON.stringify(values) });
    },
    onSuccess: () => { void qc.invalidateQueries({ queryKey: ["insurance", patientId] }); onClose(); },
  });

  return (
    <Drawer open={open} onClose={onClose} title={isEdit ? "Edit Insurance" : "Add Insurance"}>
      <form id="insurance-form" onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-1">
        <FormField label="Carrier" error={errors.carrier?.message}>
          <input {...register("carrier")} className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
        </FormField>
        <FormField label="Policy Number" error={errors.policy_number?.message}>
          <input {...register("policy_number")} className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
        </FormField>
        <FormField label="Group Number" error={errors.group_number?.message}>
          <input {...register("group_number")} className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
        </FormField>
        <FormField label="Holder Name" error={errors.holder_name?.message}>
          <input {...register("holder_name")} className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
        </FormField>
        <FormField label="Holder Relationship" error={errors.holder_relationship?.message}>
          <input {...register("holder_relationship")} className="w-full rounded border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary" />
        </FormField>
        <div className="flex items-center gap-2 py-1">
          <input id="is_primary" type="checkbox" {...register("is_primary")} className="h-4 w-4 rounded border-border" />
          <label htmlFor="is_primary" className="text-sm text-foreground">Primary insurance</label>
        </div>
        <div className="flex items-center gap-2 py-1">
          <input id="aob" type="checkbox" {...register("assignment_of_benefits")} className="h-4 w-4 rounded border-border" />
          <label htmlFor="aob" className="text-sm text-foreground">Assignment of benefits</label>
        </div>
        {mutation.isError && <p className="text-sm text-destructive">{(mutation.error as Error).message}</p>}
        <div className="flex gap-2 pt-2">
          <button type="submit" form="insurance-form" disabled={mutation.isPending} className="rounded bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-80 disabled:opacity-50">
            {isEdit ? "Update" : "Add"}
          </button>
          <button type="button" onClick={onClose} className="rounded border border-border px-3 py-1.5 text-sm hover:bg-muted">Cancel</button>
        </div>
      </form>
    </Drawer>
  );
}

export function InsurancePanel({ patientId }: { patientId: string }) {
  const qc = useQueryClient();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<PatientInsurance | undefined>(undefined);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data: insurances = [], isLoading } = useQuery<PatientInsurance[]>({
    queryKey: ["insurance", patientId],
    queryFn: () => fetcher<PatientInsurance[]>(`/api/v2/clinical/patients/${patientId}/insurance`),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => fetcher<void>(`/api/v2/clinical/patients/${patientId}/insurance/${id}`, { method: "DELETE" }),
    onSuccess: () => { void qc.invalidateQueries({ queryKey: ["insurance", patientId] }); setDeletingId(null); },
  });

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <button onClick={() => { setEditing(undefined); setDrawerOpen(true); }} className="rounded bg-foreground px-3 py-1.5 text-sm text-background hover:opacity-80">
          Add insurance
        </button>
      </div>
      {insurances.length === 0 && <p className="text-sm text-muted-foreground">No insurance records.</p>}
      {insurances.map((ins) => (
        <div key={ins.id} className="flex items-center justify-between rounded border border-border px-3 py-2 text-sm cursor-pointer hover:bg-muted/40" onClick={() => { setEditing(ins); setDrawerOpen(true); }}>
          <div className="space-y-0.5">
            <div className="font-medium">{ins.carrier}</div>
            <div className="text-muted-foreground">Policy: {ins.policy_number}{ins.group_number ? ` · Group: ${ins.group_number}` : ""}</div>
            <div className="text-muted-foreground">Holder: {ins.holder_name}</div>
          </div>
          <div className="flex items-center gap-2">
            {ins.is_primary && <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">Primary</span>}
            <button onClick={(e) => { e.stopPropagation(); setDeletingId(ins.id ?? null); }} className="rounded border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive">
              Delete
            </button>
          </div>
        </div>
      ))}
      {deletingId && (
        <div className="rounded border border-border bg-muted/30 p-4">
          <p className="mb-3 text-sm">Delete this insurance record?</p>
          <div className="flex gap-2">
            <button onClick={() => deleteMutation.mutate(deletingId)} disabled={deleteMutation.isPending} className="rounded bg-destructive px-3 py-1.5 text-sm text-white hover:opacity-80 disabled:opacity-50">Delete</button>
            <button onClick={() => setDeletingId(null)} className="rounded border border-border px-3 py-1.5 text-sm hover:bg-muted">Cancel</button>
          </div>
        </div>
      )}
      <InsuranceDrawer patientId={patientId} insurance={editing} open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  );
}
