# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🔨 Most Important Rule - Process for Adding New Rules

When receiving instructions from users that seem to require constant response rather than just one-time handling:

1. Ask "Should this be made a standard rule?"
2. If you get a YES response, record it as an additional rule in CLAUDE.md
3. From then on, always apply it as a standard rule

Through this process, we will continuously improve the project rules.

## Project Overview

datagusto is a **Data Quality Layer for AI agent systems** that ensures reliable data access and processing. The platform connects with observability platforms like Langfuse to monitor AI agent data interactions, measure data quality, and provide automated guardrails to prevent data-related failures.

## Core Product Features

### 1. Observability Platform Integration
- **Langfuse Integration**: Connects to Langfuse and other observation platforms to sync AI agent logs
- **Real-time Data Sync**: Continuously monitors AI agent execution traces and data access patterns
- **Multi-platform Support**: Extensible architecture for connecting to various observability tools

### 2. Data Quality Measurement
- **Automated Quality Assessment**: Analyzes data accessed by AI agents during tool calling and processing
- **Quality Metrics**: Measures completeness, accuracy, consistency, and validity of agent data
- **Historical Tracking**: Monitors data quality trends over time to identify degradation patterns

### 3. Data Quality Analysis
- **Quality Scoring**: Automated calculation of data quality scores for traces
- **Trend Monitoring**: Historical tracking of data quality patterns over time
- **Quality Insights**: Detailed analysis of data completeness, accuracy, and consistency

### 5. Data Guardrails SDK
- **Custom Guardrail Creation**: SDK for implementing data validation rules in AI agent systems
- **Null Handling**: Automatically exclude or handle null values in tool calling responses
- **Data Filtering**: Remove problematic records or fields before processing
- **Execution Control**: Option to halt agent execution when critical data quality thresholds are violated
- **Runtime Protection**: Real-time data validation during AI agent execution

## Tech Stack

- **Frontend**: Next.js (App Router + Server Components), TypeScript, shadcn/ui, TanStack Query, React Context API
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Alembic, Simple JWT auth, REST API, Lightweight async
- **Database**: PostgreSQL
- **Development**: Docker Compose
- **Production**: VM + Docker Compose
- **CI/CD**: Manual deployment (no automation)
- **Monitoring**: Docker standard logs only
- **Testing**: Strategic testing with pytest (backend) and Vitest (frontend), 70% coverage target

## Frontend Development Guidelines

### Next.js App Router + Server Components Strategy

This project follows strict guidelines for optimal Next.js App Router implementation to ensure maximum performance and maintainability.

#### Server Components vs Client Components

| Feature | Server Component | Client Component |
|---------|------------------|------------------|
| Declaration | Default (no declaration needed) | `"use client"` at file top |
| Execution | Server | Browser |
| JS Bundle | Not included ✅ | Included ❌ |
| Data Access | Direct DB access ✅ | Not possible ❌ |
| React Hooks | Not available ❌ | Available ✅ |
| Event Handlers | Not available ❌ | Available ✅ |

#### Mandatory Rules for Component Implementation

**Rule 1: Server Components by Default**
- All components MUST be Server Components unless interactivity is required
- Only use `"use client"` when absolutely necessary for React Hooks, event handlers, or browser APIs

**Rule 2: Client Components at Leaf Nodes Only**
- Place Client Components as deep as possible in the component tree
- Keep parent components as Server Components to minimize bundle size

**Rule 3: Data Fetching in Server Components**
- Perform all API requests and external data fetching in Server Components
- Pass only necessary, serializable data to Client Components

**Rule 4: Minimize Server-to-Client Data Transfer**
- Extract only essential data before passing to Client Components
- Avoid passing large objects, functions, or non-serializable data

**Rule 5: Use Server Actions for Form Handling**
- Prefer Server Actions over client-side state management for form submissions
- Implement data mutations on the server side when possible

**Rule 6: Implement Suspense for Progressive Loading**
- Use Suspense boundaries for better user experience
- Show loading states for slow-loading content sections

### Directory Structure

#### Feature-based Organization with Server/Client Separation

```
src/
├── app/                      # Next.js App Router
│   ├── (auth)/              # Authentication route group
│   └── (dashboard)/         # Dashboard route group
├── features/                 # Feature modules
│   ├── projects/
│   │   ├── components/      # Feature-specific components
│   │   │   ├── project-list.tsx        # Server Component (default)
│   │   │   └── project-actions.tsx     # Client Component ("use client")
│   │   ├── hooks/          # Custom hooks
│   │   ├── api/            # API related functions
│   │   └── types/          # Type definitions
│   └── traces/
├── components/              # Shared components
│   ├── ui/                 # shadcn/ui components
│   └── common/            # Other shared components
└── lib/                    # Utilities and configurations
```

