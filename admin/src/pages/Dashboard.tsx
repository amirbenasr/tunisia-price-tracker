import { useQuery } from '@tanstack/react-query'
import {
  Globe,
  Package,
  TrendingDown,
  RefreshCw,
  Activity,
  BarChart3,
  Clock,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Header } from '@/components/layout/Header'
import api from '@/api/client'
import { formatRelativeTime } from '@/lib/utils'

export function Dashboard() {
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getDashboardStats().then((res) => res.data),
  })

  const { data: websites, isLoading: loadingWebsites } = useQuery({
    queryKey: ['websites'],
    queryFn: () => api.getWebsites(1, 100).then((res) => res.data),
  })

  const statCards = [
    {
      name: 'Total Websites',
      value: stats?.total_websites || 0,
      subValue: `${stats?.active_websites || 0} active`,
      icon: Globe,
      color: 'text-blue-600',
    },
    {
      name: 'Total Products',
      value: stats?.total_products?.toLocaleString() || '0',
      subValue: `+${stats?.products_added_today || 0} today`,
      icon: Package,
      color: 'text-green-600',
    },
    {
      name: 'Price Records',
      value: stats?.total_price_records?.toLocaleString() || '0',
      subValue: `+${stats?.price_changes_today || 0} today`,
      icon: BarChart3,
      color: 'text-purple-600',
    },
    {
      name: 'Scrapes Today',
      value: stats?.scrapes_today || 0,
      subValue: `${stats?.scrapes_success_rate || 0}% success rate`,
      icon: RefreshCw,
      color: 'text-orange-600',
    },
  ]

  return (
    <div className="flex flex-col">
      <Header title="Dashboard" />

      <div className="p-6">
        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statCards.map((stat) => (
            <Card key={stat.name}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.name}
                </CardTitle>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {loadingStats ? '...' : stat.value}
                </div>
                <p className="text-xs text-muted-foreground">
                  {stat.subValue}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent Activity */}
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {/* Websites Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Websites Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingWebsites ? (
                <p className="text-muted-foreground">Loading...</p>
              ) : (
                <div className="space-y-4">
                  {websites?.items.slice(0, 5).map((website) => (
                    <div
                      key={website.id}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`h-2 w-2 rounded-full ${
                            website.is_active ? 'bg-green-500' : 'bg-gray-300'
                          }`}
                        />
                        <div>
                          <p className="font-medium">{website.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {website.total_products.toLocaleString()} products
                          </p>
                        </div>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        {website.last_scraped_at ? (
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatRelativeTime(website.last_scraped_at)}
                          </div>
                        ) : (
                          'Never scraped'
                        )}
                      </div>
                    </div>
                  ))}

                  {!websites?.items.length && (
                    <p className="text-muted-foreground">
                      No websites configured yet
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* System Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <StatusItem name="API" status="healthy" />
                <StatusItem name="Database" status="connected" />
                <StatusItem name="Redis" status="connected" />
                <StatusItem
                  name="Celery Workers"
                  status="check"
                  warning
                />
              </div>

              <div className="mt-6 rounded-lg bg-gray-50 p-4">
                <h4 className="font-medium">Quick Actions</h4>
                <p className="mt-1 text-sm text-muted-foreground">
                  Use the Scrapers page to trigger manual scrapes or configure
                  new websites.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Tips */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="list-inside list-decimal space-y-2 text-sm text-muted-foreground">
              <li>Add competitor websites in the <strong>Websites</strong> section</li>
              <li>Configure CSS selectors for each website in <strong>Scrapers</strong></li>
              <li>Trigger a manual scrape to test your configuration</li>
              <li>Use the <strong>Search</strong> page to compare prices across all competitors</li>
              <li>Monitor <strong>Price Drops</strong> for deals and competitor price changes</li>
            </ol>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

interface StatusItemProps {
  name: string
  status: string
  warning?: boolean
}

function StatusItem({ name, status, warning }: StatusItemProps) {
  return (
    <div className="flex items-center justify-between">
      <span>{name}</span>
      <span className="flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${
            warning ? 'bg-yellow-500' : 'bg-green-500'
          }`}
        />
        <span className="text-sm capitalize">{status}</span>
      </span>
    </div>
  )
}
