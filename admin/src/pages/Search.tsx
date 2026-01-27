import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search as SearchIcon, ExternalLink } from 'lucide-react'
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
import { formatPrice, calculateDiscount } from '@/lib/utils'

export function Search() {
  const [query, setQuery] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: () => api.searchPrices(searchQuery).then((res) => res.data),
    enabled: searchQuery.length >= 2,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchQuery(query)
  }

  return (
    <div className="flex flex-col">
      <Header title="Price Search" />

      <div className="p-6">
        {/* Search Form */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Search Products</CardTitle>
            <CardDescription>
              Search for a product to compare prices across all competitor websites
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="flex gap-4">
              <Input
                placeholder="e.g., Anua Peach 70% Niacinamide Serum"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1"
              />
              <Button type="submit" disabled={query.length < 2 || isFetching}>
                <SearchIcon className="mr-2 h-4 w-4" />
                Search
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results */}
        {isLoading && (
          <div className="text-center text-muted-foreground">Searching...</div>
        )}

        {data && (
          <div>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Found {data.total_results} results across {data.websites_searched} websites
                in {data.search_time_ms}ms
              </p>
            </div>

            <div className="space-y-4">
              {data.results.map((result) => (
                <Card key={`${result.website_id}-${result.product_id}`}>
                  <CardContent className="flex items-center gap-4 p-4">
                    {/* Product Image */}
                    {result.image_url && (
                      <img
                        src={result.image_url}
                        alt={result.product_name}
                        className="h-20 w-20 rounded-lg object-cover"
                      />
                    )}

                    {/* Product Info */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-medium">{result.product_name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {result.brand && `${result.brand} • `}
                            {result.website}
                          </p>
                        </div>
                        <Badge variant="outline">
                          {Math.round(result.match_score * 100)}% match
                        </Badge>
                      </div>

                      <div className="mt-2 flex items-center gap-4">
                        {/* Price */}
                        <div className="flex items-baseline gap-2">
                          <span className="text-xl font-bold">
                            {formatPrice(result.price)}
                          </span>
                          {result.original_price && result.original_price > result.price && (
                            <>
                              <span className="text-sm text-muted-foreground line-through">
                                {formatPrice(result.original_price)}
                              </span>
                              <Badge variant="destructive">
                                -{calculateDiscount(result.price, result.original_price)}%
                              </Badge>
                            </>
                          )}
                        </div>

                        {/* Stock Status */}
                        <Badge variant={result.in_stock ? 'success' : 'secondary'}>
                          {result.in_stock ? 'In Stock' : 'Out of Stock'}
                        </Badge>
                      </div>
                    </div>

                    {/* Actions */}
                    <Button variant="outline" asChild>
                      <a
                        href={result.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <ExternalLink className="mr-2 h-4 w-4" />
                        View
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}

              {data.results.length === 0 && (
                <div className="py-12 text-center text-muted-foreground">
                  No products found matching "{data.query}"
                </div>
              )}
            </div>
          </div>
        )}

        {!data && !isLoading && (
          <div className="py-12 text-center text-muted-foreground">
            Enter a product name to search for prices across all competitors
          </div>
        )}
      </div>
    </div>
  )
}