#### Naming Conventions
- **Server Components**: Default, no special suffix
- **Client Components**: Consider `.client.tsx` suffix or clear "use client" directive
- **Files**: kebab-case (e.g., `project-card.tsx`)
- **Components**: PascalCase (e.g., `ProjectCard`)

### State Management

#### TanStack Query for Server State
```typescript
// features/projects/api/use-projects.ts
export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.get<Project[]>('/projects'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Mutations
export function useCreateProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateProjectData) => 
      apiClient.post<Project>('/projects', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}
```

#### Zustand for Client State
```typescript
// stores/ui-store.ts
import { create } from 'zustand';

interface UIStore {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  selectedProjectId: string | null;
  setSelectedProject: (id: string | null) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  selectedProjectId: null,
  setSelectedProject: (id) => set({ selectedProjectId: id }),
}));
```

### API Communication

#### Unified API Client
```typescript
// lib/api-client.ts
export class ApiClient {
  private baseURL: string;
  
  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  
  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${path}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options?.headers,
      },
    });
    
    if (!response.ok) {
      throw new ApiError(response.statusText, response.status);
    }
    
    return response.json();
  }
  
  async get<T>(path: string, options?: RequestInit): Promise<T> {
    return this.request<T>(path, { ...options, method: 'GET' });
  }
  
  async post<T>(path: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  // Similar methods for PUT, PATCH, DELETE
}

export const apiClient = new ApiClient();
```

### Styling with Tailwind CSS and shadcn/ui

#### Class Variance Authority (CVA) for Component Variants
```typescript
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  // Base styles
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}
```

#### Tailwind Class Organization
```typescript
// Organize classes in logical groups
<div className={cn(
  // Layout
  "flex flex-col gap-4",
  // Sizing
  "w-full max-w-md",
  // Spacing
  "p-6",
  // Colors & Borders
  "bg-background border rounded-lg",
  // Effects
  "shadow-sm",
  // Responsive
  "md:flex-row md:gap-6",
  // Interactive states
  "hover:shadow-md transition-shadow",
  // Conditional classes
  isActive && "ring-2 ring-primary",
  className // Allow override
)} />
```

#### Dark Mode Guidelines
- Use CSS variables for colors: `bg-background`, `text-foreground`
- Avoid hardcoded colors: ~~`bg-white dark:bg-gray-900`~~
- Let shadcn/ui handle theme switching

### Form Handling

#### Complex Forms with React Hook Form + Zod
```typescript
// schemas/project.ts
import { z } from "zod";

export const projectSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().optional(),
  settings: z.object({
    public: z.boolean(),
    notifications: z.boolean(),
  }),
});

export type ProjectFormData = z.infer<typeof projectSchema>;

// components/project-form.tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

export function ProjectForm({ onSubmit }: Props) {
  const form = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      settings: {
        public: true,
        notifications: true,
      },
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Project Name</FormLabel>
              <FormControl>
                <Input placeholder="My Project" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Creating..." : "Create Project"}
        </Button>
      </form>
    </Form>
  );
}
```

#### Simple Forms with Server Actions
```typescript
// app/actions/auth.ts
"use server";

import { redirect } from "next/navigation";
import { z } from "zod";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

export async function loginAction(formData: FormData) {
  const validatedData = loginSchema.parse({
    email: formData.get("email"),
    password: formData.get("password"),
  });

  const result = await authenticateUser(validatedData);
  
  if (result.success) {
    redirect("/dashboard");
  }
  
  return { error: "Invalid credentials" };
}

// components/login-form.tsx (no "use client" needed!)
export function LoginForm() {
  return (
    <form action={loginAction} className="space-y-4">
      <input
        name="email"
        type="email"
        required
        className="input"
        placeholder="Email"
      />
      <input
        name="password"
        type="password"
        required
        className="input"
        placeholder="Password"
      />
      <button type="submit" className="btn-primary">
        Sign In
      </button>
    </form>
  );
}
```

### Error Handling

#### Error Types and Boundaries
```typescript
// lib/errors.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// app/error.tsx
"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
      <p className="text-muted-foreground mb-4">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}

// components/error-boundary.tsx
"use client";

import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <ErrorFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}
```

