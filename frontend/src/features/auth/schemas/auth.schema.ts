/**
 * Authentication validation schemas
 *
 * @description Zod validation schemas for authentication forms and API requests.
 * These schemas provide type-safe validation with user-friendly error messages.
 *
 * **Architecture**:
 * - Base schema first (registerDataSchema) for API requests
 * - Derived schemas (signUpSchema) extend base with additional fields
 * - Use .extend() before .refine() to maintain type safety
 *
 * **Features**:
 * - Client-side form validation with react-hook-form
 * - Type inference for TypeScript (eliminates duplicate type definitions)
 * - Internationalization-ready error messages
 * - Reusable across components
 *
 * @module auth.schema
 */

import { z } from 'zod';

/**
 * Sign-in form validation schema
 *
 * @description Validates user login credentials (email and password).
 * Used by the sign-in form to ensure data quality before API submission.
 *
 * **Validation Rules**:
 * - **email**: Must be a valid email format (RFC 5322 compliant)
 * - **password**: Must be at least 8 characters (matches backend requirement)
 *
 * **Error Messages**:
 * - User-friendly messages displayed in the UI
 * - Can be internationalized by replacing message strings
 *
 * @example
 * ```typescript
 * import { useForm } from 'react-hook-form';
 * import { zodResolver } from '@hookform/resolvers/zod';
 * import { signInSchema, type SignInFormData } from './auth.schema';
 *
 * function SignInForm() {
 *   const { register, handleSubmit, formState: { errors } } = useForm<SignInFormData>({
 *     resolver: zodResolver(signInSchema),
 *   });
 *
 *   const onSubmit = (data: SignInFormData) => {
 *     console.log(data); // { email: string, password: string }
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit(onSubmit)}>
 *       <input {...register('email')} />
 *       {errors.email && <span>{errors.email.message}</span>}
 *
 *       <input type="password" {...register('password')} />
 *       {errors.password && <span>{errors.password.message}</span>}
 *     </form>
 *   );
 * }
 * ```
 *
 * @example
 * ```typescript
 * // Manual validation (outside forms)
 * const result = signInSchema.safeParse({
 *   email: 'user@example.com',
 *   password: 'password123',
 * });
 *
 * if (result.success) {
 *   console.log('Valid:', result.data);
 * } else {
 *   console.error('Invalid:', result.error.errors);
 * }
 * ```
 */
export const signInSchema = z.object({
  /**
   * User's email address
   *
   * @validation Must be valid email format (e.g., user@example.com)
   * @errorMessage "Please enter a valid email address"
   */
  email: z.string().email({
    message: 'Please enter a valid email address',
  }),

  /**
   * User's password
   *
   * @validation Minimum 8 characters (matches backend password policy)
   * @errorMessage "Password must be at least 8 characters"
   *
   * @note Frontend only validates length. Backend performs additional checks:
   * - Password complexity (uppercase, lowercase, numbers, symbols)
   * - Common password detection
   * - Breach database check
   */
  password: z.string().min(8, {
    message: 'Password must be at least 8 characters',
  }),
});

/**
 * Sign-in form data type
 *
 * @description TypeScript type inferred from signInSchema.
 * Use this type for form values and API requests.
 *
 * @typedef {Object} SignInFormData
 * @property {string} email - User's email address
 * @property {string} password - User's password
 *
 * @example
 * ```typescript
 * const handleLogin = async (data: SignInFormData) => {
 *   const response = await authService.login(data);
 * };
 * ```
 */
export type SignInFormData = z.infer<typeof signInSchema>;

/**
 * Registration data schema (BASE SCHEMA)
 *
 * @description Base schema for user registration API requests.
 * This is the foundational schema from which form schemas are derived.
 *
 * **Design Pattern**: Base-First Approach
 * - Define this schema first (represents API payload)
 * - Derive form schemas using .extend() and .refine()
 * - Ensures DRY principle and type consistency
 *
 * **Validation Rules**:
 * - **name**: Minimum 2 characters (allows international names)
 * - **email**: Must be valid email format
 * - **password**: Minimum 8 characters
 *
 * **Usage**:
 * Use this schema for:
 * - API request validation
 * - Type inference for API payloads
 * - Base for deriving form schemas
 *
 * @example
 * ```typescript
 * // Validate API payload before submission
 * const registrationData = registerDataSchema.parse({
 *   name: 'John Doe',
 *   email: 'john@example.com',
 *   password: 'password123',
 * });
 *
 * await authService.register(registrationData);
 * ```
 *
 * @example
 * ```typescript
 * // Use as base for derived schemas
 * const extendedSchema = registerDataSchema.extend({
 *   additionalField: z.string(),
 * });
 * ```
 */
