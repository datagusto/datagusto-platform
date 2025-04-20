"use client";

import * as React from "react";
import {
  Bot,
  CheckCircle,
  XCircle,
  Layers,
  Code,
  AlertCircle,
  AlertTriangle,
  Brackets
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ObservationWithValidation } from "@/types/validation";

interface ObservationDialogProps {
  observation: ObservationWithValidation | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ObservationDialog({ observation, open, onOpenChange }: ObservationDialogProps) {
  if (!observation) {
    return null;
  }

  // Function to get appropriate icon for observation type
  const getObservationIcon = (type: string) => {
    switch (type) {
      case "USER_MESSAGE":
      case "USER_QUERY":
        return <Bot className="h-5 w-5" />;
      case "ASSISTANT_MESSAGE":
        return <Bot className="h-5 w-5" />;
      case "LLM_GENERATION":
        return <Brackets className="h-5 w-5" />;
      case "FUNCTION_CALL":
        return <Code className="h-5 w-5" />;
      case "DATABASE_QUERY":
        return <Layers className="h-5 w-5" />;
      case "EVENT":
        return <AlertTriangle className="h-5 w-5" />;
      default:
        return <Layers className="h-5 w-5" />;
    }
  };

  // Function to get appropriate color for log level
  const getLogLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "error":
        return "text-red-500";
      case "warn":
        return "text-amber-500";
      case "info":
        return "text-blue-500";
      case "debug":
        return "text-gray-500";
      default:
        return "text-gray-500";
    }
  };

  const qualityColor =
    observation.quality === "Poor"
      ? "text-red-500"
      : observation.quality === "Average"
        ? "text-amber-500"
        : "text-green-500";

  // Format input/output content for display
  const formatContent = (content: any) => {
    if (content === null) return "No content";
    if (typeof content === "string") return content;
    return JSON.stringify(content, null, 2);
  };

  // Check if this is an LLM observation that has system prompt
  const hasSystemPrompt =
    observation.type === "LLM_GENERATION" &&
    observation.metadata &&
    typeof observation.metadata.systemPrompt === "string";

  // Check if this is a tool that has tool code
  const hasToolCode =
    observation.type === "FUNCTION_CALL" &&
    observation.metadata &&
    typeof observation.metadata.toolCode === "string";

  // Format quality assessment explanation based on validation results
  const getQualityAssessmentExplanation = () => {
    if (observation.quality === "Poor") {
      const failedRules = observation.validationResults?.filter(r => !r.passed) || [];

      if (observation.level === "error" && observation.statusCode >= 500) {
        return (
          <>
            This observation has <span className="font-medium text-red-500">Poor</span> quality due to server errors
            (status code {observation.statusCode}) that critically affected the operation.
            {failedRules.some(r => r.ruleName === "Hallucination Check") &&
              " The LLM generated content contains potential hallucinations or factually incorrect information."}
            {failedRules.some(r => r.ruleName === "Response Coherence") &&
              " The response lacks logical coherence and consistency, making it unreliable for decision-making."}
            {failedRules.some(r => r.ruleName === "Data Quality Score") &&
              " The data quality is significantly compromised, affecting the reliability of analysis."}
            {failedRules.some(r => r.ruleName === "Response Time") &&
              " Response time exceeded acceptable thresholds, impacting user experience."}
          </>
        );
      }

      return (
        <>
          This observation has <span className="font-medium text-red-500">Poor</span> quality due to
          {failedRules.length > 0 ? (
            <>
              {' '}failed validation rules:
              <ul className="mt-1 ml-4 list-disc">
                {failedRules.map(rule => (
                  <li key={rule.ruleId}>
                    <span className="font-medium">{rule.ruleName}</span>: {rule.details}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            observation.level === "error" ? " errors reported in the execution" :
              " critical issues detected during processing"
          )}
        </>
      );
    } else if (observation.quality === "Average") {
      const suboptimalRules = observation.validationResults?.filter(r => r.score < 0.8 && r.score >= 0.6) || [];

      if (observation.level === "warn" || (observation.statusCode >= 400 && observation.statusCode < 500)) {
        return (
          <>
            This observation has <span className="font-medium text-amber-500">Average</span> quality due to warnings
            {observation.statusCode >= 400 && observation.statusCode < 500 ?
              ` and client errors (status code ${observation.statusCode})` :
              ""} that affected optimal performance.
            {suboptimalRules.some(r => r.ruleName === "Data Quality Score") &&
              " The data quality meets minimum requirements but lacks optimal structure or completeness."}
            {suboptimalRules.some(r => r.ruleName === "Response Time") &&
              " Response time is slower than recommended, but still within acceptable limits."}
            {suboptimalRules.some(r => r.ruleName === "Response Coherence") &&
              " The response maintains basic coherence but has some inconsistencies."}
          </>
        );
      }

      return (
        <>
          This observation has <span className="font-medium text-amber-500">Average</span> quality due to
          {suboptimalRules.length > 0 ? (
            <>
              {' '}validation rules scoring below optimal thresholds:
              <ul className="mt-1 ml-4 list-disc">
                {suboptimalRules.map(rule => (
                  <li key={rule.ruleId}>
                    <span className="font-medium">{rule.ruleName}</span> ({Math.round(rule.score * 100)}%): {rule.details}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            observation.level === "warn" ? " warnings reported during execution" :
              " some minor issues affecting optimal performance"
          )}
        </>
      );
    }

    return null;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-2">
            {getObservationIcon(observation.type)}
            <DialogTitle>{observation.name || 'Observation Details'}</DialogTitle>
            <Badge variant="outline" className="ml-2">
              {observation.type.replace(/_/g, " ")}
            </Badge>
          </div>
          <DialogDescription>
            Observation ID: <code className="text-xs bg-muted px-1 py-0.5 rounded">{observation.id}</code>
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-auto space-y-6 p-1">
          {/* Overview Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Overview</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Input</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-2 rounded-md text-xs overflow-auto max-h-[200px]">
                    {formatContent(observation.input)}
                  </pre>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Output</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-2 rounded-md text-xs overflow-auto max-h-[200px]">
                    {formatContent(observation.output)}
                  </pre>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-3 mt-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Duration</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">{observation.duration}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(observation.startTime).toLocaleTimeString()} - {new Date(observation.endTime).toLocaleTimeString()}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <span className={`text-xl font-bold ${getLogLevelColor(observation.level)}`}>
                      {observation.level.toUpperCase()}
                    </span>
                    {/* <Badge variant={observation.statusCode >= 400 ? "destructive" : "outline"}>
                      {observation.statusCode}
                    </Badge> */}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Quality</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    {observation.quality === "Good" ? (
                      <CheckCircle className={`h-5 w-5 ${qualityColor}`} />
                    ) : observation.quality === "Poor" ? (
                      <XCircle className={`h-5 w-5 ${qualityColor}`} />
                    ) : (
                      <AlertCircle className={`h-5 w-5 ${qualityColor}`} />
                    )}
                    <span className={`text-xl font-bold ${qualityColor}`}>{observation.quality}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Validation Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Validation</h3>
            <Card>
              <CardContent className="pt-6">
                {observation.validationResults && observation.validationResults.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Rule</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Details</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {observation.validationResults.map(result => (
                        <TableRow key={result.ruleId}>
                          <TableCell className="font-medium">{result.ruleName}</TableCell>
                          <TableCell>
                            {result.passed ? (
                              <span className="flex items-center text-green-500">
                                <CheckCircle className="h-4 w-4 mr-1" />
                                Pass
                              </span>
                            ) : (
                              <span className="flex items-center text-red-500">
                                <XCircle className="h-4 w-4 mr-1" />
                                Fail
                              </span>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className="h-2 w-16 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${result.score >= 0.8
                                      ? "bg-green-500"
                                      : result.score >= 0.6
                                        ? "bg-amber-500"
                                        : "bg-red-500"
                                    }`}
                                  style={{ width: `${result.score * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-xs">{(result.score * 100).toFixed(0)}%</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-sm">{result.details}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    No validation results available
                  </div>
                )}

                {observation.quality !== "Good" && (
                  <div className="mt-4 p-3 border rounded-md bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800">
                    <h4 className="font-medium mb-1">Quality Assessment</h4>
                    <p className="text-sm">
                      {getQualityAssessmentExplanation()}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Details Section */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Details</h3>
            <Card>
              <CardContent className="pt-6">
                <dl className="grid gap-3 sm:grid-cols-2">
                  {Object.entries(observation.metadata).map(([key, value]) => {
                    // Skip system prompt and tool code as they are displayed separately
                    if (key === "systemPrompt" || key === "toolCode") return null;

                    return (
                      <div key={key} className="space-y-1">
                        <dt className="text-sm font-medium text-muted-foreground capitalize">
                          {key.replace(/([A-Z])/g, ' $1').replace(/^./, function (str) { return str.toUpperCase(); })}
                        </dt>
                        <dd className="text-sm break-words">
                          {typeof value === "object"
                            ? JSON.stringify(value)
                            : value?.toString()}
                        </dd>
                      </div>
                    );
                  })}
                </dl>
              </CardContent>
            </Card>
          </div>

          {/* Code Section - Only shown if there's content */}
          {(hasSystemPrompt || hasToolCode) && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Code</h3>
              {hasSystemPrompt && (
                <Card>
                  <CardHeader>
                    <CardTitle>System Prompt</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-muted p-4 rounded-md text-xs overflow-auto whitespace-pre-wrap max-h-[300px]">
                      {observation.metadata.systemPrompt as string}
                    </pre>
                  </CardContent>
                </Card>
              )}

              {hasToolCode && (
                <Card className={hasSystemPrompt ? "mt-4" : ""}>
                  <CardHeader>
                    <CardTitle>Tool Code</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-muted p-4 rounded-md text-xs overflow-auto font-mono max-h-[300px]">
                      {observation.metadata.toolCode as string}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
} 