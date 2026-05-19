from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from core.permissions import HasCapability

from .filters import CustomerFilter
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "master_data"
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_class = CustomerFilter
    search_fields = ["name", "document", "email", "phone"]
    ordering_fields = ["name", "created_at", "id"]
    ordering = ["name"]
