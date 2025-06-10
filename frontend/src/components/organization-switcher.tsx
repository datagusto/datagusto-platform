"use client";

import { useState } from "react";
import { ChevronDown, Check, Building2 } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";

export function OrganizationSwitcher() {
  const { organizations, currentOrganization, setCurrentOrganization } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  if (organizations.length === 0 || !currentOrganization) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-gray-500">
        <Building2 className="h-4 w-4" />
        <span className="text-sm">No organizations</span>
      </div>
    );
  }

  const handleSelect = (orgId: string) => {
    const selectedOrg = organizations.find(o => o.organization.id === orgId)?.organization;
    if (selectedOrg) {
      setCurrentOrganization(selectedOrg);
      setIsOpen(false);
    }
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full justify-between px-3 py-2 h-auto text-left font-normal"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Building2 className="h-4 w-4 flex-shrink-0" />
          <div className="min-w-0">
            <div className="text-sm font-medium truncate">
              {currentOrganization.name}
            </div>
            <div className="text-xs text-gray-500 truncate">
              {organizations.find(o => o.organization.id === currentOrganization.id)?.membership.role}
            </div>
          </div>
        </div>
        <ChevronDown className="h-4 w-4 flex-shrink-0" />
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 max-h-64 overflow-y-auto">
            {organizations.map(({ organization, membership }) => (
              <button
                key={organization.id}
                onClick={() => handleSelect(organization.id)}
                className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-md flex-shrink-0">
                  {organization.avatar_url ? (
                    <img 
                      src={organization.avatar_url} 
                      alt={organization.name}
                      className="w-full h-full object-cover rounded-md"
                    />
                  ) : (
                    <Building2 className="h-4 w-4 text-gray-600" />
                  )}
                </div>
                
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate">
                    {organization.name}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {membership.role}
                  </div>
                </div>
                
                {currentOrganization.id === organization.id && (
                  <Check className="h-4 w-4 text-blue-600 flex-shrink-0" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}