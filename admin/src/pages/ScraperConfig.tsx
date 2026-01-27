import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Play, RefreshCw } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import api from '@/api/client'
import { formatRelativeTime } from '@/lib/utils'

export function ScraperConfig() {
  const { websiteId } = useParams<{ websiteId: string }>()
  const queryClient = useQueryClient()

  const { data: website } = useQuery({
    queryKey: ['website', websiteId],
    queryFn: () => api.getWebsite(websiteId!).then((res) => res.data),
    enabled: !!websiteId,
  })

  const { data: configs, isLoading } = useQuery({
    queryKey: ['scraper-configs', websiteId],
    queryFn: () => api.getScraperConfigs(websiteId!).then((res) => res.data),
    enabled: !!websiteId,
  })

  const { data: logs } = useQuery({
    queryKey: ['scrape-logs', websiteId],
    queryFn: () => api.getScrapeLogs(websiteId!, 1, 10).then((res) => res.data),
    enabled: !!websiteId,
  })

  const [selectors, setSelectors] = useState<Record<string, string>>({})
  const [editMode, setEditMode] = useState(false)

  const activeConfig = configs?.find((c) => c.config_type === 'product_list' && c.is_active)

  const updateConfig = useMutation({
    mutationFn: (data: { selectors: Record<string, string> }) =>
      api.updateScraperConfig(websiteId!, activeConfig!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scraper-configs', websiteId] })
      setEditMode(false)
    },
  })

  const triggerScrape = useMutation({
    mutationFn: () => api.triggerScrape(websiteId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scrape-logs', websiteId] })
    },
  })

  const handleEditClick = () => {
    if (activeConfig) {
      setSelectors(activeConfig.selectors)
      setEditMode(true)
    }
  }

  const handleSave = () => {
    updateConfig.mutate({ selectors })
  }

  if (!websiteId) {
    return <div>Invalid website ID</div>
  }

  return (
    <div className="flex flex-col">
      <Header title={`Scraper Config: ${website?.name || 'Loading...'}`} />

      <div className="p-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Selector Configuration */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>CSS Selectors</CardTitle>
                  <CardDescription>
                    Configure selectors for extracting product data
                  </CardDescription>
                </div>
                {!editMode ? (
                  <Button variant="outline" onClick={handleEditClick}>
                    Edit
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setEditMode(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={updateConfig.isPending}>
                      <Save className="mr-2 h-4 w-4" />
                      Save
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <p>Loading...</p>
              ) : activeConfig ? (
                <div className="space-y-4">
                  {Object.entries(editMode ? selectors : activeConfig.selectors).map(
                    ([key, value]) => (
                      <div key={key}>
                        <label className="mb-1 block text-sm font-medium capitalize">
                          {key.replace(/_/g, ' ')}
                        </label>
                        {editMode ? (
                          <Input
                            value={value as string}
                            onChange={(e) =>
                              setSelectors((prev) => ({
                                ...prev,
                                [key]: e.target.value,
                              }))
                            }
                            placeholder={`CSS selector for ${key}`}
                          />
                        ) : (
                          <code className="block rounded bg-gray-100 p-2 text-sm">
                            {value as string}
                          </code>
                        )}
                      </div>
                    )
                  )}

                  <div className="pt-4 text-sm text-muted-foreground">
                    Version: {activeConfig.version} | Last updated:{' '}
                    {formatRelativeTime(activeConfig.updated_at)}
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">
                  No active configuration found. Create one to start scraping.
                </p>
              )}
            </CardContent>
          </Card>

          {/* Scrape Controls & Logs */}
          <div className="space-y-6">
            {/* Controls */}
            <Card>
              <CardHeader>
                <CardTitle>Scrape Controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  className="w-full"
                  onClick={() => triggerScrape.mutate()}
                  disabled={triggerScrape.isPending || !website?.is_active}
                >
                  <Play className="mr-2 h-4 w-4" />
                  {triggerScrape.isPending ? 'Starting...' : 'Run Scrape Now'}
                </Button>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Status</span>
                    <div className="mt-1">
                      <Badge variant={website?.is_active ? 'success' : 'secondary'}>
                        {website?.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Rate Limit</span>
                    <div className="mt-1 font-medium">
                      {website?.rate_limit_ms || 1000}ms
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Logs */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Recent Scrapes
                </CardTitle>
              </CardHeader>
              <CardContent>
                {logs?.items.length ? (
                  <div className="space-y-3">
                    {logs.items.map((log) => (
                      <div
                        key={log.id}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={
                                log.status === 'success'
                                  ? 'success'
                                  : log.status === 'failed'
                                  ? 'destructive'
                                  : 'secondary'
                              }
                            >
                              {log.status}
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              {formatRelativeTime(log.started_at)}
                            </span>
                          </div>
                          <p className="mt-1 text-sm">
                            {log.products_found} found, {log.products_created} created,{' '}
                            {log.products_updated} updated
                          </p>
                        </div>
                        <div className="text-right text-sm text-muted-foreground">
                          {log.pages_scraped} pages
                          {log.duration_seconds && (
                            <div>{log.duration_seconds.toFixed(1)}s</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No scrape logs yet</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
