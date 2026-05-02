import { Button } from './button';
import { Input } from './input';
import { Card, CardHeader, CardTitle, CardContent } from './card';
import { Badge } from './badge';
import { Skeleton } from './skeleton';
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle } from './dialog';
import { Command, CommandInput, CommandList, CommandItem } from './command';

const sections: { title: string; render: () => React.ReactNode }[] = [
  {
    title: 'Button variants',
    render: () => (
      <div className="flex flex-wrap gap-2">
        {(['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'] as const).map(v => (
          <Button key={v} variant={v}>{v}</Button>
        ))}
      </div>
    ),
  },
  {
    title: 'Button sizes',
    render: () => (
      <div className="flex flex-wrap items-center gap-2">
        {(['sm', 'default', 'lg'] as const).map(s => (
          <Button key={s} size={s}>{s}</Button>
        ))}
      </div>
    ),
  },
  {
    title: 'Input',
    render: () => <Input placeholder="Type something…" className="max-w-xs" />,
  },
  {
    title: 'Card',
    render: () => (
      <Card className="max-w-xs">
        <CardHeader><CardTitle>Card title</CardTitle></CardHeader>
        <CardContent>Card content goes here.</CardContent>
      </Card>
    ),
  },
  {
    title: 'Badge variants',
    render: () => (
      <div className="flex flex-wrap gap-2">
        {(['default', 'secondary', 'destructive', 'outline', 'success', 'warning'] as const).map(v => (
          <Badge key={v} variant={v}>{v}</Badge>
        ))}
      </div>
    ),
  },
  {
    title: 'Skeleton',
    render: () => (
      <div className="space-y-2">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-32" />
      </div>
    ),
  },
  {
    title: 'Dialog',
    render: () => (
      <Dialog>
        <DialogTrigger asChild><Button variant="outline">Open dialog</Button></DialogTrigger>
        <DialogContent>
          <DialogHeader><DialogTitle>Dialog title</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Dialog body content.</p>
        </DialogContent>
      </Dialog>
    ),
  },
  {
    title: 'Command',
    render: () => (
      <Command className="rounded-lg border shadow-md max-w-xs">
        <CommandInput placeholder="Search…" />
        <CommandList>
          <CommandItem>Item one</CommandItem>
          <CommandItem>Item two</CommandItem>
        </CommandList>
      </Command>
    ),
  },
];

import React from 'react';

export default function UIShowcase() {
  return (
    <div className="p-8 space-y-10">
      <h1 className="text-3xl font-bold">UI Component Showcase</h1>
      {sections.map(({ title, render }) => (
        <section key={title}>
          <h2 className="text-lg font-semibold mb-3 text-muted-foreground">{title}</h2>
          {render()}
        </section>
      ))}
    </div>
  );
}
