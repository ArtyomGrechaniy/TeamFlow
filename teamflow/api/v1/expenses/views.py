from decimal import Decimal

from django.db.models import Q, Sum, DecimalField
from django.db.models.functions import Coalesce
from expenses.models import Expense, ExpenseCategory
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from teams.models import TeamMember

from api.v1.permissions import IsOwnerOrTeamMember
from .serializers import (ExpenseCategoryReadSerializer,
                          ExpenseCategoryWriteSerializer,
                          ExpenseReadSerializer, ExpenseWriteSerializer)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления категориями расходов.

    Поддерживает командные и личные категории.
    Добавляет агрегированное поле total.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrTeamMember]

    def get_queryset(self):
        qs = ExpenseCategory.objects.select_related("team", "user").annotate(
            total=Coalesce(
                Sum("expenses__amount_rub"),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        user = self.request.user
        team_pk = self.kwargs.get("team_pk")

        if team_pk:
            return qs.filter(team_id=team_pk)
        
        return qs.filter(user=user)
    
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ExpenseCategoryReadSerializer
        
        if self.action in ["create", "update", "partial_update"]:
            return ExpenseCategoryWriteSerializer
        
        return ExpenseCategoryReadSerializer
    
    def perform_create(self, serializer):
        team_pk = self.kwargs.get("team_pk")

        if team_pk:
            serializer.save(
                team_id=team_pk,
                user=None
            )
            return
        serializer.save(
            team_id=None,
            user=self.request.user
        )


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления расходами.

    В командном режиме, если есть team_pk в URL, показывает только расходы команды.
    В личном режиме показывает личные расходы + все расходы команд,
    где пользователь является участником.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrTeamMember]

    def get_queryset(self):
        qs = Expense.objects.select_related("category", "team", "user")
        user = self.request.user
        team_pk = self.kwargs.get("team_pk")

        if team_pk:
            return qs.filter(team_id=team_pk)
        
        user_teams = TeamMember.objects.filter(
            user=user
        ).values_list("team_id", flat=True)

        return qs.filter(
            Q(user=user) | Q(team_id__in=user_teams)
        )
    
    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ExpenseReadSerializer
        
        if self.action in ["create", "update", "partial_update"]:
            return ExpenseWriteSerializer
        
        return ExpenseReadSerializer
        
    def perform_create(self, serializer):
        team_pk = self.kwargs.get("team_pk")

        if team_pk:
            serializer.save(
                team_id=team_pk,
                user=None
            )
            return
        serializer.save(
            team_id=None,
            user=self.request.user
        )