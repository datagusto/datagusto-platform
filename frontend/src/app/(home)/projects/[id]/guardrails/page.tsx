import React from "react";
import { GuardrailsClient } from "@/components/guardrails/guardrails-client";

interface GuardrailsPageProps {
  params: Promise<{ id: string }>;
}

export default function GuardrailsPage({ params }: GuardrailsPageProps) {
  const { id: projectId } = React.use(params);
  return <GuardrailsClient projectId={projectId} />;
}