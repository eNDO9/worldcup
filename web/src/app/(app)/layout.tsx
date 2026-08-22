import { TabBar } from "@/components/TabBar";

/** App shell: one scrolling screen plus the fixed bottom tab bar.
 * No sidebar — this is a phone-first layout that simply centers on
 * larger screens rather than growing a second navigation model. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh">
      {children}
      <TabBar />
    </div>
  );
}