#### API Error Handling with TanStack Query
```typescript
// lib/query-client.ts
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error instanceof ApiError) {
          // Don't retry on 4xx errors
          if (error.status && error.status >= 400 && error.status < 500) {
            return false;
          }
        }
        return failureCount < 3;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      onError: (error) => {
        if (error instanceof ApiError) {
          switch (error.status) {
            case 401:
              // Handle unauthorized
              router.push("/login");
              break;
            case 403:
              toast.error("Access denied");
              break;
            default:
              toast.error(error.message || "An error occurred");
          }
        }
      },
    },
  },
});
```

### TypeScript Configuration

#### Strict TypeScript Settings
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

#### Type Definition Guidelines
```typescript
// 1. Use interface for object shapes
interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}

// 2. Use type for unions, intersections, and utilities
type UserRole = "admin" | "user" | "guest";
type PartialUser = Partial<User>;
type UserWithProfile = User & { profile: Profile };

// 3. Generic types for reusable components
interface ApiResponse<T> {
  data: T;
  error?: string;
  timestamp: Date;
}

// 4. Const assertions for literal types
const STATUSES = ["pending", "active", "archived"] as const;
type Status = typeof STATUSES[number];

// 5. Discriminated unions for state
type LoadingState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: Error };

// 6. Utility types usage
type ReadonlyUser = Readonly<User>;
type UserKeys = keyof User;
type PickedUser = Pick<User, "id" | "name">;

// 7. Component props
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

// 8. Environment variables
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      NEXT_PUBLIC_API_URL: string;
      NEXT_PUBLIC_API_VERSION: string;
    }
  }
}
```

### Testing Strategy

#### Test Setup with Vitest
```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});

// src/test/setup.ts
import "@testing-library/jest-dom";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
```

#### Testing Priorities
1. **Critical Business Logic**
   ```typescript
   // utils/calculations.test.ts
   describe("calculateDataQualityScore", () => {
     it("should return 100 for perfect data", () => {
       const score = calculateDataQualityScore({
         nullCount: 0,
         totalCount: 100,
         errors: [],
       });
       expect(score).toBe(100);
     });
   });
   ```

2. **Authentication Flows**
   ```typescript
   // features/auth/auth.test.tsx
   describe("LoginForm", () => {
     it("should redirect on successful login", async () => {
       const user = userEvent.setup();
       render(<LoginForm />);
       
       await user.type(screen.getByLabelText("Email"), "test@example.com");
       await user.type(screen.getByLabelText("Password"), "password123");
       await user.click(screen.getByRole("button", { name: "Sign In" }));
       
       await waitFor(() => {
         expect(mockRouter.push).toHaveBeenCalledWith("/dashboard");
       });
     });
   });
   ```

3. **Form Validation**
   ```typescript
   // features/projects/components/project-form.test.tsx
   describe("ProjectForm", () => {
     it("should show validation errors", async () => {
       render(<ProjectForm onSubmit={vi.fn()} />);
       
       fireEvent.submit(screen.getByRole("form"));
       
       await waitFor(() => {
         expect(screen.getByText("Name is required")).toBeInTheDocument();
       });
     });
   });
   ```

#### What NOT to Test
- UI appearance/styling
- External library behavior
- Simple prop passing
- Generated types

### Performance Optimization

#### Next.js Built-in Optimizations
```typescript
// 1. Image optimization
import Image from "next/image";

export function OptimizedImage({ src, alt }: Props) {
  return (
    <Image
      src={src}
      alt={alt}
      width={400}
      height={300}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      priority={false} // Only for above-the-fold images
      placeholder="blur" // With blurDataURL for static images
      className="rounded-lg"
    />
  );
}

// 2. Font optimization
import { Inter, Roboto_Mono } from "next/font/google";

export const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const robotoMono = Roboto_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-roboto-mono",
});

// 3. Dynamic imports for code splitting
import dynamic from "next/dynamic";

const HeavyChart = dynamic(() => import("@/components/heavy-chart"), {
  loading: () => <ChartSkeleton />,
  ssr: false, // Disable SSR for client-only components
});

// 4. Parallel data fetching in Server Components
export default async function DashboardPage() {
  // These run in parallel
  const [projects, traces, incidents] = await Promise.all([
    getProjects(),
    getRecentTraces(),
    getActiveIncidents(),
  ]);

  return <Dashboard data={{ projects, traces, incidents }} />;
}

// 5. Streaming with Suspense
export default function TracesPage() {
  return (
    <div className="space-y-6">
      <TraceHeader />
      <Suspense fallback={<TableSkeleton />}>
        <TraceTable />
      </Suspense>
    </div>
  );
}

// 6. Memoization for expensive computations
const ExpensiveComponent = memo(
  function ExpensiveComponent({ data }: Props) {
    const processedData = useMemo(() => 
      expensiveProcessing(data), [data]
    );
    
    return <div>{/* render processed data */}</div>;
  },
  (prevProps, nextProps) => {
    // Custom comparison
    return prevProps.data.id === nextProps.data.id;
  }
);
```

