from .models import Category, Product


# Function to retrieve or set cache for a product
def get_product_from_cache(slug):
    product = Product.objects.get_product_from_cache(slug)
    return product

# Function to retrieve or set cache for stock
def get_stock_from_cache(slug):
    stock = Product.objects.get_stock_from_product(slug)
    return stock


# Function to retrieve or set cache for a category
def get_category_from_cache(slug):
    category = Category.objects.get_category_from_cache(slug)
    return category

# Update the product cache
def update_product_cache(sender, instance, **kwargs):
    Product.objects.update_product_cache(instance.slug)


# Delete product and stock cache entries when the product or stock is deleted
def delete_product_cache(sender, instance, **kwargs):
    Product.objects.delete_product_cache(instance.slug)


# Update the category cache
def update_category_cache(sender, instance, **kwargs):
    Category.objects.update_category_cache(instance.slug)


# Delete category cache when the category is deleted
def delete_category_cache(sender, instance, **kwargs):
    Category.objects.delete_category_cache(instance.slug)

# Retrieve or cache product slugs
def get_cached_product_slugs():
    products_dict = Product.objects.get_products_dict_from_cache()

    # Extract slugs from the dictionary keys
    return list(products_dict.keys())


# Retrieve or cache category slugs
def get_cached_category_slugs():
    categories_dict = Category.objects.get_categories_dict_from_cache()
    return list(categories_dict.keys())
