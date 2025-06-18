"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { projectService } from "@/services";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import type { ProjectCreateData } from "@/types";

interface CreateProjectModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectCreated?: (project: any) => void;
}

interface FormData {
  name: string;
  description: string;
  platform_type: string;
  langfuse_public_key: string;
  langfuse_secret_key: string;
  langfuse_url: string;
}

const PLATFORM_OPTIONS = [
  { value: "langfuse", label: "Langfuse", description: "Open source LLM engineering platform" },
];

export function CreateProjectModal({ open, onOpenChange, onProjectCreated }: CreateProjectModalProps) {
  const { currentOrganization } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<FormData>({
    defaultValues: {
      name: "",
      description: "",
      platform_type: "langfuse",
      langfuse_public_key: "",
      langfuse_secret_key: "",
      langfuse_url: "https://cloud.langfuse.com",
    },
  });

  const selectedPlatform = form.watch("platform_type");

  const onSubmit = async (data: FormData) => {
    if (!currentOrganization) return;

    setIsSubmitting(true);
    try {
      // Build platform config for Langfuse
      const platform_config = {
        public_key: data.langfuse_public_key,
        secret_key: data.langfuse_secret_key,
        url: data.langfuse_url,
      };

      const projectData: ProjectCreateData = {
        name: data.name,
        description: data.description || undefined,
        organization_id: currentOrganization.id,
        platform_type: data.platform_type,
        platform_config,
      };

      const newProject = await projectService.createProject(projectData);

      // Reset form and close modal
      form.reset();
      onOpenChange(false);
      onProjectCreated?.(newProject);
    } catch (error) {
      console.error('Failed to create project:', error);
      // TODO: Add proper error handling/toast
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderPlatformConfig = () => {
    return (
      <div className="space-y-4">
        <FormField
          control={form.control}
          name="langfuse_public_key"
          rules={{
            required: "Public key is required",
            pattern: {
              value: /^pk-/,
              message: "Public key must start with 'pk_'"
            }
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Public Key</FormLabel>
              <FormControl>
                <Input placeholder="pk-..." {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="langfuse_secret_key"
          rules={{
            required: "Secret key is required",
            pattern: {
              value: /^sk-/,
              message: "Secret key must start with 'sk-'"
            }
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Secret Key</FormLabel>
              <FormControl>
                <Input type="password" placeholder="sk-..." {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="langfuse_url"
          rules={{
            required: "URL is required",
            pattern: {
              value: /^https?:\/\/.+/,
              message: "Please enter a valid URL starting with http:// or https://"
            }
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Langfuse URL</FormLabel>
              <FormControl>
                <Input placeholder="https://cloud.langfuse.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Set up a new AI agent project with data quality monitoring.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                rules={{
                  required: "Project name is required",
                  minLength: {
                    value: 2,
                    message: "Project name must be at least 2 characters"
                  },
                  maxLength: {
                    value: 50,
                    message: "Project name must be less than 50 characters"
                  }
                }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Project Name</FormLabel>
                    <FormControl>
                      <Input placeholder="My AI Agent Project" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                rules={{
                  maxLength: {
                    value: 200,
                    message: "Description must be less than 200 characters"
                  }
                }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description (Optional)</FormLabel>
                    <FormControl>
                      <Input placeholder="Brief description of your project" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="platform_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Observation Platform</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a platform" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {PLATFORM_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="border-t pt-4">
              <Label className="text-base font-medium">Platform Configuration</Label>
              <p className="text-sm text-gray-600 mb-4">
                Configure connection to your observation platform for AI agent monitoring.
              </p>
              {renderPlatformConfig()}
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Project
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}