#### Bundle Size Optimization
```bash
# Add bundle analyzer
npm install --save-dev @next/bundle-analyzer

# next.config.js
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

module.exports = withBundleAnalyzer({
  // your config
});

# Run analysis
ANALYZE=true npm run build
```

## Architecture

### Backend Architecture (FastAPI)

The backend follows layered architecture:
1. **API Layer** (`app/api/`): HTTP endpoints and routing
2. **Service Layer** (`app/services/`): Business logic and core functionality
3. **Repository Layer** (`app/repositories/`): Data access abstraction
4. **Model Layer** (`app/models/`, `app/schemas/`): Data models and validation

Key integrations:
- **Langfuse**: AI agent trace data collection and analysis
- **OpenAI**: Root cause analysis for data quality incidents
- **PostgreSQL**: Primary database for application data
- **Simple JWT**: Lightweight authentication without external dependencies
- **Guardrails SDK**: Custom SDK for implementing data quality controls

### Frontend Architecture (Next.js)

- **App Router**: Next.js with Server Components and CSR (Client-Side Rendering)
- **Authentication**: Simple JWT-based authentication
- **UI Components**: shadcn/ui components with Radix UI primitives
- **State Management**: Zustand for lightweight global state management
- **Styling**: Tailwind CSS with custom component variants

## Development Commands

### Full Stack Development
```bash
# Start all services (recommended for development)
docker compose up

# Start specific services
docker compose up backend
docker compose up frontend
docker compose up postgres
```

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Install dependencies (requires Python 3.10+)
uv install

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Generate new migration
uv run alembic revision --autogenerate -m "description"
```

### Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linting
npm run lint
```

## Environment Configuration

### Backend Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `JWT_REFRESH_SECRET_KEY`: Secret key for refresh token generation
- `ENABLE_REGISTRATION`: Boolean to enable/disable user registration
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration time (default: 30)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration time (default: 7)

### Frontend Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_API_VERSION`: API version (default: v1)

## Key Features and Flows

### Data Quality Monitoring Flow
1. **Project Setup**: User creates account, organization, and project configuration
2. **Platform Connection**: Project includes Langfuse credentials (public_key, secret_key, host)
3. **Data Sync**: Platform continuously syncs trace data and observations from Langfuse
4. **Quality Analysis**: System calculates quality scores and analyzes data patterns
5. **Quality Monitoring**: Dashboard provides real-time quality metrics and trend analysis
6. **Guardrail Configuration**: Define data quality rules and validation strategies
7. **Guardrail Activation**: SDK-based guardrails automatically filter and validate data

### SDK Integration Flow
1. **SDK Installation**: Developers integrate the datagusto SDK into their AI agent systems
2. **Guardrail Configuration**: Define data quality rules and handling strategies
3. **Runtime Monitoring**: SDK monitors data quality during tool calling and processing
4. **Automatic Remediation**: Configured guardrails automatically filter, clean, or halt processing based on data quality

### Data Models
- **User**: User account and authentication management
- **Organization**: Multi-tenant organization management with member roles
- **Project**: AI agent configuration and observability platform connections
- **Trace**: Individual AI agent execution traces with quality scores
- **Observation**: Detailed trace observations and data points
- **Guardrail**: Data quality rules and validation strategies
- **AuditLog**: System activity and change tracking

### Testing Strategy

#### Test Priorities
**High Priority (Must Test):**
- Data quality calculation logic - Core business functionality
- Langfuse API integration - External service reliability
- Authentication and authorization - Security critical
- Trace analysis algorithms - Main feature

**Medium Priority (Should Test):**
- Important API endpoints - User-facing functionality
- Database operations - Data integrity
- Input validation - Data consistency

