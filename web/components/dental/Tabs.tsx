"use client";

import * as RadixTabs from "@radix-ui/react-tabs";

export interface Tab {
  key: string;
  label: string;
  count?: number;
}

export interface TabsProps {
  tabs: Tab[];
  active: string;
  onChange: (key: string) => void;
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <RadixTabs.Root value={active} onValueChange={onChange}>
      <RadixTabs.List className="flex border-b border-border">
        {tabs.map((tab) => (
          <RadixTabs.Trigger
            key={tab.key}
            value={tab.key}
            className={`px-4 py-2.5 text-sm whitespace-nowrap border-b-2 transition-colors outline-none cursor-pointer ${
              tab.key === active
                ? "border-foreground font-semibold text-foreground"
                : "border-transparent font-medium text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
            {tab.count != null && (
              <span className="ml-1.5 font-mono text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded-full font-semibold">
                {tab.count}
              </span>
            )}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
    </RadixTabs.Root>
  );
}
