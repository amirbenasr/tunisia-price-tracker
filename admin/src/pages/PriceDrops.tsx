import { useQuery } from '@tanstack/react-query'
import { TrendingDown, ExternalLink } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
} from '@/components/ui/card'
import api from '@/api/client'
import { formatPrice, formatRelativeTime } from '@/lib/utils'

export function PriceDrops() {
  const { data, isLoading } = useQuery({
    queryKey: ['price-drops'],
    queryFn: () => api.getPriceDrops(24, 50).then((res) => res.data),
  })

  return (
    <div className="flex flex-col">
      <Header title="Price Drops" />

      <div className="p-6">
        <div className="mb-6">
          <p className="text-muted-foreground">
            Products with recent price drops in the last 24 hours
          </p>
        </div>

        {isLoading ? (
          <p>Loading...</p>
        ) : data && data.length > 0 ? (
          <div className="space-y-4">
            {data.map((drop: any) => (
              <Card key={drop.product_id}>
                <CardContent className="flex items-center gap-4 p-4">
                  {/* Product Image */}
                  {drop.image_url && (
                    <img
                      src={drop.image_url}
                      alt={drop.product_name}
                      className="h-20 w-20 rounded-lg object-cover"
                    />
                  )}

                  {/* Product Info */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium">{drop.product_name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {drop.website_name}
                        </p>
                      </div>
                      <Badge variant="destructive" className="flex items-center gap-1">
                        <TrendingDown className="h-3 w-3" />
                        -{drop.drop_percentage.toFixed(1)}%
                      </Badge>
                    </div>

                    <div className="mt-2 flex items-center gap-4">
                      <div className="flex items-baseline gap-2">
                        <span className="text-xl font-bold text-green-600">
                          {formatPrice(drop.current_price)}
                        </span>
                        <span className="text-sm text-muted-foreground line-through">
                          {formatPrice(drop.previous_price)}
                        </span>
                      </div>
                      <span className="text-sm text-green-600">
                        Save {formatPrice(drop.drop_amount)}
                      </span>
                    </div>

                    <p className="mt-1 text-xs text-muted-foreground">
                      Price dropped {formatRelativeTime(drop.recorded_at)}
                    </p>
                  </div>

                  {/* Actions */}
                  <Button variant="outline" asChild>
                    <a
                      href={drop.product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      View Deal
                    </a>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="py-12 text-center">
            <TrendingDown className="mx-auto h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No Price Drops</h3>
            <p className="mt-2 text-muted-foreground">
              No significant price drops detected in the last 24 hours.
              Check back later!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