export const registerDataSchema = z.object({
  /**
   * User's full name or display name
   *
   * @validation Minimum 2 characters (supports short international names)
   * @errorMessage "Name must be at least 2 characters"
   *
   * @note Allows unicode characters for international names
   * @example "李明", "José", "Владимир", "A B" are all valid
   */
  name: z.string().min(2, {
    message: 'Name must be at least 2 characters',
  }),

  /**
   * User's email address (must be unique in system)
   *
   * @validation Must be valid email format
   * @errorMessage "Please enter a valid email address"
   *
   * @note Backend will validate email uniqueness and may reject if already registered
   */
  email: z.string().email({
    message: 'Please enter a valid email address',
  }),

  /**
   * User's chosen password
   *
   * @validation Minimum 8 characters
   * @errorMessage "Password must be at least 8 characters"
   *
   * @note Backend enforces stronger password policies (complexity, breaches, etc.)
   */
  password: z.string().min(8, {
    message: 'Password must be at least 8 characters',
  }),
});

/**
 * Registration data type (for API submission)
 *
 * @description Type for registration API payload.
 * This matches the RegisterData interface from auth.types.ts.
 *
 * @typedef {Object} RegisterData
 * @property {string} name - User's display name
 * @property {string} email - User's email address
 * @property {string} password - User's password
 *
 * @example
 * ```typescript
 * const userData: RegisterData = {
 *   name: 'John Doe',
 *   email: 'john@example.com',
 *   password: 'securePassword123',
 * };
 * await authService.register(userData);
 * ```
 */
export type RegisterData = z.infer<typeof registerDataSchema>;

/**
 * Sign-up form validation schema (DERIVED SCHEMA)
 *
 * @description Validates new user registration form including password confirmation.
 * Derived from registerDataSchema using .extend() and .refine().
 *
 * **Design Pattern**: Extend Base Schema
 * - Extends registerDataSchema with confirmPassword field
 * - Uses .refine() for cross-field validation (password matching)
 * - Maintains type consistency with base schema
 *
 * **Validation Rules**:
 * - Inherits: name, email, password from registerDataSchema
 * - Adds: confirmPassword field
 * - Custom validation: passwords must match
 *
 * **Why This Design?**:
 * - ✅ Avoids code duplication
 * - ✅ Maintains single source of truth (base schema)
 * - ✅ Type-safe derivation
 * - ✅ Easy to maintain and update
 *
 * @example
 * ```typescript
 * import { useForm } from 'react-hook-form';
 * import { zodResolver } from '@hookform/resolvers/zod';
 * import { signUpSchema, type SignUpFormData } from './auth.schema';
 *
 * function SignUpForm() {
 *   const { register, handleSubmit, formState: { errors } } = useForm<SignUpFormData>({
 *     resolver: zodResolver(signUpSchema),
 *   });
 *
 *   const onSubmit = (data: SignUpFormData) => {
 *     // confirmPassword is only for validation, exclude it before API call
 *     const { confirmPassword, ...registrationData } = data;
 *     console.log(registrationData); // { name, email, password }
 *   };
 *
 *   return <form onSubmit={handleSubmit(onSubmit)}>...</form>;
 * }
 * ```
 *
 * @example
 * ```typescript
 * // Validation will fail if passwords don't match
 * const result = signUpSchema.safeParse({
 *   name: 'John Doe',
 *   email: 'john@example.com',
 *   password: 'password123',
 *   confirmPassword: 'differentPassword', // ❌ Doesn't match
 * });
 *
 * console.log(result.success); // false
 * console.log(result.error.errors[0].message); // "Passwords don't match"
 * ```
 */
export const signUpSchema = registerDataSchema
  /**
   * Step 1: Extend base schema with additional form field
   *
   * @description Adds confirmPassword field to base registration schema.
   * This field is used only for client-side validation and won't be sent to API.
   */
  .extend({
    /**
     * Password confirmation field
     *
     * @validation Must match the password field exactly (checked by .refine())
     * @errorMessage "Passwords don't match" (from .refine() validation below)
     *
     * @note This field is only for client-side validation and should not be sent to API
     */
    confirmPassword: z.string(),
  })
  /**
   * Step 2: Add custom cross-field validation
   *
   * @description Ensures password and confirmPassword match.
   * Zod's .refine() method allows custom validation logic across multiple fields.
   *
   * @param data - Form data object containing all fields
   * @returns boolean - true if passwords match, false otherwise
   *
   * **Error Configuration**:
   * - message: Error message shown to user
   * - path: Which field should display the error (confirmPassword)
   *
   * **Why .refine() at the end?**:
   * - .refine() converts ZodObject to ZodEffects
   * - ZodEffects doesn't support .omit(), .pick(), etc.
   * - By applying .refine() last, we keep type manipulation methods available during schema construction
   */
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'], // Error will appear on confirmPassword field
  });

/**
 * Sign-up form data type
 *
 * @description TypeScript type inferred from signUpSchema.
 * Includes all form fields including confirmPassword.
 *
 * @typedef {Object} SignUpFormData
 * @property {string} name - User's display name
 * @property {string} email - User's email address
 * @property {string} password - User's chosen password
 * @property {string} confirmPassword - Password confirmation (validation only)
 *
 * @note When submitting to API, exclude confirmPassword:
 * @example
 * ```typescript
 * const handleRegister = async (data: SignUpFormData) => {
 *   // Remove confirmPassword before sending to API
 *   const { confirmPassword, ...registrationData } = data;
 *   await authService.register(registrationData);
 * };
 * ```
 */
export type SignUpFormData = z.infer<typeof signUpSchema>;
