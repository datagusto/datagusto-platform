/**
 * API Key list component
 *
 * @description Displays list of API keys for an agent.
 * Shows key prefix, name, expiration, and delete action.
 *
 * @module api-key-list
 */

'use client';

import { useState, useEffect } from 'react';
import { agentService } from '../services';
import { CreateAPIKeyDialog } from './create-api-key-dialog';
import type { AgentAPIKey, AgentAPIKeyCreateResponse } from '../types';
import type { CreateAPIKeyFormData } from '../schemas/api-key.schema';

/**
 * API Key list props
 */
interface APIKeyListProps {
  agentId: string;
}

/**
 * API Key list component
 *
 * @description Fetches and displays API keys with create/delete functionality.
 */
export function APIKeyList({ agentId }: APIKeyListProps) {
  const [apiKeys, setApiKeys] = useState<AgentAPIKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deletingKeyId, setDeletingKeyId] = useState<string | null>(null);

  // Fetch API keys
  useEffect(() => {
    let isMounted = true;

    async function fetchAPIKeys() {
      try {
        setIsLoading(true);
        setError(null);

        const response = await agentService.listAPIKeys(agentId);

        if (!isMounted) return;

        setApiKeys(response.items);
      } catch (err) {
        if (!isMounted) return;

        console.error('Failed to fetch API keys:', err);
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load API keys. Please try again.'
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchAPIKeys();

    return () => {
      isMounted = false;
    };
  }, [agentId]);

  // Handle create API key
  const handleCreateAPIKey = async (
    data: CreateAPIKeyFormData
  ): Promise<AgentAPIKeyCreateResponse> => {
    const result = await agentService.createAPIKey(agentId, data);
    // Refetch API keys
    const response = await agentService.listAPIKeys(agentId);
    setApiKeys(response.items);
    return result;
  };

  // Handle delete API key
  const handleDeleteAPIKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
      return;
    }

    try {
      setDeletingKeyId(keyId);
      await agentService.deleteAPIKey(agentId, keyId);
      // Refetch API keys
      const response = await agentService.listAPIKeys(agentId);
      setApiKeys(response.items);
    } catch (err) {
      console.error('Failed to delete API key:', err);
      alert(err instanceof Error ? err.message : 'Failed to delete API key');
    } finally {
      setDeletingKeyId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">API Keys</h3>
        <button
          onClick={() => setCreateDialogOpen(true)}
          className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors flex items-center gap-2"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Create API Key
        </button>
      </div>

      {/* API Keys List */}
      {apiKeys.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <svg
            className="w-12 h-12 text-gray-400 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
            />
          </svg>
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            No API keys
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Create an API key to start using this agent
          </p>
          <button
            onClick={() => setCreateDialogOpen(true)}
            className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors"
          >
            Create API Key
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Key
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Used
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expires
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {apiKeys.map((key) => (
                <tr key={key.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <code className="text-sm font-mono text-gray-900">
                      {key.key_prefix}...
                    </code>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {key.name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {key.last_used_at
                      ? new Date(key.last_used_at).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {key.is_expired ? (
                      <span className="text-red-600 font-medium">Expired</span>
                    ) : key.expires_at ? (
                      new Date(key.expires_at).toLocaleDateString()
                    ) : (
                      <span className="text-gray-500">Never</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => handleDeleteAPIKey(key.id)}
                      disabled={deletingKeyId === key.id}
                      className="text-red-600 hover:text-red-900 disabled:opacity-50"
                    >
                      {deletingKeyId === key.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create API Key Dialog */}
      <CreateAPIKeyDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        agentId={agentId}
        onCreateAPIKey={handleCreateAPIKey}
      />
    </div>
  );
}
