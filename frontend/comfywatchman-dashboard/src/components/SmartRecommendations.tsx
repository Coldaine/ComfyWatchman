import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import {
  Sparkles,
  TrendingUp,
  Users,
  Clock,
  Download,
  Star,
  Zap
} from 'lucide-react';
import { toast } from 'sonner';
import { useUserPreferences } from '../hooks/useUserPreferences';

interface Recommendation {
  id: string;
  type: 'model' | 'workflow' | 'preset';
  name: string;
  reason: string;
  confidence: number;
  category: 'trending' | 'personalized' | 'collaborative' | 'seasonal';
  metadata: {
    downloads?: number;
    rating?: number;
    users?: number;
    compatibility?: string;
  };
}

const recommendations: Recommendation[] = [
  {
    id: '1',
    type: 'model',
    name: 'SDXL Turbo',
    reason: 'Based on your recent portrait work and preference for fast iterations',
    confidence: 92,
    category: 'personalized',
    metadata: {
      downloads: 15420,
      rating: 4.8,
      compatibility: 'SD XL'
    }
  },
  {
    id: '2',
    type: 'workflow',
    name: 'Advanced ControlNet Pipeline',
    reason: 'Popular among users with similar workflows to yours',
    confidence: 87,
    category: 'collaborative',
    metadata: {
      users: 2341,
      rating: 4.9
    }
  },
  {
    id: '3',
    type: 'model',
    name: 'Detail Enhancement LORA',
    reason: 'Trending this week - 340% increase in downloads',
    confidence: 95,
    category: 'trending',
    metadata: {
      downloads: 8923,
      rating: 4.7
    }
  },
  {
    id: '4',
    type: 'preset',
    name: 'Winter Holiday Style',
    reason: 'Seasonal recommendation for December creative work',
    confidence: 78,
    category: 'seasonal',
    metadata: {
      users: 1245,
      rating: 4.6
    }
  },
  {
    id: '5',
    type: 'model',
    name: 'AnimateDiff V3',
    reason: 'Complements your existing animation workflow setup',
    confidence: 85,
    category: 'personalized',
    metadata: {
      downloads: 12100,
      rating: 4.9,
      compatibility: 'SD 1.5'
    }
  },
  {
    id: '6',
    type: 'workflow',
    name: 'Upscale & Refine Pro',
    reason: 'Often used together with Realistic Vision V6.0 in your library',
    confidence: 91,
    category: 'personalized',
    metadata: {
      users: 3456,
      rating: 4.8
    }
  }
];

