# API Client and Services Architecture

This directory contains the centralized API client and related utilities that provide a standardized way to interact with backend APIs throughout the application.

## API Client Architecture

The API client architecture follows these principles:

1. **Centralization**: All API requests go through a single, consistent client
2. **Standardization**: Common patterns like auth headers, error handling, and response parsing are handled uniformly
3. **Type Safety**: API requests and responses are strongly typed for better developer experience
4. **Mocking**: Support for mock implementations when backend services are not available

## Core Components

### `api-client.ts`

The core API client that provides:

- HTTP method helpers (`get`, `post`, `put`, `delete`, etc.)
- Automatic authorization header management
- Standardized error handling
- Mock data fallbacks for development
- Consistent response formatting

### Service Layer

Services are built on top of the API client, and they:

- Provide domain-specific API calls (agents, guardrails, auth, etc.)
- Handle domain-specific transformations and data needs
- Implement mock data capabilities for development and testing
- Encapsulate business logic for data manipulation

## Usage Guidelines

### Using the API Client Directly

```typescript
import { apiClient } from '@/lib/api-client';

// Making a GET request
const response = await apiClient.get<User[]>('/api/users');

// Making a POST request with data
const response = await apiClient.post<CreateUserResponse>(
  '/api/users',
  {
    name: 'John Doe',
    email: 'john@example.com'
  }
);

// Handling errors
if (response.error) {
  console.error(`Request failed: ${response.error}`);
}
```

### Using Services

```typescript
import { agentService } from '@/services';

// Get all agents
const agents = await agentService.getAgents();

// Create an agent
const newAgent = await agentService.createAgent({
  name: 'Customer Support Bot',
  description: 'Handles customer inquiries'
});
```

## Mock Data Handling

The API architecture includes support for mock data, which is used when:

1. The `NEXT_PUBLIC_API_URL` environment variable is not set
2. During development or testing

This allows the application to function without a working backend API.

## Adding New Services

To add a new service for a domain area:

1. Create a new file in `src/services/` (e.g., `my-domain-service.ts`)
2. Import and use the API client
3. Define the types for your domain data
4. Implement mock data handling if needed
5. Export your service and add it to `src/services/index.ts`

## Benefits

- **Maintainability**: Changes to API handling can be made in one place
- **Consistency**: Common patterns are applied consistently across the app
- **Testability**: Services can be mocked easily for testing
- **Developer Experience**: Type safety and standardized responses improve productivity 