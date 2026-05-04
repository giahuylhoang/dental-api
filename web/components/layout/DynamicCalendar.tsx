"use client";
import dynamic from "next/dynamic";
export const FullCalendar = dynamic(() => import("@fullcalendar/react"), { ssr: false });
