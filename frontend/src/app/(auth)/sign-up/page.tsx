"use client";

import { z } from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { AuthCard } from "@/components/auth-card";
import { AuthForm, type FormFieldConfig } from "@/components/auth-form";
import type { RegisterData } from "@/types/auth";
import { useAuth } from "@/lib/auth-context";

const signUpSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters" }),
  email: z.string().email({ message: "Please enter a valid email address" }),
  password: z.string().min(8, { message: "Password must be at least 8 characters" }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

const signUpFields: FormFieldConfig[] = [
  {
    name: "name",
    label: "Full Name",
    placeholder: "John Doe",
  },
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
  {
    name: "confirmPassword",
    label: "Confirm Password",
    type: "password",
    placeholder: "••••••••",
  },
];

export default function SignUp() {
  const router = useRouter();
  const { register } = useAuth();

  async function handleSubmit(values: z.infer<typeof signUpSchema>) {
    try {
      await register({
        name: values.name,
        email: values.email,
        password: values.password,
      });

      toast.success("Account created successfully");
      router.push("/sign-in");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "An error occurred during registration"
      );
    }
  }

  const footer = (
    <p className="text-sm text-gray-500">
      Already have an account?{" "}
      <Link href="/sign-in" className="font-medium text-primary hover:underline">
        Sign in
      </Link>
    </p>
  );

  return (
    <AuthCard
      title="Create an Account"
      description="Enter your details to create a new account"
      footer={footer}
    >
      <AuthForm
        schema={signUpSchema}
        fields={signUpFields}
        onSubmit={handleSubmit}
        submitButtonText="Create Account"
        loadingText="Creating Account..."
        defaultValues={{
          name: "",
          email: "",
          password: "",
          confirmPassword: "",
        }}
      />
    </AuthCard>
  );
} 