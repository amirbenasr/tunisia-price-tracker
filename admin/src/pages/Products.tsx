import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ExternalLink } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
} from '@/components/ui/card'
import api from '@/api/client'
import { formatPrice } from '@/lib/utils'

export function Products() {
  const [page, setPage] = useState(1)
  const pageSize = 20

  const { data, isLoading } = useQuery({
    queryKey: ['products', page],
    queryFn: () => api.getProducts({ page, page_size: pageSize }).then((res) => res.data),
  })

  return (
    <div className="flex flex-col">
      <Header title="Products" />

      <div className="p-6">
        {/* Filters */}
        <div className="mb-6 flex gap-4">
          <Input placeholder="Search products..." className="max-w-sm" />
        </div>

        {/* Products Grid */}
        {isLoading ? (
          <p>Loading...</p>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {data?.items.map((product) => (
                <Card key={product.id}>
                  <CardContent className="p-4">
                    {product.image_url && (
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="mb-3 h-40 w-full rounded-lg object-cover"
                      />
                    )}
                    <h3 className="line-clamp-2 font-medium">{product.name}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {product.website_name}
                    </p>

                    <div className="mt-3 flex items-center justify-between">
                      {product.current_price ? (
                        <div className="flex items-baseline gap-2">
                          <span className="font-bold">
                            {formatPrice(product.current_price)}
                          </span>
                          {product.original_price && product.original_price > product.current_price && (
                            <span className="text-sm text-muted-foreground line-through">
                              {formatPrice(product.original_price)}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">No price</span>
                      )}
                      <Badge variant={product.in_stock ? 'success' : 'secondary'} className="text-xs">
                        {product.in_stock ? 'In Stock' : 'Out'}
                      </Badge>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-3 w-full"
                      asChild
                    >
                      <a
                        href={product.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <ExternalLink className="mr-2 h-4 w-4" />
                        View Product
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Pagination */}
            {data && data.total_pages > 1 && (
              <div className="mt-6 flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {data.total_pages}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={page === data.total_pages}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