**Low Priority (Don't Test):**
- Simple CRUD operations - Framework functionality
- Configuration loading - Library functionality
- Thin wrapper functions - Minimal business logic

#### Test Tools and Setup
```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio httpx factory-boy freezegun pytest-mock coverage

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test types
uv run pytest tests/unit/        # Unit tests only
uv run pytest tests/integration/ # Integration tests only
```

#### Test Configuration
```ini
# pytest.ini
[tool:pytest]
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
    --asyncio-mode=auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

[tool.coverage.run]
omit = 
    app/main.py
    app/core/config.py
    app/models/__init__.py
    */migrations/*
    */tests/*
```

#### Database Testing
```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/test_datagusto"

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    async with test_engine.begin() as conn:
        async_session = sessionmaker(conn, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session
            # Transaction automatically rolled back

@pytest.fixture
async def test_client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
```

#### Test Data Factories
```python
# tests/factories.py
import factory
from factory import Faker, SubFactory
from app.models import User, Project, Trace

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    name = Faker('name')
    email = Faker('email')
    organization_id = factory.LazyFunction(lambda: str(uuid4()))

class ProjectFactory(factory.Factory):
    class Meta:
        model = Project
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    name = Faker('company')
    description = Faker('text', max_nb_chars=200)
    organization_id = factory.LazyFunction(lambda: str(uuid4()))

class TraceFactory(factory.Factory):
    class Meta:
        model = Trace
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    project_id = factory.LazyFunction(lambda: str(uuid4()))
    data = factory.LazyFunction(lambda: {
        "completion_tokens": 100,
        "prompt_tokens": 50,
        "total_tokens": 150
    })
    quality_score = Faker('pyfloat', min_value=0, max_value=100)

# Usage examples
def test_analyze_trace():
    trace = TraceFactory.build()  # In-memory only (fast)
    # or
    trace = TraceFactory.create()  # Save to DB (integration test)
```

#### Mock Strategy
```python
from unittest.mock import Mock, AsyncMock, patch
import pytest

# External API mocking (always mock)
@pytest.mark.asyncio
async def test_sync_traces_from_langfuse():
    mock_langfuse = Mock()
    mock_langfuse.get_traces = AsyncMock(return_value=[
        {"id": "trace_1", "data": "test"}
    ])
    
    service = TraceService(langfuse_client=mock_langfuse)
    result = await service.sync_traces("project_id")
    
    assert len(result.new_traces) == 1
    mock_langfuse.get_traces.assert_called_once()

# Time-dependent function testing
from freezegun import freeze_time

@freeze_time("2024-01-01")
async def test_time_dependent_function():
    result = await function_that_uses_current_time()
    assert result.timestamp == datetime(2024, 1, 1)

# Repository mocking (for service tests)
@pytest.mark.asyncio
async def test_service_with_mocked_repo():
    mock_repo = Mock()
    mock_repo.get_by_id = AsyncMock(return_value=TraceFactory.build())
    
    service = DataQualityService(quality_repo=mock_repo)
    result = await service.analyze_quality("trace_id", mock_db)
    
    assert result.score >= 0
```

#### Test Examples
```python
# Unit test example - Business logic
@pytest.mark.asyncio
async def test_calculate_data_quality_score():
    trace_data = {
        "total_fields": 100,
        "null_fields": 10,
        "invalid_fields": 5
    }
    
    score = calculate_data_quality_score(trace_data)
    
    assert score == 85  # (100 - 10 - 5) / 100 * 100

# Integration test example - API endpoint
@pytest.mark.asyncio
async def test_create_project_endpoint(test_client: AsyncClient):
    project_data = {
        "name": "Test Project",
        "description": "Test description"
    }
    
    response = await test_client.post("/api/v1/projects", json=project_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert "id" in data

# Service test example - External API integration
@pytest.mark.asyncio
async def test_langfuse_integration():
    mock_client = Mock()
    mock_client.get_traces = AsyncMock(return_value=[
        {"id": "1", "status": "completed"},
        {"id": "2", "status": "failed"}
    ])
    
    service = LangfuseService(client=mock_client)
    traces = await service.fetch_recent_traces("project_id")
    
    assert len(traces) == 2
    assert traces[0]["status"] == "completed"
```

#### Coverage Goals
**Phase 1 (Current):** 50% - Focus on critical business logic
**Phase 2 (6 months):** 70% - Cover main API endpoints and services  
**Phase 3 (1 year):** 80% - Comprehensive coverage for stable operation

#### Test Organization
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_data_quality_service.py
│   │   ├── test_trace_service.py
│   │   └── test_langfuse_service.py
│   ├── repositories/
│   │   └── test_trace_repository.py
│   └── utils/
│       └── test_calculations.py
├── integration/
│   ├── api/
│   │   ├── test_auth_endpoints.py
│   │   ├── test_project_endpoints.py
│   │   └── test_trace_endpoints.py
│   └── database/
│       └── test_migrations.py
├── factories.py
└── conftest.py
```

## Database Migrations

### Alembic Configuration
- Uses Alembic for database schema management
- Migration files in `backend/alembic/versions/`
- Create migration: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`

## API Structure

### Current Endpoints
- `/api/v1/auth/*`: Authentication and user management endpoints
- `/api/v1/organizations/*`: Organization management and member operations
- `/api/v1/projects/*`: Project management and observability platform connections
- `/api/v1/traces/*`: Trace data synchronization and quality analysis
- `/api/v1/guardrails/*`: Guardrail configuration and management

### API Versioning
- All endpoints prefixed with `/api/v1`
- Versioned router structure supports future API versions

## Deployment & Operations

### Development
- Docker Compose for local development environment
- Hot reload enabled for both frontend and backend

### Production
- VM deployment with Docker Compose
- Manual deployment process (no CI/CD automation)
- Docker standard logs for monitoring
- No advanced monitoring or observability tools

## Backend Development Guidelines (FastAPI)

### Code Organization and Architecture

#### Layered Architecture
The backend strictly follows a layered architecture pattern:

```
app/
├── api/         # API Layer - HTTP endpoints, request/response handling
├── services/    # Service Layer - Business logic, orchestration
├── repositories/# Repository Layer - Data access abstraction
├── models/      # SQLAlchemy models - Database schema
├── schemas/     # Pydantic models - Request/response validation
└── core/        # Core utilities - Config, security, dependencies
```

**Rules:**
- Each layer should only depend on layers below it
- API layer calls Service layer, never Repository directly
- Service layer orchestrates business logic and calls Repository layer
- Repository layer handles all database operations

#### File Naming Conventions
- Use snake_case for all Python files and modules
- Suffix files with their layer type: `_service.py`, `_repository.py`, `_schema.py`
- Group related functionality in the same file

### API Design Standards

#### RESTful Endpoints
```python
# Good
@router.get("/agents/{agent_id}")  # Get single resource
@router.get("/agents")             # List resources
@router.post("/agents")            # Create resource
@router.put("/agents/{agent_id}")  # Update entire resource
@router.patch("/agents/{agent_id}") # Partial update
@router.delete("/agents/{agent_id}") # Delete resource

# Bad
@router.get("/get_agent/{agent_id}")  # Don't use verbs in URLs
@router.post("/agents/create")        # The HTTP method already indicates action
```

#### Async-First Approach
All endpoints and service methods MUST be async unless there's a specific reason:
```python
# Standard approach - use async
@router.get("/projects/{project_id}")
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    project_repo: ProjectRepository = Depends(get_project_repository)
) -> ProjectResponse:
    project = await project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

### Error Handling

#### Simple HTTPException Usage
Use FastAPI's built-in HTTPException for error handling:
```python
from fastapi import HTTPException

# Resource not found
if not project:
    raise HTTPException(status_code=404, detail="Project not found")

# Validation error
if len(name) < 3:
    raise HTTPException(status_code=422, detail="Name must be at least 3 characters")

# Unauthorized
if not user.is_active:
    raise HTTPException(status_code=401, detail="User account is disabled")

# Forbidden
if project.organization_id != current_user.organization_id:
    raise HTTPException(status_code=403, detail="Access denied")
```

### Service Layer Patterns

#### Service with Dependency Injection
Services use dependency injection pattern consistent with repositories:
```python
class TraceService:
    def __init__(
        self,
        trace_repo: TraceRepository,
        quality_repo: QualityRepository,
        langfuse_client: LangfuseClient
    ):
        self.trace_repo = trace_repo
        self.quality_repo = quality_repo
        self.langfuse_client = langfuse_client
    
    async def sync_traces(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> SyncResult:
        """Sync traces from Langfuse for a project"""
        # Business logic using self.trace_repo, self.langfuse_client
        pass
    
    async def analyze_quality(
        self,
        trace_id: UUID,
        db: AsyncSession
    ) -> QualityAnalysis:
        """Analyze data quality for a trace"""
        # Business logic using self.quality_repo
        pass

# Dependency injection setup
def get_trace_service(
    trace_repo: TraceRepository = Depends(get_trace_repository),
    quality_repo: QualityRepository = Depends(get_quality_repository),
    langfuse_client: LangfuseClient = Depends(get_langfuse_client)
) -> TraceService:
    return TraceService(trace_repo, quality_repo, langfuse_client)
```

#### Transaction Management
Handle transactions at the service layer:
```python
async def create_incident_with_analysis(
    incident_data: IncidentCreate,
    db: AsyncSession
) -> Incident:
    async with db.begin():  # Transaction boundary
        incident = await incident_repo.create(incident_data)
        analysis = await analysis_service.create_initial_analysis(incident.id)
        # If any operation fails, entire transaction rolls back
    return incident
```

### Repository Layer Patterns

#### Base Repository Pattern
Use a base repository for common operations:
```python
from typing import Generic, TypeVar, Optional, List, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        db.add(instance)
        await db.flush()  # Flush to get ID without committing
        return instance
    
    async def update(self, db: AsyncSession, instance: ModelType, **kwargs) -> ModelType:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await db.flush()
        return instance
```

#### Repository Implementation
```python
class ProjectRepository(BaseRepository[Project]):
    def __init__(self):
        super().__init__(Project)
    
    async def get_by_organization(
        self, 
        db: AsyncSession, 
        org_id: UUID
    ) -> List[Project]:
        stmt = select(self.model).where(
            self.model.organization_id == org_id
        ).order_by(self.model.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()
```

### Database Models and Schemas

#### Model Naming and Structure
```python
# app/models/project.py
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Project(BaseModel):
    __tablename__ = "projects"
    
    # Use descriptive column names
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    agents = relationship("Agent", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_project_org_id", "organization_id"),
    )
```

#### Pydantic Schema Patterns
```python
# app/schemas/project.py
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

class ProjectWithStats(ProjectResponse):
    agent_count: int = 0
    active_incidents: int = 0
    last_sync_at: Optional[datetime] = None
```

### Dependency Injection

#### Database Session Management
```python
# app/core/database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### Repository Injection
```python
# app/core/dependencies.py
def get_project_repository() -> ProjectRepository:
    return ProjectRepository()

def get_trace_repository() -> TraceRepository:
    return TraceRepository()

# Usage in endpoint
@router.get("/projects/{project_id}")
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    project_repo: ProjectRepository = Depends(get_project_repository)
):
    return await project_repo.get_by_id(db, project_id)
```

### Authentication and Authorization

#### JWT Token Handling
```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await user_repo.get_by_id(db, UUID(user_id))
    if user is None:
        raise credentials_exception
    return user
```

#### Permission Checking
```python
async def verify_project_access(
    project_id: UUID,
    current_user: User,
    project_repo: ProjectRepository,
    db: AsyncSession,
    required_role: Optional[str] = None
) -> Project:
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has access to the project's organization
    if project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Additional role-based checks if needed
    if required_role:
        # Implement role checking logic
        pass
    
    return project
```

### Logging

#### Simple Logging
Use Python's standard logging module with simple messages:
```python
import logging

logger = logging.getLogger(__name__)

# Simple informational messages
logger.info(f"Trace sync started for project {project_id}")
logger.info(f"Synced {new_count} new traces in {duration_ms}ms")

# Warning messages
logger.warning(f"Rate limit approaching for Langfuse API")

# Error messages with exception info
try:
    result = await external_api_call()
except Exception as e:
    logger.error(f"Failed to call external API: {str(e)}", exc_info=True)
```

### Testing Standards

#### Test Organization
```
tests/
├── unit/
│   ├── services/
│   ├── repositories/
│   └── utils/
├── integration/
│   ├── api/
│   └── database/
└── conftest.py  # Shared fixtures
```

#### Test Patterns
```python
# tests/unit/services/test_trace_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.trace_service import TraceService

@pytest.mark.asyncio
async def test_analyze_quality_success():
    # Arrange
    mock_repo = Mock()
    mock_repo.get_by_id = AsyncMock(return_value=mock_trace)
    
    # Act
    result = await TraceService.analyze_quality(
        trace_id=trace_id,
        db=mock_db,
        quality_repo=mock_repo
    )
    
    # Assert
    assert result.quality_score >= 0
    assert result.quality_score <= 100
    mock_repo.get_by_id.assert_called_once_with(mock_db, trace_id)
```

### Performance Optimization

#### Query Optimization
```python
# Use eager loading for related data
stmt = select(Project).options(
    selectinload(Project.agents),
    selectinload(Project.incidents)
).where(Project.organization_id == org_id)

# Use pagination for large datasets
async def get_traces_paginated(
    db: AsyncSession,
    project_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Trace]:
    stmt = select(Trace).where(
        Trace.project_id == project_id
    ).offset(skip).limit(limit).order_by(Trace.created_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()
```


### Code Quality Standards

#### Type Hints
Always use type hints for function parameters and return values:
```python
from typing import List, Optional, Dict, Any
from uuid import UUID

async def process_traces(
    project_id: UUID,
    trace_ids: List[UUID],
    options: Optional[Dict[str, Any]] = None
) -> Dict[UUID, TraceResult]:
    pass
```

#### Docstrings
Use clear, concise docstrings in English:
```python
async def analyze_data_quality(
    trace_id: UUID,
    db: AsyncSession
) -> QualityAnalysis:
    """
    Analyze data quality for a specific trace.
    
    Evaluates completeness, accuracy, consistency, and validity
    of data accessed during trace execution.
    
    Args:
        trace_id: The UUID of the trace to analyze
        db: Database session
    
    Returns:
        QualityAnalysis object containing scores and issues
    
    Raises:
        HTTPException: If trace does not exist or analysis fails
    """
    pass
```

#### Comments
All comments must be in English:
```python
# Good - English comments
# Check if the trace exists before processing
if not trace:
    raise HTTPException(status_code=404, detail="Trace not found")

# Bad - avoid non-English comments
# トレースの存在確認
```

### Environment Variables

#### Configuration Management
Use pydantic-settings for type-safe environment variable management:
```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Required settings
    database_url: str
    jwt_secret_key: str
    
    # Optional settings with defaults
    enable_registration: bool = True
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # External service configurations
    openai_api_key: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Database Migrations

#### Migration Naming Convention
Use descriptive names starting with a verb:
```bash
# Good examples
alembic revision --autogenerate -m "create_users_table"
alembic revision --autogenerate -m "add_organization_id_to_projects"
alembic revision --autogenerate -m "update_trace_indexes_for_performance"
alembic revision --autogenerate -m "remove_deprecated_status_column"

# Bad examples
alembic revision --autogenerate -m "users"  # Not descriptive
alembic revision --autogenerate -m "fix"    # Too vague
```

### Background Tasks

#### Using arq for Async Task Processing
For background tasks that require reliability and scalability:
```python
# app/core/tasks.py
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings

async def startup_task_pool():
    return await create_pool(
        RedisSettings(host=settings.redis_host, port=settings.redis_port)
    )

# app/tasks/trace_analysis.py
async def analyze_trace_quality(ctx, trace_id: str):
    """Background task to analyze trace data quality"""
    async with get_db() as db:
        trace_service = ctx['trace_service']
        await trace_service.analyze_quality(trace_id, db)

# Usage in API endpoint
@router.post("/traces/{trace_id}/analyze")
async def trigger_analysis(
    trace_id: UUID,
    task_pool: ArqRedis = Depends(get_task_pool)
):
    job = await task_pool.enqueue_job(
        'analyze_trace_quality',
        str(trace_id)
    )
    return {"job_id": job.job_id, "status": "queued"}
```

### API Versioning

Simple versioning strategy:
- All endpoints use `/api/v1` prefix
- Breaking changes require new version (`/api/v2`)
- No complex versioning rules

## Important Notes

- Simple, lightweight architecture focused on data quality monitoring
- Manual deployment workflow - no automated CI/CD pipeline
- Strategic testing approach with 70% coverage target
- Uses JWT with refresh tokens for authentication (no external auth providers)
- Docker standard logging - no advanced monitoring setup
- **Primary Focus**: Data quality measurement and prevention for AI agents
- **SDK-First Approach**: Provides both monitoring platform and runtime protection SDK
- **Extensible Platform Support**: Currently supports Langfuse with architecture for additional platforms
- **Real-time Guardrails**: Proactive data quality protection during AI agent execution

## Git Commit Message Rules

### IMPORTANT: Never include Claude Code information in commits
- **NEVER** include "🤖 Generated with [Claude Code]" in commit messages
- **NEVER** include "Co-Authored-By: Claude" in commit messages
- **NEVER** mention AI assistance or code generation tools in commits
- Keep commit messages focused on the changes made, not how they were made

### Commit Message Format
Follow conventional commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

Example:
```
fix: improve data quality analysis performance

- Deferred analysis until after trace commit
- Batch analyze traces for better performance
- Fixed UI alignment issues
```