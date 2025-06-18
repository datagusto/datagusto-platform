"use client";

import { z } from "zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Suspense } from "react";

import { AuthCard } from "@/components/auth-card";
import { AuthForm, type FormFieldConfig } from "@/components/auth-form";
import type { LoginCredentials } from "@/types/auth";
import { useAuth } from "@/lib/auth-context";

const signInSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address" }),
  password: z.string().min(8, { message: "Password must be at least 8 characters" }),
});

const signInFields: FormFieldConfig[] = [
  {
    name: "email",
    label: "Email",
    type: "email",
    placeholder: "your.email@example.com",
  },
  {
    name: "password",
    label: "Password",
    type: "password",
    placeholder: "••••••••",
  },
];

function SignInContent() {
  const router = useRouter();
  const { login } = useAuth();

  async function handleSubmit(values: z.infer<typeof signInSchema>) {
    try {
      await login(values as LoginCredentials);
      toast.success("Signed in successfully");
      router.push("/home");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "An error occurred during sign in"
      );
    }
  }

  const footer = (
    <p className="text-sm text-gray-500">
      Don't have an account?{" "}
      <Link href="/sign-up" className="font-medium text-primary hover:underline">
        Sign up
      </Link>
    </p>
  );

  return (
    <AuthCard
      title="Sign In"
      description="Enter your credentials to access your account"
      footer={footer}
    >
      <AuthForm
        schema={signInSchema}
        fields={signInFields}
        onSubmit={handleSubmit}
        submitButtonText="Sign In"
        loadingText="Signing in..."
        defaultValues={{
          email: "",
          password: "",
        }}
      />
    </AuthCard>
  );
}

export default function SignIn() {
  return (
    <Suspense>
      <SignInContent />
    </Suspense>
  );
} 