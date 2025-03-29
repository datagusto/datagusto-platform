// 初期ガードレールデータ
const initialGuardrails = [
//   {
//     id: 1,
//     name: "Anti-Hallucination Guardrail",
//     validation: "Hallucination Check",
//     condition: "Score < 0.7",
//     action: "Regenerate Response",
//     status: "Active",
//     description: "Checks if output contains hallucinations and regenerates the response if detected"
//   },
//   {
//     id: 2,
//     name: "Data Completeness Check",
//     validation: "Data Quality Score",
//     condition: "Completeness < 0.5",
//     action: "Ask User for Confirmation",
//     status: "Active",
//     description: "Verifies completeness of tool output data and asks user for confirmation if below threshold"
//   },
  {
    id: 3,
    name: "Content Safety Filter",
    validation: "Toxic Content Detection",
    condition: "Contains Toxic Content",
    action: "Stop Processing",
    status: "Active",
    description: "Detects toxic content in outputs and stops processing, directing to support"
  },
//   {
//     id: 4,
//     name: "Human Support Escalation",
//     validation: "Hallucination Check",
//     condition: "Score < 0.5",
//     action: "Connect to Human Support",
//     status: "Active",
//     description: "When critical hallucinations are detected in agent responses, automatically connects the user to human customer support"
//   }
];

export type Guardrail = {
  id: number;
  name: string;
  validation: string;
  condition: string;
  action: string;
  status: string;
  description: string;
};

// ガードレールデータを取得
export const getGuardrails = (): Guardrail[] => {
  return initialGuardrails;
};

// 新しいガードレールを追加
export const addGuardrail = (guardrail: Omit<Guardrail, "id">): Guardrail => {
  const newGuardrail: Guardrail = {
    id: initialGuardrails.length > 0 ? Math.max(...initialGuardrails.map(g => g.id)) + 1 : 1,
    ...guardrail
  };
  
  // 新しいガードレールを配列に追加
  initialGuardrails.push(newGuardrail);
  
  return newGuardrail;
};

// 事前定義されたガードレールのアクション
export const guardrailActions = [
  { id: 1, name: "Regenerate Response", description: "Force the agent to regenerate its response" },
  { id: 2, name: "Ask User for Confirmation", description: "Prompt the user to confirm whether to proceed" },
  { id: 3, name: "Stop Processing", description: "Halt agent processing and direct to support" },
  { id: 4, name: "Log and Continue", description: "Log the violation but allow agent to continue" },
  { id: 5, name: "Connect to Human Support", description: "Transfer the conversation to a human customer support agent" }
]; 