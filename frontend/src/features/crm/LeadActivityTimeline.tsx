interface Activity {
  id: string;
  kind: string;
  body: string;
  author?: string;
  created_at: string;
}

interface Props {
  activities: Activity[];
}

export default function LeadActivityTimeline({ activities }: Props) {
  if (activities.length === 0) {
    return <p className="text-sm text-zinc-400">No activities yet.</p>;
  }
  return (
    <ul className="flex flex-col gap-3">
      {activities.map((a) => (
        <li key={a.id} className="rounded border border-zinc-200 bg-zinc-50 p-3 text-sm">
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span className="font-medium capitalize">{a.kind}</span>
            <span>{a.author ?? 'Unknown'} · {new Date(a.created_at).toLocaleString()}</span>
          </div>
          <p className="mt-1 text-zinc-800">{a.body}</p>
        </li>
      ))}
    </ul>
  );
}
