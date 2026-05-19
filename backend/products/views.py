from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions import HasCapability

from .filters import ProductFilter, SupplierFilter
from .models import Category, Product, Supplier
from .serializers import CategorySerializer, ProductSerializer, SupplierSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "master_data"
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "id"]
    ordering = ["name"]


class SupplierViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "master_data"
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_class = SupplierFilter
    search_fields = ["name", "legal_name", "document", "email", "phone"]
    ordering_fields = ["name", "created_at", "id"]
    ordering = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "master_data"
    queryset = Product.objects.select_related("category", "supplier").all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ["sku", "name", "description"]
    ordering_fields = ["name", "sku", "min_stock", "sale_price", "unit_cost", "created_at", "id"]
    ordering = ["name"]
