import { TracesClient } from "@/components/traces/traces-client";

interface TracesPageProps {
  params: Promise<{ id: string }>;
}

export default async function TracesPage({ params }: TracesPageProps) {
  const { id } = await params;
  return <TracesClient projectId={id} />;
}