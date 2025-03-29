"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Bot, ArrowLeft, Check } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { agentService } from "@/services/agent-service";

export default function NewAgentPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [formData, setFormData] = useState({
    name: "",
    type: "",
    status: "ACTIVE" as "ACTIVE" | "INACTIVE",
  });
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (step === 1) {
      setStep(2);
    } else if (step === 2) {
      setStep(3);
      setIsLoading(true);
      setError(null);
      
      try {
        await agentService.createAgent({
          name: formData.name,
          description: `${formData.type} Agent`,
          config: { 
            type: formData.type,
            status: formData.status
          }
        });
        
        setSuccess(true);
        
        // Success message display and redirect
        setTimeout(() => {
          router.push("/agents");
        }, 1500);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create agent");
        setSuccess(false);
      } finally {
        setIsLoading(false);
      }
    }
  };
  
  // Available agent types
  const agentTypes = ["General"];
  
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="icon" asChild>
          <Link href="/agents">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">Add New Agent</h1>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>
            {step === 1 && "Agent Details"}
            {step === 2 && "Confirm Agent Details"}
            {step === 3 && (success ? "Agent Created" : "Creating Agent...")}
          </CardTitle>
          <CardDescription>
            {step === 1 && "Enter the information for your new AI agent"}
            {step === 2 && "Please review the agent details before creating"}
            {step === 3 && (success 
              ? "Your agent has been successfully created" 
              : "Setting up your new agent...")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === 1 && (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Agent Name</Label>
                <Input 
                  id="name" 
                  placeholder="e.g. Customer Support Bot" 
                  value={formData.name}
                  onChange={(e) => handleChange("name", e.target.value)}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="type">Agent Type</Label>
                <Select 
                  value={formData.type} 
                  onValueChange={(value) => handleChange("type", value)}
                  required
                >
                  <SelectTrigger id="type">
                    <SelectValue placeholder="Select agent type" />
                  </SelectTrigger>
                  <SelectContent>
                    {agentTypes.map((type: string) => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="status">Initial Status</Label>
                <Select 
                  value={formData.status} 
                  onValueChange={(value) => handleChange("status", value as "ACTIVE" | "INACTIVE")}
                >
                  <SelectTrigger id="status">
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ACTIVE">Active</SelectItem>
                    <SelectItem value="INACTIVE">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Button type="submit" className="w-full">
                Continue
              </Button>
            </form>
          )}
          
          {step === 2 && (
            <div className="space-y-6">
              <div className="rounded-md border p-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Bot className="h-8 w-8 text-primary" />
                  <div>
                    <h3 className="font-semibold">{formData.name}</h3>
                    <p className="text-sm text-muted-foreground">{formData.type}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">Status</p>
                    <p>{formData.status === "ACTIVE" ? "Active" : "Inactive"}</p>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button onClick={handleSubmit}>
                  Create Agent
                </Button>
              </div>
            </div>
          )}
          
          {step === 3 && isLoading && !success && (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="animate-pulse flex flex-col items-center space-y-4">
                <Bot className="h-16 w-16 text-primary" />
                <p>Creating your agent...</p>
              </div>
            </div>
          )}
          
          {step === 3 && error && (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="rounded-full bg-red-100 p-3">
                  <Bot className="h-8 w-8 text-red-600" />
                </div>
                <h3 className="text-xl font-medium">Failed to Create Agent</h3>
                <p className="text-muted-foreground">{error}</p>
                <Button variant="outline" onClick={() => setStep(2)}>
                  Back
                </Button>
              </div>
            </div>
          )}
          
          {step === 3 && success && (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="rounded-full bg-green-100 p-3">
                  <Check className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="text-xl font-medium">Agent Created Successfully</h3>
                <p className="text-muted-foreground">
                  Your new agent "{formData.name}" has been created and is ready to use.
                </p>
                <p className="text-sm text-muted-foreground">
                  Redirecting to agents list...
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 