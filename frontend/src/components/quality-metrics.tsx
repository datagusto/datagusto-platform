import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { QualityIssue } from '@/types';

interface QualityMetricsProps {
  observationId: string;
  qualityIssues: QualityIssue[];
}

interface QualityMetricRowProps {
  criteria: string;
  description: string;
  status: 'Incident' | 'Compliant';
  details: string;
}

function QualityMetricRow({ criteria, description, status, details }: QualityMetricRowProps) {
  return (
    <div className="grid grid-cols-3 gap-4 py-3 border-b border-gray-100 last:border-b-0 items-center">
      <div className="flex flex-col justify-center">
        <div className="font-medium text-sm text-gray-900">{criteria}</div>
        <div className="text-xs text-gray-500 mt-1">{description}</div>
      </div>
      <div className="flex items-center">
        <Badge 
          variant={status === 'Compliant' ? 'default' : 'destructive'}
          className={
            status === 'Compliant' 
              ? 'bg-green-100 text-green-800 hover:bg-green-100' 
              : 'bg-red-100 text-red-800 hover:bg-red-100'
          }
        >
          {status}
        </Badge>
      </div>
      <div className="text-sm text-gray-700">
        {status === 'Incident' ? (
          <ul className="list-disc list-inside space-y-1">
            {details.split('•').filter(Boolean).map((detail, index) => (
              <li key={index} className="text-sm">
                {detail.trim()}
              </li>
            ))}
          </ul>
        ) : (
          <span>{details}</span>
        )}
      </div>
    </div>
  );
}

export function QualityMetrics({ observationId, qualityIssues }: QualityMetricsProps) {
  // Filter issues for this specific observation
  if (process.env.NODE_ENV === 'development') {
    console.log(`QualityMetrics: Looking for observationId: ${observationId}`);
    console.log('Available quality issues:', qualityIssues);
  }
  
  const observationIssues = qualityIssues.filter(issue => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`Filtering issue: ${issue.observation_id} === ${observationId} ? ${issue.observation_id === observationId}`);
    }
    return issue.observation_id === observationId;
  });
  
  // Calculate completeness details
  const completenessIssues = observationIssues.filter(issue => 
    issue.quality_metrics === 'completeness'
  );
  
  let completenessStatus: 'Incident' | 'Compliant' = 'Compliant';
  let completenessDetails = 'All data is complete across fields';
  
  if (completenessIssues.length > 0) {
    completenessStatus = 'Incident';
    completenessDetails = completenessIssues.map(issue => {
      const percentage = issue.metadata?.completeness ? 
        (issue.metadata.completeness * 100).toFixed(2) : 
        issue.description.match(/(\d+\.?\d*)%/)?.[1] || '0';
      return `Column '${issue.column}' has only ${percentage}% non-null values.`;
    }).join('• ');
  }

  const qualityMetrics = [
    {
      criteria: 'Data Completeness',
      description: 'Required data fields coverage',
      status: completenessStatus,
      details: completenessDetails
    }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Quality Metrics</CardTitle>
        {observationIssues.length > 0 && (
          <p className="text-sm text-gray-600 mt-1">
            {observationIssues.length} issue(s) found for this observation
          </p>
        )}
      </CardHeader>
      <CardContent className="p-0">
        {/* Header Row */}
        <div className="grid grid-cols-3 gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200">
          <div className="font-medium text-sm text-gray-700">Criteria</div>
          <div className="font-medium text-sm text-gray-700">Status</div>
          <div className="font-medium text-sm text-gray-700">Details</div>
        </div>
        
        {/* Metric Rows */}
        <div className="px-6">
          {qualityMetrics.map((metric, index) => (
            <QualityMetricRow key={index} {...metric} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}