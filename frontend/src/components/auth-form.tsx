"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

export interface FormFieldConfig {
  name: string;
  label: string;
  type?: string;
  placeholder?: string;
}

interface AuthFormProps {
  schema: z.ZodSchema<any>;
  fields: FormFieldConfig[];
  onSubmit: (values: any) => Promise<void>;
  submitButtonText: string;
  loadingText: string;
  defaultValues?: Record<string, any>;
}

export function AuthForm({
  schema,
  fields,
  onSubmit,
  submitButtonText,
  loadingText,
  defaultValues = {},
}: AuthFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues,
  });

  async function handleSubmit(values: any) {
    setIsLoading(true);
    
    try {
      await onSubmit(values);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        {fields.map((field) => (
          <FormField
            key={field.name}
            control={form.control}
            name={field.name}
            render={({ field: formField }) => (
              <FormItem>
                <FormLabel>{field.label}</FormLabel>
                <FormControl>
                  <Input
                    type={field.type || "text"}
                    placeholder={field.placeholder}
                    {...formField}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        ))}
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {loadingText}
            </>
          ) : (
            submitButtonText
          )}
        </Button>
      </form>
    </Form>
  );
}