export function SmartRecommendations() {
  const { preferences, updatePreference } = useUserPreferences();

  const handleDownload = (rec: Recommendation) => {
    toast.success(`Added ${rec.name} to download queue`);
  };

  const handleDismiss = (id: string) => {
    const currentDismissed = preferences.dismissedRecommendations || [];
    if (!currentDismissed.includes(id)) {
      updatePreference('dismissedRecommendations', [...currentDismissed, id]);
      toast.success('Recommendation dismissed');
    }
  };

  const getCategoryIcon = (category: Recommendation['category']) => {
    switch (category) {
      case 'trending': return TrendingUp;
      case 'personalized': return Sparkles;
      case 'collaborative': return Users;
      case 'seasonal': return Clock;
    }
  };

  const getCategoryLabel = (category: Recommendation['category']) => {
    switch (category) {
      case 'trending': return 'Trending';
      case 'personalized': return 'For You';
      case 'collaborative': return 'Community Pick';
      case 'seasonal': return 'Seasonal';
    }
  };

  const getCategoryColor = (category: Recommendation['category']) => {
    switch (category) {
      case 'trending': return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
      case 'personalized': return 'text-purple-500 bg-purple-500/10 border-purple-500/30';
      case 'collaborative': return 'text-blue-500 bg-blue-500/10 border-blue-500/30';
      case 'seasonal': return 'text-green-500 bg-green-500/10 border-green-500/30';
    }
  };

  const filteredRecommendations = recommendations.filter(
    r => !preferences.dismissedRecommendations?.includes(r.id)
  );

  const groupedRecommendations = {
    personalized: filteredRecommendations.filter(r => r.category === 'personalized'),
    trending: filteredRecommendations.filter(r => r.category === 'trending'),
    collaborative: filteredRecommendations.filter(r => r.category === 'collaborative'),
    seasonal: filteredRecommendations.filter(r => r.category === 'seasonal'),
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <Sparkles className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <h3>Smart Recommendations</h3>
              <p className="text-sm text-muted-foreground mt-1">
                AI-powered suggestions based on your usage patterns and community trends
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm">
            Refresh
          </Button>
        </div>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-2 text-purple-500 mb-2">
            <Sparkles className="w-4 h-4" />
            <div className="text-sm">For You</div>
          </div>
          <div className="text-2xl">{groupedRecommendations.personalized.length}</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-2 text-orange-500 mb-2">
            <TrendingUp className="w-4 h-4" />
            <div className="text-sm">Trending</div>
          </div>
          <div className="text-2xl">{groupedRecommendations.trending.length}</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-2 text-blue-500 mb-2">
            <Users className="w-4 h-4" />
            <div className="text-sm">Community</div>
          </div>
          <div className="text-2xl">{groupedRecommendations.collaborative.length}</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-2 text-green-500 mb-2">
            <Clock className="w-4 h-4" />
            <div className="text-sm">Seasonal</div>
          </div>
          <div className="text-2xl">{groupedRecommendations.seasonal.length}</div>
        </Card>
      </div>

      {/* Recommendations List */}
      <div className="space-y-6">
        {/* Personalized */}
        {groupedRecommendations.personalized.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-500" />
              <h4>Personalized For You</h4>
            </div>
            <div className="grid gap-3">
              {groupedRecommendations.personalized.map(rec => (
                <RecommendationCard
                  key={rec.id}
                  recommendation={rec}
                  onDownload={handleDownload}
                  onDismiss={handleDismiss}
                  getCategoryIcon={getCategoryIcon}
                  getCategoryLabel={getCategoryLabel}
                  getCategoryColor={getCategoryColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Trending */}
        {groupedRecommendations.trending.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-orange-500" />
              <h4>Trending Now</h4>
            </div>
            <div className="grid gap-3">
              {groupedRecommendations.trending.map(rec => (
                <RecommendationCard
                  key={rec.id}
                  recommendation={rec}
                  onDownload={handleDownload}
                  onDismiss={handleDismiss}
                  getCategoryIcon={getCategoryIcon}
                  getCategoryLabel={getCategoryLabel}
                  getCategoryColor={getCategoryColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Collaborative */}
        {groupedRecommendations.collaborative.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-500" />
              <h4>Community Picks</h4>
            </div>
            <div className="grid gap-3">
              {groupedRecommendations.collaborative.map(rec => (
                <RecommendationCard
                  key={rec.id}
                  recommendation={rec}
                  onDownload={handleDownload}
                  onDismiss={handleDismiss}
                  getCategoryIcon={getCategoryIcon}
                  getCategoryLabel={getCategoryLabel}
                  getCategoryColor={getCategoryColor}
                />
              ))}
            </div>
          </div>
        )}

        {/* Seasonal */}
        {groupedRecommendations.seasonal.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-green-500" />
              <h4>Seasonal Picks</h4>
            </div>
            <div className="grid gap-3">
              {groupedRecommendations.seasonal.map(rec => (
                <RecommendationCard
                  key={rec.id}
                  recommendation={rec}
                  onDownload={handleDownload}
                  onDismiss={handleDismiss}
                  getCategoryIcon={getCategoryIcon}
                  getCategoryLabel={getCategoryLabel}
                  getCategoryColor={getCategoryColor}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface RecommendationCardProps {
  recommendation: Recommendation;
  onDownload: (rec: Recommendation) => void;
  onDismiss: (id: string) => void;
  getCategoryIcon: (category: Recommendation['category']) => any;
  getCategoryLabel: (category: Recommendation['category']) => string;
  getCategoryColor: (category: Recommendation['category']) => string;
}

function RecommendationCard({
  recommendation,
  onDownload,
  onDismiss,
  getCategoryIcon,
  getCategoryLabel,
  getCategoryColor
}: RecommendationCardProps) {
  const CategoryIcon = getCategoryIcon(recommendation.category);

  return (
    <Card className="p-4">
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg ${getCategoryColor(recommendation.category)}`}>
          <CategoryIcon className="w-6 h-6" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="truncate">{recommendation.name}</h4>
                <Badge variant="outline">
                  {recommendation.type.charAt(0).toUpperCase() + recommendation.type.slice(1)}
                </Badge>
                <div className={`px-2 py-1 rounded-md text-xs border ${getCategoryColor(recommendation.category)}`}>
                  {getCategoryLabel(recommendation.category)}
                </div>
              </div>

              <p className="text-sm text-muted-foreground mt-2">
                {recommendation.reason}
              </p>

              <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                {recommendation.metadata.downloads && (
                  <div className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    {recommendation.metadata.downloads.toLocaleString()}
                  </div>
                )}
                {recommendation.metadata.rating && (
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                    {recommendation.metadata.rating}
                  </div>
                )}
                {recommendation.metadata.users && (
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    {recommendation.metadata.users.toLocaleString()} users
                  </div>
                )}
                {recommendation.metadata.compatibility && (
                  <Badge variant="secondary">
                    {recommendation.metadata.compatibility}
                  </Badge>
                )}
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-500" />
                <span className="text-sm">{recommendation.confidence}% match</span>
              </div>
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <Button size="sm" onClick={() => onDownload(recommendation)}>
              <Download className="w-4 h-4 mr-2" />
              Add to Queue
            </Button>
            <Button variant="outline" size="sm" onClick={() => onDismiss(recommendation.id)}>
              Dismiss
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
