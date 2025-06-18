"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Search, Settings } from "lucide-react";
import { GuardrailPreset, GUARDRAIL_PRESETS, GUARDRAIL_CATEGORIES } from "@/types/guardrail-presets";
import { GuardrailFormData } from "@/types/guardrail";

interface GuardrailPresetSelectorProps {
  projectId: string;
  onSelectPreset: (preset: GuardrailPreset) => void;
  onCancel: () => void;
  onCustomCreate: () => void;
}

export function GuardrailPresetSelector({ 
  projectId, 
  onSelectPreset, 
  onCancel, 
  onCustomCreate 
}: GuardrailPresetSelectorProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredPresets = GUARDRAIL_PRESETS.filter(preset => {
    const matchesSearch = preset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         preset.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         preset.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesCategory = selectedCategory ? preset.category === selectedCategory : true;
    
    return matchesSearch && matchesCategory;
  });

  const categoryCounts = Object.keys(GUARDRAIL_CATEGORIES).reduce((acc, category) => {
    acc[category] = GUARDRAIL_PRESETS.filter(p => p.category === category).length;
    return acc;
  }, {} as Record<string, number>);

  const handlePresetSelect = (preset: GuardrailPreset) => {
    onSelectPreset(preset);
  };

  return (
    <div className="flex-1 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Choose a Guardrail</h1>
            <p className="text-gray-600">
              Select from pre-configured guardrails or create a custom one
            </p>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col lg:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search guardrails..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant={selectedCategory === null ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(null)}
            >
              All ({GUARDRAIL_PRESETS.length})
            </Button>
            {Object.entries(GUARDRAIL_CATEGORIES).map(([key, category]) => (
              <Button
                key={key}
                variant={selectedCategory === key ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(key)}
              >
                {category.name} ({categoryCounts[key]})
              </Button>
            ))}
          </div>
        </div>

        {/* Custom Create Option - Coming Soon */}
        <Card className="mb-6 border-dashed border-2 border-gray-300 opacity-60">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                  <Settings className="h-6 w-6 text-gray-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg text-gray-700">Custom Guardrail</h3>
                  <p className="text-gray-500">Create a fully customized guardrail with advanced settings</p>
                </div>
              </div>
              <Badge variant="secondary" className="bg-gray-100 text-gray-600">
                Coming Soon
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Preset Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPresets.map((preset) => (
            <Card 
              key={preset.id} 
              className="hover:shadow-lg transition-shadow cursor-pointer group"
              onClick={() => handlePresetSelect(preset)}
            >
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">{preset.icon}</div>
                    <div>
                      <CardTitle className="text-lg group-hover:text-blue-600 transition-colors">
                        {preset.name}
                      </CardTitle>
                      <Badge 
                        variant="secondary" 
                        className={GUARDRAIL_CATEGORIES[preset.category].color}
                      >
                        {GUARDRAIL_CATEGORIES[preset.category].name}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                  {preset.description}
                </p>
                
                {/* Tags */}
                <div className="flex flex-wrap gap-1 mb-4">
                  {preset.tags.map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>

                {/* Configuration Preview */}
                <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Trigger:</span>
                    <span className="font-medium">
                      {preset.formData.triggerType === 'always' ? 'Always' :
                       preset.formData.triggerType === 'specific_tool' ? `Tool: ${preset.formData.toolName}` :
                       'Regex Pattern'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Action:</span>
                    <span className="font-medium">
                      {preset.formData.actionType === 'filter_records' ? 'Filter Records' : 'Interrupt Agent'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredPresets.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <Search className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No guardrails found</h3>
            <p className="text-gray-600">
              Try adjusting your search terms or category filter
            </p>
          </div>
        )}
      </div>
    </div>
  );
}