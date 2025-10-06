from django.urls import path
from . import views

urlpatterns = [
    # Expense CRUD endpoints
    path('expenses/', views.ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('expenses/<int:pk>/', views.ExpenseDetailView.as_view(), name='expense-detail'),
    
    # History and Stats endpoints
    path('expenses/history/', views.expense_history, name='expense-history'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('expenses/summary/', views.expense_summary, name='expense-summary'),
    
    # Category choices endpoint
    path('categories/choices/', views.category_choices, name='category-choices'),
    
    # Export endpoint
    path('export/excel/', views.export_excel, name='export-excel'),
]