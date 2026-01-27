import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, ExternalLink, Play, Settings } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import api, { Website } from '@/api/client'
import { formatRelativeTime } from '@/lib/utils'

export function Websites() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['websites'],
    queryFn: () => api.getWebsites(1, 100).then((res) => res.data),
  })

  const triggerScrape = useMutation({
    mutationFn: (websiteId: string) => api.triggerScrape(websiteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['websites'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex flex-col">
        <Header title="Websites" />
        <div className="p-6">
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col">
      <Header title="Websites" />

      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <p className="text-muted-foreground">
            Manage competitor websites to track prices from
          </p>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Website
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((website) => (
            <WebsiteCard
              key={website.id}
              website={website}
              onTriggerScrape={() => triggerScrape.mutate(website.id)}
              isScraping={triggerScrape.isPending}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

interface WebsiteCardProps {
  website: Website
  onTriggerScrape: () => void
  isScraping: boolean
}

function WebsiteCard({ website, onTriggerScrape, isScraping }: WebsiteCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{website.name}</CardTitle>
            <CardDescription className="mt-1">
              <a
                href={website.base_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 hover:underline"
              >
                {website.base_url}
                <ExternalLink className="h-3 w-3" />
              </a>
            </CardDescription>
          </div>
          <Badge variant={website.is_active ? 'success' : 'secondary'}>
            {website.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Products</span>
            <span className="font-medium">{website.total_products}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Last Scraped</span>
            <span className="font-medium">
              {website.last_scraped_at
                ? formatRelativeTime(website.last_scraped_at)
                : 'Never'}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Rate Limit</span>
            <span className="font-medium">{website.rate_limit_ms}ms</span>
          </div>

          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={onTriggerScrape}
              disabled={isScraping || !website.is_active}
            >
              <Play className="mr-2 h-4 w-4" />
              Scrape
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link to={`/scrapers/${website.id}`}>
                <Settings className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
