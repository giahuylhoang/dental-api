import { LockedFeature } from "@/components/dental/LockedFeature";
export default function Page() {
  return (
    <LockedFeature
      title="Treatment Plans"
      body="The treatment plans workspace is paused while we redesign the clinical model."
      backHref="/dashboard"
    />
  );
}
