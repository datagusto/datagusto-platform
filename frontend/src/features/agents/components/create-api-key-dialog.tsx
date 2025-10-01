/**
 * Create API key dialog component
 *
 * @description Dialog for creating a new API key.
 * Shows the full API key once after creation with copy functionality.
 *
 * @module create-api-key-dialog
 */

'use client';

import { useState } from 'react';
import { CreateAPIKeyForm } from './create-api-key-form';
import type { CreateAPIKeyFormData } from '../schemas/api-key.schema';
import type { AgentAPIKeyCreateResponse } from '../types';

/**
 * Create API key dialog props
 */
interface CreateAPIKeyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  onCreateAPIKey: (data: CreateAPIKeyFormData) => Promise<AgentAPIKeyCreateResponse>;
}

/**
 * Create API key dialog component
 *
 * @description Two-step dialog:
 * 1. Form to create API key
 * 2. Display created key with copy button (shown only once)
 */
export function CreateAPIKeyDialog({
  open,
  onOpenChange,
  agentId,
  onCreateAPIKey,
}: CreateAPIKeyDialogProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [createdKey, setCreatedKey] = useState<AgentAPIKeyCreateResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (data: CreateAPIKeyFormData) => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await onCreateAPIKey(data);
      setCreatedKey(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to create API key'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    if (createdKey?.api_key) {
      await navigator.clipboard.writeText(createdKey.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onOpenChange(false);
      // Reset state after animation
      setTimeout(() => {
        setCreatedKey(null);
        setError(null);
        setCopied(false);
      }, 300);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div
          className="bg-white rounded-lg shadow-xl max-w-md w-full p-6"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              {createdKey ? 'API Key Created' : 'Create API Key'}
            </h2>
            <p className="mt-1 text-sm text-gray-600">
              {createdKey
                ? 'Copy your API key now. It will not be shown again.'
                : 'Create a new API key for this agent'}
            </p>
          </div>

          {/* Content */}
          {createdKey ? (
            <div className="space-y-4">
              {/* Warning */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex">
                  <svg
                    className="w-5 h-5 text-yellow-600 mr-2"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                  <div>
                    <h4 className="text-sm font-medium text-yellow-800">
                      Store this key securely
                    </h4>
                    <p className="text-xs text-yellow-700 mt-1">
                      This is the only time you will see the full key
                    </p>
                  </div>
                </div>
              </div>

              {/* API Key Display */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  API Key
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    readOnly
                    value={createdKey.api_key}
                    className="flex-1 border rounded-md px-3 py-2 font-mono text-sm bg-gray-50"
                  />
                  <button
                    onClick={handleCopy}
                    className="px-4 py-2 bg-gray-100 text-gray-900 rounded-md hover:bg-gray-200 transition-colors"
                  >
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              </div>

              {/* Key Info */}
              <div className="text-sm text-gray-600">
                <p>
                  <span className="font-medium">Prefix:</span> {createdKey.key_prefix}
                </p>
                {createdKey.name && (
                  <p>
                    <span className="font-medium">Name:</span> {createdKey.name}
                  </p>
                )}
                {createdKey.expires_at && (
                  <p>
                    <span className="font-medium">Expires:</span>{' '}
                    {new Date(createdKey.expires_at).toLocaleDateString()}
                  </p>
                )}
              </div>

              {/* Done Button */}
              <button
                onClick={handleClose}
                className="w-full px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors"
              >
                Done
              </button>
            </div>
          ) : (
            <>
              {/* Form */}
              <CreateAPIKeyForm
                onSubmit={handleSubmit}
                isLoading={isLoading}
                error={error}
              />

              {/* Cancel Button */}
              <button
                type="button"
                onClick={handleClose}
                disabled={isLoading}
                className="mt-3 w-full px-4 py-2 text-sm text-gray-700 hover:text-gray-900 disabled:opacity-60"
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>
    </>
  );
}
